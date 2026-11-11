"""Public learning facade: other modules import only this."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.learning.application.service import WeakArea
from app.modules.learning.domain.stats import UserStats
from app.modules.learning.wiring import build_learning_service, build_stats_service

__all__ = [
    "UserStats",
    "WeakArea",
    "due_review_count",
    "merge_guest",
    "path_progress",
    "user_stats",
    "weak_areas",
]


async def weak_areas(
    session: AsyncSession, user_id: UUID, subject_id: UUID, limit: int = 5
) -> list[WeakArea]:
    return await build_learning_service(session).weak_areas(user_id, subject_id, limit)


async def merge_guest(session: AsyncSession, from_id: UUID, into_id: UUID) -> None:
    await build_learning_service(session).merge_guest(from_id, into_id)


async def path_progress(
    session: AsyncSession, user_id: UUID, subject_id: UUID, lesson_ids: list[UUID]
) -> tuple[set[UUID], int]:
    """(completed lesson ids among lesson_ids, placement start unit index)."""
    return await build_learning_service(session).path_progress(user_id, subject_id, lesson_ids)


async def user_stats(session: AsyncSession, user_id: UUID) -> UserStats:
    """Per-learner stats: lifetime counters, 30-day series, per-subject mastery, recent mocks."""
    return await build_stats_service(session).user_stats(user_id)


async def due_review_count(session: AsyncSession, user_id: UUID, subject_id: UUID | None) -> int:
    """Mistakes due for spaced-repetition review now (all subjects when subject_id is None)."""
    return await build_learning_service(session).due_count(user_id, subject_id)
