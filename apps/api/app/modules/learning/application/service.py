import random
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.learning.domain import rush
from app.modules.learning.domain.elo import DEFAULT_PLAYER_ELO, compute_elo_delta, level_for
from app.modules.learning.domain.mastery import weakest
from app.modules.learning.domain.placement import PlacementState, PoolItem, start_unit_index
from app.modules.learning.domain.session import (
    ABANDONED,
    COMPLETED,
    IN_PROGRESS,
    Mode,
    SessionRec,
    can_start,
    costs_hearts,
    lesson_unlocked,
    validate_count,
    xp_base,
)
from app.modules.learning.domain.srs import new_card
from app.modules.learning.infrastructure.orm import NIL
from app.modules.learning.infrastructure.repositories import SqlLearningRepository
from app.modules.learning.ports import ContentPort, HeartsPort, Item
from app.shared.errors import Conflict, Forbidden, NotFound, ValidationFailed
from app.shared.events import Event, publish
from app.shared.ids import new_id

PLACEMENT_POOL = 24
REVIEW_DEFAULT = 10


@dataclass(frozen=True, slots=True)
class SessionView:
    id: UUID
    mode: str
    status: str
    subject_id: UUID | None
    total: int
    answered: int
    correct: int
    items: list[Item]
    hearts: int | None
    unlimited_hearts: bool
    ends_at: datetime | None = None  # rush only: server deadline


@dataclass(frozen=True, slots=True)
class AnswerResult:
    correct: bool
    correct_response: dict[str, Any]
    elo_delta: int
    hearts: int | None
    unlimited_hearts: bool
    answered: int
    total: int
    session_done: bool
    next_item: Item | None  # placement only
    streak: int | None = None  # rush only: current streak
    points: int | None = None  # rush only: running score


@dataclass(frozen=True, slots=True)
class FinishView:
    id: UUID
    mode: str
    status: str
    correct: int
    answered: int
    total: int
    xp_base: int
    start_unit_index: int | None
    best_streak: int | None = None  # rush only
    points: int | None = None  # rush only


@dataclass(frozen=True, slots=True)
class WeakArea:
    topic_id: UUID | None
    type_id: UUID
    score: float
    attempts: int


@dataclass(frozen=True, slots=True)
class PlacementView:
    start_unit_index: int
    ability: float | None
    skipped: bool


def _nil(v: UUID | None) -> UUID | None:
    return None if v is None or v == NIL else v


