"""Public gamification facade: other modules import only this."""

from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.gamification.application.service import HeartsView
from app.modules.gamification.infrastructure.progress import ProgressStats, SqlProgressReader
from app.modules.gamification.wiring import build_gamification_service

__all__ = ["ProgressStats", "hearts_state", "lose_heart", "merge_guest", "progress_stats"]


async def hearts_state(session: AsyncSession, user_id: UUID) -> HeartsView:
    return await build_gamification_service(session).hearts_state(user_id)


async def lose_heart(session: AsyncSession, user_id: UUID) -> HeartsView:
    """Deduct one heart (floor 0, no-op for unlimited plans); never blocks the caller."""
    return await build_gamification_service(session).lose_heart(user_id)


async def merge_guest(session: AsyncSession, from_id: UUID, into_id: UUID) -> None:
    await build_gamification_service(session).merge_guest(from_id, into_id)


async def progress_stats(session: AsyncSession, user_id: UUID, since: date) -> ProgressStats:
    """Lifetime xp/streak/lesson counters and xp per Tashkent day from `since` on."""
    return await SqlProgressReader(session).read(user_id, since)
