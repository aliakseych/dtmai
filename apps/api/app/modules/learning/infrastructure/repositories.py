from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.learning.domain.mastery import Mastery
from app.modules.learning.domain.merge import (
    merge_mastery,
    merge_rating,
    src_card_wins,
    src_placement_wins,
)
from app.modules.learning.domain.session import COMPLETED, IN_PROGRESS, Mode, SessionRec
from app.modules.learning.domain.srs import Card
from app.modules.learning.infrastructure.orm import (
    NIL,
    AttemptRow,
    MasteryRow,
    PlacementRow,
    ProcessedEventRow,
    RatingRow,
    ReviewCardRow,
    SessionRow,
)
from app.shared.ids import new_id


def _rec(r: SessionRow) -> SessionRec:
    return SessionRec(
        id=r.id,
        user_id=r.user_id,
        mode=Mode(r.mode),
        subject_id=r.subject_id,
        topic_id=r.topic_id,
        lesson_id=r.lesson_id,
        language=r.language,
        question_ids=[UUID(q) for q in r.question_ids],
        started_at=r.started_at,
        status=r.status,
        correct=r.correct,
        answered=r.answered,
        meta=dict(r.meta or {}),
        finished_at=r.finished_at,
    )


class SqlLearningRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def completed_lesson_ids(self, user_id: UUID, lesson_ids: list[UUID]) -> set[UUID]:
        if not lesson_ids:
            return set()
        rows = await self._s.scalars(
            select(SessionRow.lesson_id)
            .where(
                SessionRow.user_id == user_id,
                SessionRow.mode == Mode.LESSON.value,
                SessionRow.status == COMPLETED,
                SessionRow.lesson_id.in_(lesson_ids),
            )
            .distinct()
        )
        return {r for r in rows if r is not None}

    # sessions
    async def add_session(self, rec: SessionRec) -> None:
        self._s.add(
            SessionRow(
                id=rec.id,
                user_id=rec.user_id,
                mode=rec.mode.value,
                subject_id=rec.subject_id,
                topic_id=rec.topic_id,
                lesson_id=rec.lesson_id,
                language=rec.language,
                question_ids=[str(q) for q in rec.question_ids],
                status=rec.status,
                correct=rec.correct,
                answered=rec.answered,
                meta=rec.meta,
                started_at=rec.started_at,
            )
        )
        await self._s.flush()

    async def get_session(self, session_id: UUID, *, lock: bool = False) -> SessionRec | None:
        q = select(SessionRow).where(SessionRow.id == session_id)
        if lock:
            q = q.with_for_update()
        row = (await self._s.execute(q)).scalar_one_or_none()
        return _rec(row) if row else None

    async def save_session(self, rec: SessionRec) -> None:
        await self._s.execute(
            update(SessionRow)
            .where(SessionRow.id == rec.id)
            .values(
                status=rec.status,
                correct=rec.correct,
                answered=rec.answered,
                meta=rec.meta,
                finished_at=rec.finished_at,
            )
        )

    async def open_sessions(self, user_id: UUID, mode: Mode) -> list[SessionRec]:
        """The user's in-progress sessions of `mode`, row-locked."""
        res = await self._s.execute(
            select(SessionRow)
            .where(
                SessionRow.user_id == user_id,
                SessionRow.mode == mode.value,
                SessionRow.status == IN_PROGRESS,
            )
            .with_for_update()
        )
        return [_rec(r) for r in res.scalars()]

    async def answered_ids(self, session_id: UUID) -> set[UUID]:
        res = await self._s.execute(
            select(AttemptRow.question_id).where(AttemptRow.session_id == session_id)
        )
        return set(res.scalars())

    async def seen_ids(self, user_id: UUID, limit: int = 200) -> list[UUID]:
        res = await self._s.execute(
            select(AttemptRow.question_id)
            .where(AttemptRow.user_id == user_id)
            .order_by(AttemptRow.created_at.desc())
            .limit(limit)
        )
        return list(dict.fromkeys(res.scalars()))

    async def add_attempt(
        self,
        *,
        session_id: UUID,
        user_id: UUID,
        question_id: UUID,
        correct: bool,
        response: dict,
        time_ms: int | None,
        elo_delta: int,
    ) -> bool:
        """False when this (session, question) was already answered."""
        stmt = (
            pg_insert(AttemptRow)
            .values(
                id=new_id(),
                session_id=session_id,
                user_id=user_id,
                question_id=question_id,
                correct=correct,
                response=response,
                time_ms=time_ms,
                elo_delta=elo_delta,
            )
            .on_conflict_do_nothing(constraint="uq_attempts_session_question")
            .returning(AttemptRow.id)
        )
        return (await self._s.execute(stmt)).first() is not None

    # rating
    async def rating(self, user_id: UUID, subject_id: UUID, default: float) -> float:
        r = await self._s.get(RatingRow, (user_id, subject_id))
        return r.elo if r else default

    async def set_rating(self, user_id: UUID, subject_id: UUID, elo: float) -> None:
        stmt = pg_insert(RatingRow).values(user_id=user_id, subject_id=subject_id, elo=elo)
        await self._s.execute(
            stmt.on_conflict_do_update(index_elements=["user_id", "subject_id"], set_={"elo": elo})
        )

    # mastery
    async def mastery(self, user_id: UUID, topic_id: UUID | None, type_id: UUID) -> Mastery:
        r = await self._s.get(MasteryRow, (user_id, topic_id or NIL, type_id))
        return Mastery(r.score, r.attempts, r.correct) if r else Mastery()

    async def set_mastery(
        self, user_id: UUID, subject_id: UUID, topic_id: UUID | None, type_id: UUID, m: Mastery
    ) -> None:
        vals = {
            "subject_id": subject_id,
            "score": m.score,
            "attempts": m.attempts,
            "correct": m.correct,
        }
        stmt = pg_insert(MasteryRow).values(
            user_id=user_id, topic_id=topic_id or NIL, type_id=type_id, **vals
        )
        await self._s.execute(
            stmt.on_conflict_do_update(index_elements=["user_id", "topic_id", "type_id"], set_=vals)
        )

    async def weak_mastery(
        self, user_id: UUID, subject_id: UUID
    ) -> list[tuple[UUID, UUID, Mastery]]:
        res = await self._s.execute(
            select(MasteryRow).where(
                MasteryRow.user_id == user_id, MasteryRow.subject_id == subject_id
            )
        )
        return [
            (r.topic_id, r.type_id, Mastery(r.score, r.attempts, r.correct)) for r in res.scalars()
        ]

    # SRS
    async def card(self, user_id: UUID, question_id: UUID) -> Card | None:
        r = await self._s.get(ReviewCardRow, (user_id, question_id))
        return Card(r.ease, r.interval_days, r.reps, r.lapses, r.due_at) if r else None

    async def set_card(
        self,
        user_id: UUID,
        question_id: UUID,
        subject_id: UUID,
        topic_id: UUID | None,
        type_id: UUID,
        c: Card,
    ) -> None:
        vals = {
            "subject_id": subject_id,
            "topic_id": topic_id or NIL,
            "type_id": type_id,
            "ease": c.ease,
            "interval_days": c.interval_days,
            "reps": c.reps,
            "lapses": c.lapses,
            "due_at": c.due_at,
        }
        stmt = pg_insert(ReviewCardRow).values(user_id=user_id, question_id=question_id, **vals)
        await self._s.execute(
            stmt.on_conflict_do_update(index_elements=["user_id", "question_id"], set_=vals)
        )

    async def due_question_ids(
        self, user_id: UUID, subject_id: UUID, now: datetime, limit: int
    ) -> list[UUID]:
        res = await self._s.execute(
            select(ReviewCardRow.question_id)
            .where(
                ReviewCardRow.user_id == user_id,
                ReviewCardRow.subject_id == subject_id,
                ReviewCardRow.due_at <= now,
            )
            .order_by(ReviewCardRow.due_at)
            .limit(limit)
        )
        return list(res.scalars())

    async def due_count(self, user_id: UUID, subject_id: UUID | None, now: datetime) -> int:
        from sqlalchemy import func

        q = (
            select(func.count())
            .select_from(ReviewCardRow)
            .where(ReviewCardRow.user_id == user_id, ReviewCardRow.due_at <= now)
        )
        if subject_id:
            q = q.where(ReviewCardRow.subject_id == subject_id)
        return int((await self._s.execute(q)).scalar_one())

    # placement
    async def placement(self, user_id: UUID, subject_id: UUID) -> PlacementRow | None:
        return await self._s.get(PlacementRow, (user_id, subject_id))

    async def set_placement(
        self,
        user_id: UUID,
        subject_id: UUID,
        start_unit_index: int,
        ability: float | None,
        skipped: bool,
    ) -> None:
        vals = {"start_unit_index": start_unit_index, "ability": ability, "skipped": skipped}
        stmt = pg_insert(PlacementRow).values(user_id=user_id, subject_id=subject_id, **vals)
        await self._s.execute(
            stmt.on_conflict_do_update(index_elements=["user_id", "subject_id"], set_=vals)
        )

    # events
    async def mark_event(self, event_id: UUID, handler: str) -> bool:
        stmt = (
            pg_insert(ProcessedEventRow)
            .values(event_id=event_id, handler=handler)
            .on_conflict_do_nothing()
            .returning(ProcessedEventRow.event_id)
        )
        return (await self._s.execute(stmt)).first() is not None

    # guest merge
    async def merge(self, from_id: UUID, into_id: UUID) -> None:
        s = self._s
        for model in (SessionRow, AttemptRow):
            await s.execute(update(model).where(model.user_id == from_id).values(user_id=into_id))
        await self._merge_rows(into_id, from_id)

    async def _merge_rows(self, into_id: UUID, from_id: UUID) -> None:
        s = self._s

        async def pairs(model, key):  # noqa: ANN001, ANN202
            mine = {
                key(r): r
                for r in (await s.scalars(select(model).where(model.user_id == into_id))).all()
            }
            for src in (await s.scalars(select(model).where(model.user_id == from_id))).all():
                yield mine.get(key(src)), src

        async for dst, src in pairs(RatingRow, lambda r: r.subject_id):
            if dst is None:
                src.user_id = into_id
            else:
                dst.elo = merge_rating(dst.elo, src.elo)
                await s.delete(src)
        async for dst, src in pairs(MasteryRow, lambda r: (r.topic_id, r.type_id)):
            if dst is None:
                src.user_id = into_id
            else:
                dst.score, dst.attempts, dst.correct = merge_mastery(
                    (dst.score, dst.attempts, dst.correct), (src.score, src.attempts, src.correct)
                )
                await s.delete(src)
        async for dst, src in pairs(ReviewCardRow, lambda r: r.question_id):
            if dst is None:
                src.user_id = into_id
            elif src_card_wins(dst.reps, src.reps):
                for f in ("ease", "interval_days", "reps", "lapses", "due_at"):
                    setattr(dst, f, getattr(src, f))
                await s.delete(src)
            else:
                await s.delete(src)
        async for dst, src in pairs(PlacementRow, lambda r: r.subject_id):
            if dst is None:
                src.user_id = into_id
            else:
                if src_placement_wins(dst.skipped, src.skipped):
                    for f in ("start_unit_index", "ability", "skipped", "completed_at"):
                        setattr(dst, f, getattr(src, f))
                await s.delete(src)
        await s.flush()
