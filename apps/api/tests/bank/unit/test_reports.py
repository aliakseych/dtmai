import asyncio
from datetime import datetime
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.modules.bank.application.service import MAX_REPORTS_PER_DAY, BankService
from app.shared.errors import Conflict, Forbidden


class Repo:
    def __init__(self, today: int = 0, count: int = 1) -> None:
        self.today, self.count, self.added = today, count, 0
        self.q = SimpleNamespace(id=uuid4(), status="draft")

    async def get_many(self, ids: Any) -> list[Any]:
        return [self.q]

    async def count_reports_by_user_since(self, user_id: UUID, since: datetime) -> int:
        return self.today

    async def add_report(self, qid: UUID, user_id: UUID, reason: str) -> int:
        self.added += 1
        return self.count


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
