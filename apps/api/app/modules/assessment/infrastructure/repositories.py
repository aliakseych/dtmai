from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.assessment.domain.attempt import IN_PROGRESS, SUBMITTED, MockAttempt
from app.modules.assessment.infrastructure.orm import MockAttemptRow


def _rec(r: MockAttemptRow) -> MockAttempt:
    return MockAttempt(
        id=r.id, user_id=r.user_id, kind=r.kind, blueprint_id=r.blueprint_id,
        blueprint_version=r.blueprint_version, language=r.language, started_at=r.started_at,
        deadline=r.deadline, questions=list(r.questions), sections=list(r.sections), status=r.status,
        answers=dict(r.answers or {}), flags=list(r.flags or []), result=r.result,
        submit_reason=r.submit_reason, submitted_at=r.submitted_at, score=r.score,
    )


class SqlAttemptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, a: MockAttempt) -> None:
        self._s.add(MockAttemptRow(
            id=a.id, user_id=a.user_id, kind=a.kind, blueprint_id=a.blueprint_id,
            blueprint_version=a.blueprint_version, language=a.language, status=a.status,
            started_at=a.started_at, deadline=a.deadline, questions=a.questions, sections=a.sections,
            answers=a.answers, flags=a.flags,
        ))
        await self._s.flush()

    async def get(self, attempt_id: UUID, *, lock: bool = False) -> MockAttempt | None:
        q = select(MockAttemptRow).where(MockAttemptRow.id == attempt_id)
        if lock:
            q = q.with_for_update()
        r = (await self._s.execute(q)).scalar_one_or_none()
        return _rec(r) if r else None

    async def active_for(self, user_id: UUID, *, lock: bool = False) -> MockAttempt | None:
        q = select(MockAttemptRow).where(MockAttemptRow.user_id == user_id, MockAttemptRow.status == IN_PROGRESS)
        if lock:
            q = q.with_for_update()
        r = (await self._s.execute(q)).scalar_one_or_none()
        return _rec(r) if r else None

    async def has_active(self, user_id: UUID) -> bool:
        q = select(MockAttemptRow.id).where(MockAttemptRow.user_id == user_id, MockAttemptRow.status == IN_PROGRESS)
        return (await self._s.execute(q.limit(1))).first() is not None

    async def history(self, user_id: UUID, limit: int) -> list[MockAttempt]:
        q = (select(MockAttemptRow).where(MockAttemptRow.user_id == user_id, MockAttemptRow.status == SUBMITTED)
             .order_by(MockAttemptRow.started_at.desc()).limit(limit))
        return [_rec(r) for r in (await self._s.execute(q)).scalars()]

    async def expired_ids(self, now: datetime, limit: int) -> list[UUID]:
        q = (select(MockAttemptRow.id).where(MockAttemptRow.status == IN_PROGRESS, MockAttemptRow.deadline <= now)
             .order_by(MockAttemptRow.deadline).limit(limit))
        return list((await self._s.execute(q)).scalars())

    async def save(self, a: MockAttempt) -> None:
        r = await self._s.get(MockAttemptRow, a.id)
        assert r is not None
        r.status, r.answers, r.flags, r.result = a.status, a.answers, a.flags, a.result
        r.submit_reason, r.submitted_at, r.score = a.submit_reason, a.submitted_at, a.score
        await self._s.flush()
