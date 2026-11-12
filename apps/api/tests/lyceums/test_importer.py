import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.modules.lyceums.application.importer import LyceumImporter, list_runs
from app.modules.lyceums.domain.models import (
    ImportRun,
    ImportStatus,
    SourceLanguage,
    SourceLyceum,
    SourceSpeciality,
    competition_ratio,
)
from app.shared.errors import Conflict, ValidationFailed


class FakeSource:
    def __init__(self, fail_pairs: set[tuple[int, int]] | None = None, boom: bool = False) -> None:
        self.fail_pairs = fail_pairs or set()
        self.boom = boom

    async def lyceums(self) -> list[SourceLyceum]:
        if self.boom:
            raise RuntimeError("down")
        return [
            SourceLyceum(1035, "219", "Litsey", "Lyceum", "Лицей"),
            SourceLyceum(1036, "220", "Litsey 2", "", ""),
        ]

    async def languages(self) -> list[SourceLanguage]:
        return [
            SourceLanguage(2, "11", "O‘zbek", "", "Узбекский"),
            SourceLanguage(3, "12", "Rus", "", "Русский"),
        ]

    async def specialities(self, lyc: int, lang: int) -> list[SourceSpeciality]:
        if (lyc, lang) in self.fail_pairs:
            raise RuntimeError("x")
        return [SourceSpeciality("3910002", "Matematika", 52, 671)]


class FakeSink:
    def __init__(self) -> None:
        self.stats: dict[tuple[UUID, UUID, str, int], SourceSpeciality] = {}
        self.ids: dict[tuple[str, int], UUID] = {}

    def _id(self, kind: str, ext: int) -> UUID:
        return self.ids.setdefault((kind, ext), uuid4())

    async def upsert_lyceum(self, item: SourceLyceum) -> UUID:
        return self._id("l", item.external_id)

    async def upsert_language(self, item: SourceLanguage) -> UUID:
        return self._id("g", item.external_id)

    async def upsert_stat(
        self, *, lyceum_id: UUID, language_id: UUID, year: int, item: SourceSpeciality
    ) -> None:
        self.stats[(lyceum_id, language_id, item.code, year)] = item


class FakeRuns:
    def __init__(self) -> None:
        self.rows: dict[UUID, ImportRun] = {}
        self.failed: list[UUID] = []

    async def create(self, year: int, requested_by: UUID | None) -> ImportRun:
        run = ImportRun(
            uuid4(), year, ImportStatus.PENDING, requested_by, created_at=datetime.now(UTC)
        )
        self.rows[run.id] = run
        return run

    async def get(self, run_id: UUID) -> ImportRun | None:
        return self.rows.get(run_id)

    async def save(self, run: ImportRun) -> None:
        self.rows[run.id] = run

    async def list(self, limit: int) -> list[ImportRun]:
        return list(self.rows.values())[:limit]

    async def reset_stale(self, older_than: datetime) -> None:
        for r in self.rows.values():
            if r.status in (ImportStatus.PENDING, ImportStatus.RUNNING) and (
                r.created_at is not None and r.created_at < older_than
            ):
                r.status = ImportStatus.FAILED

    async def active(self) -> ImportRun | None:
        return next(
            (
                r
                for r in self.rows.values()
                if r.status in (ImportStatus.PENDING, ImportStatus.RUNNING)
            ),
            None,
        )

    async def mark_failed(self, run_id: UUID, error: str) -> None:
        self.failed.append(run_id)
        self.rows[run_id].status = ImportStatus.FAILED


def _run(source: FakeSource, sink: FakeSink | None = None, year: int = 2025) -> ImportRun:
    sink = sink or FakeSink()
    runs = FakeRuns()

    async def go() -> ImportRun:
        imp = LyceumImporter(source, sink, runs, concurrency=2)
        run = await imp.start(year, None)
        return await imp.run(run.id)

    return asyncio.run(go())


