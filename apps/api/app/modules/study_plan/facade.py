from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.study_plan.infrastructure.repositories import SqlPlanRepository
from app.modules.study_plan.wiring import build_plan_service

__all__ = ["merge_guest", "study_schedules", "today_summary"]


async def merge_guest(session: AsyncSession, from_id: UUID, into_id: UUID) -> None:
    await build_plan_service(session).merge_guest(from_id, into_id)


async def study_schedules(
    session: AsyncSession, user_ids: list[UUID]
) -> dict[UUID, tuple[str, tuple[int, ...]]]:
    """Learners' chosen (study_time "HH:MM", weekdays) for reminders; absent = none chosen."""
    return await SqlPlanRepository(session).study_schedules(user_ids)


async def today_summary(session: AsyncSession, user_id: UUID) -> tuple[int, int]:
    """(open, total) planned tasks for today, for other modules' dashboards."""
    return await build_plan_service(session).today_counts(user_id)
