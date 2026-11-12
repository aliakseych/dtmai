import asyncio
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.interfaces.http.v1.assessment import SaveIn
from app.modules.assessment.application.service import AssessmentService


class Repo:
    def __init__(self, active: dict) -> None:
        self.active, self.moved = active, []

    async def active_for(self, user_id, lock=False):
        return self.active.get(user_id)

    async def reassign(self, a, b):
        self.moved.append((a, b))


def _svc(repo: Repo, finalized: list) -> AssessmentService:
    s = AssessmentService.__new__(AssessmentService)
    s._r = repo  # type: ignore[assignment]

    async def fin(a, *, reason):
        finalized.append((a, reason))

    s._finalize = fin  # type: ignore[method-assign]
    return s


def test_both_active_finalizes_guest_then_rekeys() -> None:
    g, u = uuid4(), uuid4()
    finalized: list = []
    repo = Repo({g: "guest-attempt", u: "user-attempt"})
    asyncio.run(_svc(repo, finalized).merge_guest(g, u))
    assert finalized == [("guest-attempt", "auto")]
    assert repo.moved == [(g, u)]


def test_only_guest_active_is_rekeyed_untouched() -> None:
    g, u = uuid4(), uuid4()
    finalized: list = []
    repo = Repo({g: "guest-attempt"})
    asyncio.run(_svc(repo, finalized).merge_guest(g, u))
    assert finalized == []
    assert repo.moved == [(g, u)]


def test_save_bounds() -> None:
    with pytest.raises(ValidationError):
        SaveIn(flags=[uuid4() for _ in range(201)])
    with pytest.raises(ValidationError):
        SaveIn(answers={uuid4(): {"v": "x" * 5000}})
    SaveIn(answers={uuid4(): {"v": "ok"}}, flags=[uuid4()])
