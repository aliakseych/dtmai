"""Public gamification facade: other modules import only this."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.gamification.application.service import HeartsView
from app.modules.gamification.wiring import build_gamification_service


async def hearts_state(session: AsyncSession, user_id: UUID) -> HeartsView:
    return await build_gamification_service(session).hearts_state(user_id)


async def lose_heart(session: AsyncSession, user_id: UUID) -> HeartsView:
    """Deduct one heart (floor 0, no-op for unlimited plans); never blocks the caller."""
    return await build_gamification_service(session).lose_heart(user_id)


async def merge_guest(session: AsyncSession, from_id: UUID, into_id: UUID) -> None:
    await build_gamification_service(session).merge_guest(from_id, into_id)