class LearningService:
    def __init__(
        self,
        repo: SqlLearningRepository,
        content: ContentPort,
        hearts: HeartsPort,
        session: AsyncSession,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._r = repo
        self._c = content
        self._h = hearts
        self._s = session
        self._now = clock

    # ---- starting -------------------------------------------------------
    async def _open(
        self,
        user_id: UUID,
        mode: Mode,
        items: list[Item],
        *,
        subject_id: UUID | None,
        topic_id: UUID | None = None,
        lesson_id: UUID | None = None,
        language: str,
        meta: dict[str, Any] | None = None,
        question_ids: list[UUID] | None = None,
    ) -> SessionRec:
        if not items:
            raise Conflict("no questions available", code="no_questions")
        now = self._now()
        for stale in await self._r.open_sessions(user_id, mode):
            await self._close(stale)  # earned xp of an unfinished rush/drill is never dropped
        rec = SessionRec(
            id=new_id(),
            user_id=user_id,
            mode=mode,
            subject_id=subject_id,
            topic_id=topic_id,
            lesson_id=lesson_id,
            language=language,
            question_ids=question_ids or [i.id for i in items],
            started_at=now,
            meta=meta or {},
        )
        await self._r.add_session(rec)
        return rec

    async def _hearts_gate(self, user_id: UUID, mode: Mode) -> None:
        hearts, unlimited = await self._h.state(user_id)
        can_start(mode, hearts, unlimited)

    async def _view(self, rec: SessionRec, items: list[Item]) -> SessionView:
        hearts, unlimited = await self._h.state(rec.user_id)
        ends = rec.meta.get("ends_at") if rec.mode is Mode.RUSH else None
        return SessionView(
            rec.id,
            rec.mode.value,
            rec.status,
            rec.subject_id,
            rec.total,
            rec.answered,
            rec.correct,
            items,
            hearts,
            unlimited,
            datetime.fromisoformat(ends) if ends else None,
        )

    async def start_lesson(self, user_id: UUID, lesson_id: UUID, language: str) -> SessionView:
        await self._hearts_gate(user_id, Mode.LESSON)
        ref = await self._c.lesson(lesson_id, language)
        if ref is None:
            raise NotFound("lesson not found", code="lesson_not_found")
        done, start_unit = await self.path_progress(
            user_id, ref.subject_id, [lid for unit in ref.path_units for lid in unit]
        )
        if not lesson_unlocked(ref.path_units, done, start_unit, lesson_id):
            raise Conflict("finish the previous lessons first", code="lesson_locked")
        items = await self._c.pick(
            subject_id=ref.subject_id,
            topic_ids=ref.topic_ids,
            type_ids=ref.type_ids,
            language=ref.language,
            n=validate_count(ref.count),
        )
        rec = await self._open(
            user_id,
            Mode.LESSON,
            items,
            subject_id=ref.subject_id,
            lesson_id=lesson_id,
            language=ref.language,
        )
        return await self._view(rec, items)

    async def start_drill(
        self,
        user_id: UUID,
        subject_id: UUID,
        topic_id: UUID | None,
        type_id: UUID | None,
        language: str,
        count: int,
        *,
        source_id: UUID | None = None,
        level: str | None = None,
        unsolved_only: bool = False,
    ) -> SessionView:
        await self._hearts_gate(user_id, Mode.DRILL)
        # Bank browsing: never repeat solved questions when asked; otherwise avoid recent ones.
        exclude = (
            await self._r.solved_ids(user_id)
            if unsolved_only
            else await self._r.seen_ids(user_id, 50)
        )
        items = await self._c.pick(
            subject_id=subject_id,
            topic_ids=[topic_id] if topic_id else None,
            type_ids=[type_id] if type_id else None,
            language=language,
            n=validate_count(count),
            exclude_ids=exclude,
            source_id=source_id,
            level=level,
        )
        if not items and not unsolved_only:  # all recently seen: allow repeats, not an empty drill
            items = await self._c.pick(
                subject_id=subject_id,
                topic_ids=[topic_id] if topic_id else None,
                type_ids=[type_id] if type_id else None,
                language=language,
                n=count,
                source_id=source_id,
                level=level,
            )
        rec = await self._open(
            user_id, Mode.DRILL, items, subject_id=subject_id, topic_id=topic_id, language=language
        )
        return await self._view(rec, items)

    async def start_review(
        self, user_id: UUID, subject_id: UUID, language: str, count: int = REVIEW_DEFAULT
    ) -> SessionView:
        n = validate_count(count)
        due_ids = await self._r.due_question_ids(user_id, subject_id, self._now(), n)
        items = await self._c.items(due_ids)
        chosen = {i.id for i in items}
        for topic_id, type_id, _m in await self._weak_ranked(user_id, subject_id, 5):
            if len(items) >= n:
                break
            more = await self._c.pick(
                subject_id=subject_id,
                topic_ids=[topic_id] if topic_id else None,
                type_ids=[type_id],
                language=language,
                n=n - len(items),
                exclude_ids=list(chosen),
            )
            items += more
            chosen |= {i.id for i in more}
        rec = await self._open(
            user_id,
            Mode.REVIEW,
            items,
            subject_id=subject_id,
            language=language,
            meta={"due": len(due_ids)},
        )
        return await self._view(rec, items)

    async def start_rush(self, user_id: UUID, subject_id: UUID, language: str) -> SessionView:
        """60 s run over verified questions (the bank only serves verified ones); the clock starts now."""
        pool = await self._c.pick(
            subject_id=subject_id,
            topic_ids=None,
            type_ids=None,
            language=language,
            n=rush.POOL_SIZE,
            exclude_ids=await self._r.seen_ids(user_id, 50),
        )
        if len(pool) < rush.POOL_SIZE:  # small bank: allow repeats rather than a short run
            pool = await self._c.pick(
                subject_id=subject_id,
                topic_ids=None,
                type_ids=None,
                language=language,
                n=rush.POOL_SIZE,
            )
        items = [i for i in pool if i.kind != "passage_group"]  # passages are too slow for a sprint
        random.shuffle(items)
        now = self._now()
        rec = await self._open(
            user_id,
            Mode.RUSH,
            items,
            subject_id=subject_id,
            language=language,
            meta={"ends_at": rush.deadline(now).isoformat(), "streak": 0, "best": 0, "points": 0},
        )
        return await self._view(rec, items)

    async def start_placement(self, user_id: UUID, subject_id: UUID, language: str) -> SessionView:
        pool = await self._c.pick(
            subject_id=subject_id,
            topic_ids=None,
            type_ids=None,
            language=language,
            n=PLACEMENT_POOL,
        )
        random.Random(str(user_id)).shuffle(pool)
        state = PlacementState([PoolItem(i.id, i.difficulty) for i in pool])
        first = state.next_item()
        if first is None:
            raise Conflict("no questions available", code="no_questions")
        meta = {
            "pool": [{"id": str(p.id), "d": p.difficulty} for p in state.pool],
            "theta": state.theta,
            "asked": [],
            "deltas": [],
        }
        rec = await self._open(
            user_id, Mode.PLACEMENT, pool, subject_id=subject_id, language=language, meta=meta
        )
        return await self._view(rec, [i for i in pool if i.id == first.id])

    async def skip_placement(self, user_id: UUID, subject_id: UUID) -> PlacementView:
        earned = await self._r.placement(user_id, subject_id)
        if earned is not None:  # never overwrite an earned (or earlier) placement
            return PlacementView(earned.start_unit_index, earned.ability, earned.skipped)
        await self._r.set_placement(user_id, subject_id, 0, None, True)
        return PlacementView(0, None, True)

    async def placement(self, user_id: UUID, subject_id: UUID) -> PlacementView | None:
        p = await self._r.placement(user_id, subject_id)
        return PlacementView(p.start_unit_index, p.ability, p.skipped) if p else None

    # ---- reading --------------------------------------------------------
    async def _owned(self, user_id: UUID, session_id: UUID, *, lock: bool = False) -> SessionRec:
        rec = await self._r.get_session(session_id, lock=lock)
        if rec is None:
            raise NotFound("session not found", code="session_not_found")
        if rec.user_id != user_id:
            raise Forbidden("not your session", code="forbidden")
        return rec

    @staticmethod
    def _state(rec: SessionRec) -> PlacementState:
        m = rec.meta
        s = PlacementState([PoolItem(UUID(p["id"]), float(p["d"])) for p in m["pool"]])
        s.theta = float(m["theta"])
        s.asked = [UUID(a) for a in m["asked"]]
        s.deltas = [float(d) for d in m["deltas"]]
        return s

    @staticmethod
    def _store(rec: SessionRec, s: PlacementState) -> None:
        rec.meta = {
            **rec.meta,
            "theta": s.theta,
            "asked": [str(a) for a in s.asked],
            "deltas": s.deltas,
        }

    async def get(self, user_id: UUID, session_id: UUID) -> SessionView:
        """Resume: remaining (unanswered) items."""
        rec = await self._owned(user_id, session_id)
        if rec.mode is Mode.PLACEMENT:
            nxt = self._state(rec).next_item() if rec.status == IN_PROGRESS else None
            items = await self._c.items([nxt.id]) if nxt else []
        else:
            done = await self._r.answered_ids(rec.id)
            items = await self._c.items([q for q in rec.question_ids if q not in done])
        return await self._view(rec, items)

    # ---- answering ------------------------------------------------------
    async def answer(
        self,
        user_id: UUID,
        session_id: UUID,
        question_id: UUID,
        response: dict[str, Any],
        time_ms: int | None,
    ) -> AnswerResult:
        rec = await self._owned(user_id, session_id, lock=True)
        if rec.status != IN_PROGRESS:
            raise Conflict("session is closed", code="session_closed")
        if rec.mode is Mode.RUSH and rush.is_expired(
            self._now(), datetime.fromisoformat(rec.meta["ends_at"])
        ):
            raise Conflict("time is up", code="rush_time_up")
        state: PlacementState | None = None
        pool_item: PoolItem | None = None
        if rec.mode is Mode.PLACEMENT:
            state = self._state(rec)
            pool_item = state.next_item()
            if pool_item is None or pool_item.id != question_id:
                raise Conflict("not the current placement question", code="wrong_question")
        elif question_id not in rec.question_ids:
            raise ValidationFailed("question not in session", code="question_not_in_session")

        found = await self._c.items([question_id])
        if not found:
            raise NotFound("question not found", code="question_not_found")
        item = found[0]
        graded = await self._c.grade(question_id, response)
        elo_delta = 0
        if rec.mode is not Mode.PLACEMENT:
            rating = await self._r.rating(user_id, item.subject_id, DEFAULT_PLAYER_ELO)
            elo_delta = compute_elo_delta(
                rating,
                item.difficulty,
                graded.correct,
                level_for(item.difficulty, official=item.official),
                (time_ms / 1000) if time_ms is not None else None,
            )
        if not await self._r.add_attempt(
            session_id=rec.id,
            user_id=user_id,
            question_id=question_id,
            correct=graded.correct,
            response=response,
            time_ms=time_ms,
            elo_delta=elo_delta,
        ):
            raise Conflict("already answered", code="already_answered")

        rec.answered += 1
        rec.correct += 1 if graded.correct else 0
        if rec.mode is Mode.RUSH:
            streak = int(rec.meta.get("streak", 0)) + 1 if graded.correct else 0
            points = int(rec.meta.get("points", 0))
            if graded.correct:
                points += rush.BASE_POINTS * rush.multiplier(streak)
            rec.meta = {
                **rec.meta,
                "streak": streak,
                "best": max(int(rec.meta.get("best", 0)), streak),
                "points": points,
            }
        if rec.mode is not Mode.PLACEMENT:
            await self._r.set_rating(
                user_id,
                item.subject_id,
                await self._r.rating(user_id, item.subject_id, DEFAULT_PLAYER_ELO) + elo_delta,
            )
            await self.apply_learning(user_id, item, graded.correct)

        hearts: int | None = None
        unlimited = False
        if costs_hearts(rec.mode) and not graded.correct:
            hearts = await self._h.lose(user_id)
        else:
            hearts, unlimited = await self._h.state(user_id)
        if costs_hearts(rec.mode):
            unlimited = (await self._h.state(user_id))[1]

        next_item: Item | None = None
        done = rec.done
        if state is not None and pool_item is not None:
            state.record(pool_item, graded.correct)
            self._store(rec, state)
            done = state.finished
            nxt = state.next_item()
            if nxt:
                next_item = (await self._c.items([nxt.id]) or [None])[0]
        await self._r.save_session(rec)
        if rec.mode is not Mode.PLACEMENT and rec.done:
            await self._complete(rec)

        await publish(
            self._s,
            Event(
                "AttemptGraded",
                {
                    "user_id": str(user_id),
                    "question_id": str(question_id),
                    "question_type_id": str(item.type_id),
                    "topic_id": str(item.topic_id),
                    "subject_id": str(item.subject_id),
                    "correct": graded.correct,
                    "mode": rec.mode.value,
                    "session_id": str(rec.id),
                },
            ),
        )
        return AnswerResult(
            graded.correct,
            graded.correct_response,
            elo_delta,
            hearts,
            unlimited,
            rec.answered,
            rec.total,
            done,
            next_item,
            streak=int(rec.meta.get("streak", 0)) if rec.mode is Mode.RUSH else None,
            points=int(rec.meta.get("points", 0)) if rec.mode is Mode.RUSH else None,
        )

    async def apply_learning(self, user_id: UUID, item: Item, correct: bool) -> None:
        """Mastery + spaced repetition update for one graded item."""
        m = await self._r.mastery(user_id, item.topic_id, item.type_id)
        m.record(correct)
        await self._r.set_mastery(user_id, item.subject_id, item.topic_id, item.type_id, m)
        card = await self._r.card(user_id, item.id)
        now = self._now()
        if card is None:
            if correct:
                return
            card = new_card(now)
        else:
            card.review(correct, now)
        await self._r.set_card(user_id, item.id, item.subject_id, item.topic_id, item.type_id, card)

    async def on_mock_attempt(self, event_id: UUID, payload: dict[str, Any]) -> None:
        """Mock answers feed mastery/SRS via events (mock sessions live in `assessment`)."""
        if payload.get("mode") != "mock" or not await self._r.mark_event(
            event_id, "attempt_graded"
        ):
            return
        found = await self._c.items([UUID(payload["question_id"])])
        if found:
            await self.apply_learning(UUID(payload["user_id"]), found[0], bool(payload["correct"]))

    # ---- finishing ------------------------------------------------------
    def _xp(self, rec: SessionRec) -> int:
        if rec.mode is Mode.RUSH:
            return rush.xp(rec.correct, int(rec.meta.get("best", 0)))
        return xp_base(rec.mode, rec.correct, rec.total)

    async def _complete(self, rec: SessionRec) -> None:
        """Mark a played session completed and emit SessionCompleted (xp is settled downstream)."""
        rec.status = COMPLETED
        rec.finished_at = self._now()
        await self._r.save_session(rec)
        # Rush is judged on what was answered, so the xp ceiling is per answered item.
        scored_total = rec.answered if rec.mode is Mode.RUSH else rec.total
        await publish(
            self._s,
            Event(
                "SessionCompleted",
                {
                    "user_id": str(rec.user_id),
                    "session_id": str(rec.id),
                    "mode": rec.mode.value,
                    "xp_base": self._xp(rec),
                    "correct": rec.correct,
                    "total": scored_total,
                },
            ),
        )

    async def _close(self, rec: SessionRec) -> int | None:
        """Settle an in-progress session: complete it when played, abandon otherwise.
        Returns the placement start unit when one was earned."""
        unit: int | None = None
        if rec.mode is Mode.PLACEMENT:
            state = self._state(rec)
            if state.finished and rec.subject_id:
                units = await self._c.unit_count(rec.subject_id, rec.language)
                unit = start_unit_index(state.theta, units)
                await self._r.set_placement(rec.user_id, rec.subject_id, unit, state.theta, False)
                rec.status = COMPLETED
            else:
                rec.status = ABANDONED
            rec.finished_at = self._now()
            await self._r.save_session(rec)
        elif rec.done or (rec.mode is Mode.RUSH and rec.answered > 0):
            await self._complete(rec)
        else:
            rec.status = ABANDONED
            rec.finished_at = self._now()
            await self._r.save_session(rec)
        return unit

    async def finish(self, user_id: UUID, session_id: UUID) -> FinishView:
        rec = await self._owned(user_id, session_id, lock=True)
        unit: int | None = None
        if rec.status == IN_PROGRESS:
            unit = await self._close(rec)
        elif rec.mode is Mode.PLACEMENT and rec.subject_id:
            p = await self._r.placement(user_id, rec.subject_id)
            unit = p.start_unit_index if p else None
        rush_meta = rec.mode is Mode.RUSH
        return FinishView(
            rec.id,
            rec.mode.value,
            rec.status,
            rec.correct,
            rec.answered,
            rec.total,
            self._xp(rec) if rec.status == COMPLETED else 0,
            unit,
            best_streak=int(rec.meta.get("best", 0)) if rush_meta else None,
            points=int(rec.meta.get("points", 0)) if rush_meta else None,
        )

    # ---- analytics ------------------------------------------------------
    async def _weak_ranked(self, user_id: UUID, subject_id: UUID, limit: int):  # noqa: ANN202
        rows = await self._r.weak_mastery(user_id, subject_id)
        by_key = {(t, ty): m for t, ty, m in rows}
        ranked = weakest([(k, m) for k, m in by_key.items()], limit)
        return [(_nil(k[0]), k[1], m) for k, m in ranked]  # type: ignore[index]

    async def weak_areas(self, user_id: UUID, subject_id: UUID, limit: int = 5) -> list[WeakArea]:
        return [
            WeakArea(t, ty, m.score, m.attempts)
            for t, ty, m in await self._weak_ranked(user_id, subject_id, limit)
        ]

    async def mastery(self, user_id: UUID, subject_id: UUID) -> list[WeakArea]:
        rows = await self._r.weak_mastery(user_id, subject_id)
        return sorted(
            (WeakArea(_nil(t), ty, m.score, m.attempts) for t, ty, m in rows), key=lambda w: w.score
        )

    async def path_progress(
        self, user_id: UUID, subject_id: UUID, lesson_ids: list[UUID]
    ) -> tuple[set[UUID], int]:
        """Completed lesson ids among `lesson_ids` and the placement start unit (0 if none)."""
        done = await self._r.completed_lesson_ids(user_id, lesson_ids)
        placement = await self._r.placement(user_id, subject_id)
        return done, (placement.start_unit_index if placement else 0)

    async def solved_ids(self, user_id: UUID) -> list[UUID]:
        return await self._r.solved_ids(user_id)

    async def due_count(self, user_id: UUID, subject_id: UUID | None) -> int:
        return await self._r.due_count(user_id, subject_id, self._now())

    async def merge_guest(self, from_id: UUID, into_id: UUID) -> None:
        if from_id != into_id:
            await self._r.merge(from_id, into_id)
