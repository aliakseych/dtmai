import asyncio
from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.modules.gamification.application.service import GamificationService


def _svc(days: list[date]) -> GamificationService:
    s = GamificationService.__new__(GamificationService)
    stats = SimpleNamespace(lessons_completed=0, hearts=None)
    cfg = SimpleNamespace(xp_caps=SimpleNamespace(daily_cap=600, session_cap=150, per_item_cap=10))
    handled_at = datetime(2026, 1, 5, 19, 1, tzinfo=UTC)  # 00:01 Tashkent on the 6th

    async def load(_u):
        return stats, cfg, 5, False, handled_at

    async def mark(*_):
        return True

    async def noop(*_a, **_k):
        return None

    async def award(_stats, _cfg, day, *_a, **_k):
        days.append(day)
        return 5

    async def streak(_stats, _cfg, day):
        days.append(day)

    s._load = load  # type: ignore[method-assign]
    s._stats = SimpleNamespace(mark_event=mark, save=noop)  # type: ignore[assignment]
    s._sync_profile = noop  # type: ignore[method-assign]
    s._award_xp = award  # type: ignore[method-assign]
    s._touch_streak = streak  # type: ignore[method-assign]
    s._advance = noop  # type: ignore[method-assign]
    s._achievements = noop  # type: ignore[method-assign]
    return s


def test_event_credited_to_day_it_occurred_not_handled() -> None:
    days: list[date] = []
    occurred = datetime(2026, 1, 5, 18, 59, tzinfo=UTC)  # 23:59 Tashkent on the 5th
    asyncio.run(_svc(days).on_session_completed(uuid4(), uuid4(), "s", "drill", 5, 3, 4, occurred))
    assert days == [date(2026, 1, 5), date(2026, 1, 5)]


def test_without_occurred_at_falls_back_to_handling_time() -> None:
    days: list[date] = []
    asyncio.run(_svc(days).on_session_completed(uuid4(), uuid4(), "s", "drill", 5, 3, 4))
    assert days == [date(2026, 1, 6), date(2026, 1, 6)]
