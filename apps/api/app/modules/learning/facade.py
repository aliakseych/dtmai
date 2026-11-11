"""Public learning facade: other modules import only this."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.learning.application.service import WeakArea
from app.modules.learning.wiring import build_learning_service

__all__ = ["WeakArea", "merge_guest", "path_progress", "weak_areas"]


async def weak_areas(session: AsyncSession, user_id: UUID, subject_id: UUID, limit: int = 5) -> list[WeakArea]:
    return await build_learning_service(session).weak_areas(user_id, subject_id, limit)


async def merge_guest(session: AsyncSession, from_id: UUID, into_id: UUID) -> None:
    await build_learning_service(session).merge_guest(from_id, into_id)


async def path_progress(
    session: AsyncSession, user_id: UUID, subject_id: UUID, lesson_ids: list[UUID]
) -> tuple[set[UUID], int]:
    """(completed lesson ids among lesson_ids, placement start unit index)."""
    return await build_learning_service(session).path_progress(user_id, subject_id, lesson_ids)
