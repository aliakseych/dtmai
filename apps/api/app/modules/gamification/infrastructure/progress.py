from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.gamification.infrastructure.orm import UserStatsRow, XpLogRow


@dataclass(frozen=True, slots=True)
class ProgressStats:
    xp_total: int
    streak_current: int
    streak_best: int
    lessons_completed: int
    daily_xp: dict[date, int]


class SqlProgressReader:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def read(self, user_id: UUID, since: date) -> ProgressStats:
        row = await self._s.get(UserStatsRow, user_id)
        per_day = (
            await self._s.execute(
                select(XpLogRow.day, func.sum(XpLogRow.amount))
                .where(XpLogRow.user_id == user_id, XpLogRow.day >= since)
                .group_by(XpLogRow.day)
            )
        ).all()
        daily = {day: int(total) for day, total in per_day}
        if row is None:
            return ProgressStats(0, 0, 0, 0, daily)
        return ProgressStats(
            row.xp_total, row.streak_current, row.streak_longest, row.lessons_completed, daily
        )
