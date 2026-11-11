"""Seed ledger: deleted seed events/FAQ stay deleted; missing subject links get filled."""

from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy.sql.dml import Update

from app.modules.exam_info.application.service import ExamInfoService
from app.modules.exam_info.infrastructure import seed as seed_mod
from app.modules.exam_info.infrastructure import seed_data as d
from app.shared.errors import ValidationFailed


class _Result:
    def __init__(self, rows: list[int]) -> None:
        self._rows = rows

    def all(self) -> list[int]:
        return self._rows

    def first(self) -> int | None:
        return self._rows[0] if self._rows else None


class FakeSession:
    """Records statements; seeded_key behaves like the real ledger table."""

    def __init__(self, conflicting: frozenset[str] = frozenset()) -> None:
        self.ledger: set[tuple[str, str]] = set()
        self.inserted: list[str] = []
        self.updates: list[str] = []
        self.conflicting = conflicting

    async def execute(self, stmt: Any) -> _Result:
        table = stmt.table.name
        if isinstance(stmt, Update):
            self.updates.append(table)
            return _Result([])
        if table == "seeded_key":
            p = stmt.compile().params
            key = (p["kind"], p["key"])
            if key in self.ledger:
                return _Result([])
            self.ledger.add(key)
            return _Result([1])
        if table in self.conflicting:
            return _Result([])
        self.inserted.append(table)
        return _Result([1])


class Subjects:
    def __init__(self, codes: dict[str, Any]) -> None:
        self.codes = codes

    async def ids_by_code(self) -> dict[str, Any]:
        return self.codes


ALL_CODES = {
    s.subject_code: uuid4() for p in d.profile_specs() for s in p.sections if s.subject_code
}


async def test_deleted_events_and_faq_are_not_recreated() -> None:
    session = FakeSession()
    first = await seed_mod.seed(session, Subjects(ALL_CODES))  # type: ignore[arg-type]
    assert first["events"] == len(d.EVENTS)
    assert first["faq"] == len(d.FAQ)
    # an admin deletes them, then a deploy reruns the seed
    again = await seed_mod.seed(session, Subjects(ALL_CODES))  # type: ignore[arg-type]
    assert again["events"] == 0
    assert again["faq"] == 0


async def test_rerun_fills_only_missing_section_subject_links() -> None:
    session = FakeSession(conflicting=frozenset({"exam_profile_section"}))
    await seed_mod.seed(session, Subjects(ALL_CODES))  # type: ignore[arg-type]
    assert "exam_profile_section" in session.updates


async def test_missing_catalog_subject_warns(caplog: pytest.LogCaptureFixture) -> None:
    session = FakeSession()
    with caplog.at_level("WARNING"):
        await seed_mod.seed(session, Subjects({}))  # type: ignore[arg-type]
    assert "missing" in caplog.text


class _Repo:
    def __init__(self) -> None:
        self.section_calls: list[Any] = []
        self.choice_calls: list[Any] = []

    async def get_section(self, section_id: Any) -> object:
        return object()

    async def set_section_subject(self, section_id: Any, subject_id: Any) -> None:
        self.section_calls.append(subject_id)

    async def replace_choice(self, group: str, subject_ids: list[Any]) -> None:
        self.choice_calls.append(subject_ids)


async def test_unknown_subject_is_rejected() -> None:
    known = uuid4()
    repo = _Repo()
    svc = ExamInfoService(repo, Subjects({"math": known}))  # type: ignore[arg-type]
    with pytest.raises(ValidationFailed):
        await svc.set_section_subject(uuid4(), uuid4())
    with pytest.raises(ValidationFailed):
        await svc.replace_choice("foreign_language", [known, uuid4()])
    assert repo.section_calls == [] and repo.choice_calls == []
    await svc.set_section_subject(uuid4(), known)
    await svc.set_section_subject(uuid4(), None)
    await svc.replace_choice("foreign_language", [known])
    assert repo.section_calls == [known, None] and repo.choice_calls == [[known]]
