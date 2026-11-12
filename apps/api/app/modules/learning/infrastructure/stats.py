"""Adapters behind the stats ports: own attempts/mastery tables plus gamification and assessment facades."""

from datetime import UTC, date, datetime, time
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.assessment import facade as assessment
from app.modules.gamification import facade as gamification
from app.modules.learning.domain.stats import MockResult, Progress, SubjectAnswers
from app.modules.learning.infrastructure.orm import AttemptRow, MasteryRow, SessionRow

TASHKENT = ZoneInfo("Asia/Tashkent")


class SqlAnswerStats:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def daily(self, user_id: UUID, since: date) -> dict[date, tuple[int, int]]:
        day = func.date(func.timezone("Asia/Tashkent", AttemptRow.created_at))
        start = datetime.combine(since, time.min, tzinfo=TASHKENT).astimezone(UTC)
        rows = (
            await self._s.execute(
                select(day, func.count(), func.count().filter(AttemptRow.correct))
                .where(AttemptRow.user_id == user_id, AttemptRow.created_at >= start)
                .group_by(day)
            )
        ).all()
        return {d: (int(n), int(c)) for d, n, c in rows}

    async def by_subject(self, user_id: UUID) -> list[SubjectAnswers]:
        answers = (
            await self._s.execute(
                select(SessionRow.subject_id, func.count(), func.count().filter(AttemptRow.correct))
                .join(SessionRow, SessionRow.id == AttemptRow.session_id)
                .where(AttemptRow.user_id == user_id)
                .group_by(SessionRow.subject_id)
            )
        ).all()
        mastery = {
            subject: (float(weighted), int(attempts))
            for subject, weighted, attempts in (
                await self._s.execute(
                    select(
                        MasteryRow.subject_id,
                        func.sum(MasteryRow.score * MasteryRow.attempts),
                        func.sum(MasteryRow.attempts),
                    )
                    .where(MasteryRow.user_id == user_id)
                    .group_by(MasteryRow.subject_id)
                )
            ).all()
        }
        out = []
        for subject, n, c in answers:
            weighted, attempts = mastery.get(subject, (0.0, 0))
            out.append(
                SubjectAnswers(subject, int(n), int(c), weighted / attempts if attempts else None)
            )
        return out


class FacadeProgress:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def progress(self, user_id: UUID, since: date) -> Progress:
        p = await gamification.progress_stats(self._s, user_id, since)
        return Progress(
            p.xp_total, p.streak_current, p.streak_best, p.lessons_completed, p.daily_xp
        )


class FacadeMockResults:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def recent(self, user_id: UUID, limit: int) -> list[MockResult]:
        return [
            MockResult(m.mock_id, m.taken_at, m.score, m.max_score)
            for m in await assessment.mock_results(self._s, user_id, limit)
        ]
