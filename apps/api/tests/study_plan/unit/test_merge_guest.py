from uuid import uuid4

from app.modules.study_plan.application.service import PlanService


class _Repo:
    """In-memory stand-in mirroring SqlPlanRepository.merge: destination wins, guest fills gaps."""

    def __init__(self, plans: dict) -> None:
        self.plans = plans

    async def merge(self, from_id, into_id) -> None:
        guest = self.plans.pop(from_id, None)
        if guest is not None and into_id not in self.plans:
            self.plans[into_id] = guest


def _svc(repo) -> PlanService:
    return PlanService(
        repo, None, None, None, None, None, now=None, max_day_minutes=150, dream=None
    )  # type: ignore[arg-type]


async def test_guest_plan_moves_to_user_without_one() -> None:
    guest, user = uuid4(), uuid4()
    repo = _Repo({guest: "guest-plan"})
    await _svc(repo).merge_guest(guest, user)
    assert repo.plans == {user: "guest-plan"}


async def test_existing_plan_is_kept() -> None:
    guest, user = uuid4(), uuid4()
    repo = _Repo({guest: "guest-plan", user: "own-plan"})
    await _svc(repo).merge_guest(guest, user)
    assert repo.plans == {user: "own-plan"}


async def test_same_user_is_noop() -> None:
    u = uuid4()
    repo = _Repo({u: "p"})
    await _svc(repo).merge_guest(u, u)
    assert repo.plans == {u: "p"}
