import asyncio
from datetime import datetime
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.modules.bank.application.service import MAX_REPORTS_PER_DAY, BankService
from app.shared.errors import Conflict, Forbidden, NotFound


class Repo:
    def __init__(self, today: int = 0, count: int = 1, inserted: bool = True) -> None:
        self.today, self.count, self.added, self.inserted = today, count, 0, inserted
        self.cleared: list[UUID] = []
        self.saved: list[Any] = []
        self.q = SimpleNamespace(id=uuid4(), status="verified", parent_id=None)

    async def get_many(self, ids: Any) -> list[Any]:
        return [self.q]

    async def count_reports_by_user_since(self, user_id: UUID, since: datetime) -> int:
        return self.today

    async def add_report(self, qid: UUID, user_id: UUID, reason: str) -> tuple[int, bool]:
        self.added += 1
        return self.count, self.inserted

    async def clear_reports(self, qid: UUID) -> None:
        self.cleared.append(qid)
        self.count = 0

    async def save(self, q: Any) -> None:
        self.saved.append(q.status)

    async def add_audit(self, *a: Any, **k: Any) -> None: ...


def test_guest_cannot_report() -> None:
    repo = Repo()
    svc = BankService(repo)  # type: ignore[arg-type]
    with pytest.raises(Forbidden):
        asyncio.run(svc.report(repo.q.id, uuid4(), "x", is_guest=True))
    assert repo.added == 0


def test_daily_cap() -> None:
    repo = Repo(today=MAX_REPORTS_PER_DAY)
    svc = BankService(repo)  # type: ignore[arg-type]
    with pytest.raises(Conflict) as e:
        asyncio.run(svc.report(repo.q.id, uuid4(), "x"))
    assert e.value.code == "report_rate_limited"
    assert repo.added == 0


def test_registered_report_recorded() -> None:
    repo = Repo(today=MAX_REPORTS_PER_DAY - 1)
    svc = BankService(repo)  # type: ignore[arg-type]
    assert asyncio.run(svc.report(repo.q.id, uuid4(), "x")) is False
    assert repo.added == 1


def test_reverified_question_not_rehidden_by_old_reports() -> None:
    repo = Repo(count=3, inserted=False)
    svc = BankService(repo, report_hide_threshold=3)  # type: ignore[arg-type]
    repo.q.kind, repo.q.payload, repo.q.answer, repo.q.stem = "x", {}, {}, "s"
    # a duplicate report (nothing inserted) never hides, whatever the stored total says
    assert asyncio.run(svc.report(repo.q.id, uuid4(), "x")) is False
    assert repo.saved == []
    # hidden -> verified wipes the old reports
    repo.q.status = "hidden"
    from unittest.mock import patch

    with patch.object(BankService, "_validate"):
        asyncio.run(svc.set_status(repo.q.id, "verified", None))
    assert repo.cleared == [repo.q.id]
    assert repo.count == 0


def test_report_on_unpublished_question_is_404() -> None:
    repo = Repo()
    repo.q.status = "draft"
    svc = BankService(repo)  # type: ignore[arg-type]
    with pytest.raises(NotFound):
        asyncio.run(svc.report(repo.q.id, uuid4(), "x"))
    assert repo.added == 0


def test_child_status_cannot_change_directly() -> None:
    repo = Repo()
    repo.q.parent_id = uuid4()
    svc = BankService(repo)  # type: ignore[arg-type]
    with pytest.raises(Conflict) as e:
        asyncio.run(svc.set_status(repo.q.id, "hidden", None))
    assert e.value.code == "child_status"
