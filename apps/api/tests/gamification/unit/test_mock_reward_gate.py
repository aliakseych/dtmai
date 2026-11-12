import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app.modules.gamification.application.service import GamificationService


def _svc(awarded: list) -> GamificationService:
    s = GamificationService.__new__(GamificationService)
    stats = SimpleNamespace(mocks_submitted=0)

    async def load(_u):
        return stats, SimpleNamespace(mock_xp=50), None, None, None

    async def mark(*_):
        return True

    async def save(_s):
        pass

    async def award(*a, **k):
        awarded.append(1)
        return 50

    s._load = load  # type: ignore[method-assign]
    s._award_xp = award  # type: ignore[method-assign]
    s._stats = SimpleNamespace(mark_event=mark, save=save)  # type: ignore[assignment]
    return s


def test_unrewardable_mock_earns_nothing() -> None:
    awarded: list = []
    asyncio.run(_svc(awarded).on_mock_submitted(uuid4(), uuid4(), "a", rewardable=False))
    assert awarded == []
