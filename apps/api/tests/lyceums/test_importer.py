import asyncio
from uuid import UUID, uuid4

from app.modules.lyceums.application.importer import LyceumImporter
from app.modules.lyceums.domain.models import (
    ImportRun,
    ImportStatus,
    SourceLanguage,
    SourceLyceum,
    SourceSpeciality,
    competition_ratio,
)


class FakeSource:
    def __init__(self, fail_pairs: set[tuple[int, int]] | None = None, boom: bool = False) -> None:
        self.fail_pairs = fail_pairs or set()
        self.boom = boom

    async def lyceums(self) -> list[SourceLyceum]:
        if self.boom:
            raise RuntimeError("down")
        return [SourceLyceum(1035, "219", "Litsey", "Lyceum", "Лицей"),
                SourceLyceum(1036, "220", "Litsey 2", "", "")]

    async def languages(self) -> list[SourceLanguage]:
        return [SourceLanguage(2, "11", "O‘zbek", "", "Узбекский"),
                SourceLanguage(3, "12", "Rus", "", "Русский")]

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

    async def create(self, year: int, requested_by: UUID | None) -> ImportRun:
        run = ImportRun(uuid4(), year, ImportStatus.PENDING, requested_by)
        self.rows[run.id] = run
        return run

    async def get(self, run_id: UUID) -> ImportRun | None:
        return self.rows.get(run_id)

    async def save(self, run: ImportRun) -> None:
        self.rows[run.id] = run

    async def list(self, limit: int) -> list[ImportRun]:
        return list(self.rows.values())[:limit]


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


def test_partial_failures_counted_but_succeed() -> None:
    run = _run(FakeSource(fail_pairs={(1035, 2)}))
    assert run.status is ImportStatus.SUCCEEDED
    assert run.errors == 1 and run.stats == 3


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