def test_import_stamps_year_and_counts() -> None:
    sink = FakeSink()
    run = _run(FakeSource(), sink)
    assert run.status is ImportStatus.SUCCEEDED
    assert (run.lyceums, run.stats, run.errors) == (2, 4, 0)
    assert {k[3] for k in sink.stats} == {2025}
    assert run.finished_at is not None


def test_partial_failures_are_marked_partial() -> None:
    run = _run(FakeSource(fail_pairs={(1035, 2)}))
    assert run.status is ImportStatus.PARTIAL
    assert run.errors == 1 and run.stats == 3


def test_second_start_while_active_conflicts() -> None:
    runs = FakeRuns()
    imp = LyceumImporter(FakeSource(), FakeSink(), runs)

    async def go() -> None:
        await imp.start(2025, None)
        await imp.start(2025, None)

    with pytest.raises(Conflict):
        asyncio.run(go())


def test_stale_active_run_is_reset_then_start_allowed() -> None:
    runs = FakeRuns()
    imp = LyceumImporter(FakeSource(), FakeSink(), runs)

    async def go() -> ImportRun:
        old = await imp.start(2025, None)
        old.created_at = datetime.now(UTC) - timedelta(hours=3)
        new = await imp.start(2025, None)
        assert runs.rows[old.id].status is ImportStatus.FAILED
        return new

    assert asyncio.run(go()).status is ImportStatus.PENDING


def test_listing_runs_fails_stale_ones_so_the_history_is_truthful() -> None:
    runs = FakeRuns()
    imp = LyceumImporter(FakeSource(), FakeSink(), runs)

    async def go() -> list[ImportRun]:
        old = await imp.start(2025, None)
        old.created_at = datetime.now(UTC) - timedelta(hours=3)
        return await list_runs(runs, 20)

    assert [r.status for r in asyncio.run(go())] == [ImportStatus.FAILED]


def test_redelivered_run_is_a_noop() -> None:
    sink = FakeSink()
    runs = FakeRuns()
    imp = LyceumImporter(FakeSource(), sink, runs)

    async def go() -> ImportRun:
        run = await imp.start(2025, None)
        await imp.run(run.id)
        sink.stats.clear()
        return await imp.run(run.id)

    assert asyncio.run(go()).status is ImportStatus.SUCCEEDED
    assert sink.stats == {}


def test_crash_rolls_back_and_marks_failed_separately() -> None:
    runs = FakeRuns()
    calls: list[str] = []

    async def rollback() -> None:
        calls.append("rollback")

    class Boom(FakeSink):
        async def upsert_lyceum(self, item: SourceLyceum) -> UUID:
            raise RuntimeError("db")

    imp = LyceumImporter(FakeSource(), Boom(), runs, rollback=rollback)

    async def go() -> ImportRun:
        run = await imp.start(2025, None)
        return await imp.run(run.id)

    run = asyncio.run(go())
    assert run.status is ImportStatus.FAILED
    assert calls == ["rollback"] and runs.failed == [run.id]


def test_start_rejects_far_future_year() -> None:
    imp = LyceumImporter(FakeSource(), FakeSink(), FakeRuns())
    with pytest.raises(ValidationFailed):
        asyncio.run(imp.start(2099, None))


def test_all_failed_marks_failed() -> None:
    run = _run(FakeSource(fail_pairs={(a, b) for a in (1035, 1036) for b in (2, 3)}))
    assert run.status is ImportStatus.FAILED


def test_source_down_marks_failed_with_message() -> None:
    run = _run(FakeSource(boom=True))
    assert run.status is ImportStatus.FAILED and "down" in (run.error or "")


def test_rerun_is_idempotent() -> None:
    sink = FakeSink()
    _run(FakeSource(), sink)
    _run(FakeSource(), sink)
    assert len(sink.stats) == 4


def test_ratio() -> None:
    assert competition_ratio(671, 52) == 12.9
    assert competition_ratio(10, 0) is None
