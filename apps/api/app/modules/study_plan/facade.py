from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.study_plan.wiring import build_plan_service

__all__ = ["today_summary"]


async def today_summary(session: AsyncSession, user_id: UUID) -> tuple[int, int]:
    """(open, total) planned tasks for today, for other modules' dashboards."""
    return await build_plan_service(session).today_counts(user_id)
