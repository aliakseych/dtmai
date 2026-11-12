import math
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.assessment.domain.attempt import MockAttempt, deadline_for, rewardable
from app.modules.assessment.domain.comparison import Comparison, compare
from app.modules.assessment.domain.prediction import Prediction, predict
from app.modules.assessment.domain.scoring import Scored, max_score, score
from app.modules.assessment.infrastructure.repositories import SqlAttemptRepository
from app.modules.assessment.ports import Blueprint, ContentPort, Item, LyceumBenchmarkPort, UserPort
from app.shared.errors import Conflict, Forbidden, NotFound, ValidationFailed
from app.shared.events import Event, publish
from app.shared.ids import new_id

STARTABLE_KINDS = ("official", "generated")  # templates are authoring drafts, never runnable
PERSONAL_MIN = 10
PERSONAL_MAX = 60
PERSONAL_MIN_PER_QUESTION = 1.5


@dataclass(frozen=True, slots=True)
class AttemptView:
    attempt: MockAttempt
    items: list[Item]
    server_now: datetime
    time_left_s: int
    accepted: bool = True  # False: the save arrived after the deadline and was not applied


@dataclass(frozen=True, slots=True)
class ResultView:
    attempt: MockAttempt
    comparison: Comparison | None


@dataclass(frozen=True, slots=True)
class PredictionView:
    prediction: Prediction | None
    comparison: Comparison | None


def served_weight(weight: float, served: int, requested: int) -> float:
    """An underfilled section counts proportionally, so max_total reflects the questions actually served."""
    return weight * min(1.0, served / requested) if requested > 0 else weight


def _snap(item: Item, section: int) -> dict[str, Any]:
    return {
        "id": str(item.id),
        "subject_id": str(item.subject_id),
        "topic_id": str(item.topic_id) if item.topic_id else None,
        "type_id": str(item.type_id),
        "section": section,
    }


class AssessmentService:
    def __init__(
        self,
        repo: SqlAttemptRepository,
        content: ContentPort,
        users: UserPort,
        benchmark: Callable[[], LyceumBenchmarkPort],
        session: AsyncSession,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._r, self._c, self._u, self._bench, self._s, self._now = (
            repo,
            content,
            users,
            benchmark,
            session,
            clock,
        )

    # ---- catalogue --------------------------------------------------------
    async def list_mocks(self) -> list[Blueprint]:
        return await self._c.blueprints()

    # ---- starting ---------------------------------------------------------
    async def _guard_no_active(self, user_id: UUID) -> None:
        active = await self._r.active_for(user_id, lock=True)
        if active is None:
            return
        if active.expired(self._now()):
            await self._finalize(active, reason="auto")
            return
        raise Conflict("finish the active mock first", code="active_attempt_exists")

    async def start(self, user_id: UUID, blueprint_id: UUID, language: str) -> AttemptView:
        await self._guard_no_active(user_id)
        bp = await self._c.blueprint(blueprint_id)
        if bp is None or bp.status != "published" or bp.kind not in STARTABLE_KINDS:
            raise NotFound("mock not found", code="mock_not_found")
        questions: list[dict[str, Any]] = []
        sections: list[dict[str, Any]] = []
        used: list[UUID] = []
        for idx, sec in enumerate(bp.sections):
            subject_id = UUID(str(sec["subject_id"]))
            fixed = [UUID(str(q)) for q in sec.get("question_ids") or []]
            if fixed:
                items = await self._c.items(fixed)
            else:
                items = await self._c.pick(
                    subject_id=subject_id,
                    topic_ids=[UUID(str(t)) for t in sec.get("topic_ids") or []] or None,
                    type_ids=[UUID(str(t)) for t in sec.get("type_ids") or []] or None,
                    language=language,
                    n=int(sec["count"]),
                    exclude_ids=used,
                )
            if not items:
                raise Conflict("not enough questions for this mock", code="no_questions")
            requested = len(fixed) if fixed else int(sec["count"])
            used += [i.id for i in items]
            questions += [_snap(i, idx) for i in items]
            sections.append(
                {
                    "subject_id": str(subject_id),
                    "count": len(items),
                    "weight": served_weight(float(sec.get("weight", 1.0)), len(items), requested),
                }
            )
        return await self._open(
            user_id, bp.kind, bp.id, bp.version, language, bp.duration_min, questions, sections
        )

    async def start_personal(
        self, user_id: UUID, subject_id: UUID, language: str, count: int
    ) -> AttemptView:
        if not await self._u.has_feature(user_id, "personal_mock"):
            raise Forbidden("personal mocks are a premium feature", code="premium_required")
        if not 5 <= count <= 90:
            raise ValidationFailed("count must be 5..90", code="invalid_count")
        await self._guard_no_active(user_id)
        spots = await self._c.weak_spots(user_id, subject_id)
        items: list[Item] = []
        if spots:
            share = math.ceil(count * 0.7 / len(spots))  # ~70% weak areas, rest general
            for s in spots:
                items += await self._c.pick(
                    subject_id=subject_id,
                    topic_ids=[s.topic_id] if s.topic_id else None,
                    type_ids=[s.type_id],
                    language=language,
                    n=share,
                    exclude_ids=[i.id for i in items],
                )
            items = items[: math.ceil(count * 0.7)]
        items += await self._c.pick(
            subject_id=subject_id,
            topic_ids=None,
            type_ids=None,
            language=language,
            n=count - len(items),
            exclude_ids=[i.id for i in items],
        )
        if not items:
            raise Conflict("not enough questions", code="no_questions_personal")
        minutes = min(
            PERSONAL_MAX * 3, max(PERSONAL_MIN, math.ceil(len(items) * PERSONAL_MIN_PER_QUESTION))
        )
        return await self._open(
            user_id,
            "personal",
            None,
            None,
            language,
            minutes,
            [_snap(i, 0) for i in items],
            [
                {
                    "subject_id": str(subject_id),
                    "weight": served_weight(1.0, len(items), count),
                    "count": len(items),
                }
            ],
        )

    async def _open(
        self,
        user_id: UUID,
        kind: str,
        blueprint_id: UUID | None,
        version: int | None,
        language: str,
        duration_min: int,
        questions: list[dict[str, Any]],
        sections: list[dict[str, Any]],
    ) -> AttemptView:
        now = self._now()
        a = MockAttempt(
            new_id(),
            user_id,
            kind,
            blueprint_id,
            version,
            language,
            now,
            deadline_for(now, duration_min),
            questions,
            sections,
        )
        try:
            await self._r.add(a)
        except IntegrityError as e:  # concurrent start lost the unique-active race
            raise Conflict("finish the active mock first", code="active_attempt_exists") from e
        return await self._view(a)

    # ---- reading / autosave ----------------------------------------------
    async def _view(self, a: MockAttempt, accepted: bool = True) -> AttemptView:
        items = await self._c.items([UUID(q["id"]) for q in a.questions])
        now = self._now()
        return AttemptView(a, items, now, a.time_left(now), accepted)

    async def _owned(self, user_id: UUID, attempt_id: UUID, *, lock: bool = False) -> MockAttempt:
        a = await self._r.get(attempt_id, lock=lock)
        if a is None:
            raise NotFound("attempt not found", code="attempt_not_found")
        if a.user_id != user_id:
            raise Forbidden("not your attempt", code="forbidden")
        return a

    async def active(self, user_id: UUID) -> AttemptView | None:
        a = await self._r.active_for(user_id, lock=True)
        if a is None:
            return None
        if a.expired(self._now()):
            await self._finalize(a, reason="auto")
            return None
        return await self._view(a)

    async def get(self, user_id: UUID, attempt_id: UUID) -> AttemptView:
        a = await self._owned(user_id, attempt_id, lock=True)
        if a.expired(self._now()):
            await self._finalize(a, reason="auto")
        return await self._view(a)

    async def save(
        self,
        user_id: UUID,
        attempt_id: UUID,
        answers: dict[str, dict[str, Any]] | None,
        flags: list[str] | None,
    ) -> AttemptView:
        a = await self._owned(user_id, attempt_id, lock=True)
        now = self._now()
        if not a.active:
            return await self._view(a, accepted=False)
        accepted = a.apply_save(now, answers, flags)
        if a.expired(now):  # past the deadline: lock in what we have
            await self._finalize(a, reason="auto")
        else:
            await self._r.save(a)
        return await self._view(a, accepted=accepted)

    # ---- submitting ---------------------------------------------------------
    async def submit(self, user_id: UUID, attempt_id: UUID) -> ResultView:
        a = await self._owned(user_id, attempt_id, lock=True)
        if a.active:
            await self._finalize(a, reason="auto" if a.expired(self._now()) else "manual")
        return await self._result_view(a)

    async def _finalize(self, a: MockAttempt, *, reason: str) -> None:
        a.close(self._now(), reason=reason)
        scored: list[Scored] = []
        review: list[dict[str, Any]] = []
        for q in a.questions:
            resp = a.answers.get(q["id"])
            correct, correct_resp = False, {}
            if resp is not None:
                g = await self._c.grade(UUID(q["id"]), resp)
                correct, correct_resp = g.correct, g.correct_response
            scored.append(
                Scored(q["section"], q["subject_id"], q["topic_id"], q["type_id"], correct)
            )
            review.append(
                {
                    "question_id": q["id"],
                    "answered": resp is not None,
                    "correct": correct,
                    "response": resp,
                    "correct_response": correct_resp,
                }
            )
        weights = [float(s["weight"]) for s in a.sections]
        res = score(scored, weights)
        a.score = res.total
        a.result = {
            "total": res.total,
            "max_total": res.max_total,
            "subject_scores": res.subject_scores,
            "correct": res.correct,
            "questions": res.answered_total,
            "review": review,
            "breakdown": [
                {
                    "topic_id": b.topic_id,
                    "type_id": b.type_id,
                    "correct": b.correct,
                    "total": b.total,
                }
                for b in res.breakdown
            ],
        }
        await self._r.save(a)
        answered = sum(1 for r in review if r["answered"])
        for q, r in zip(a.questions, review, strict=True):
            if not r["answered"]:  # a skip carries no signal for mastery/SRS/question stats
                continue
            await publish(
                self._s,
                Event(
                    "AttemptGraded",
                    {
                        "user_id": str(a.user_id),
                        "question_id": q["id"],
                        "question_type_id": q["type_id"],
                        "topic_id": q["topic_id"],
                        "subject_id": q["subject_id"],
                        "correct": r["correct"],
                        "mode": "mock",
                        "session_id": str(a.id),
                    },
                ),
            )
        await publish(
            self._s,
            Event(
                "MockSubmitted",
                {
                    "user_id": str(a.user_id),
                    "attempt_id": str(a.id),
                    "score": res.total,
                    "subject_scores": res.subject_scores,
                    "kind": a.kind,
                    "blueprint_id": str(a.blueprint_id) if a.blueprint_id else None,
                    "answered": answered,
                    "questions": len(a.questions),
                    "rewardable": rewardable(answered, len(a.questions)),
                },
            ),
        )

    async def auto_submit_expired(self, limit: int = 100) -> int:
        """Background sweep: finalize every attempt past its deadline."""
        n = 0
        for attempt_id in await self._r.expired_ids(self._now(), limit):
            a = await self._r.get(attempt_id, lock=True)
            if a is not None and a.expired(self._now()):
                await self._finalize(a, reason="auto")
                n += 1
        return n

    # ---- results -------------------------------------------------------------
    async def _comparison(self, user_id: UUID, value: float) -> Comparison | None:
        lyceum_id = await self._u.target_lyceum_id(user_id)
        if lyceum_id is None:
            return None
        b = await self._bench().benchmark(lyceum_id)
        if b is None:
            return None
        return compare(
            value, passing_score=b.passing_score, competition_ratio=b.competition_ratio, year=b.year
        )

    async def _result_view(self, a: MockAttempt) -> ResultView:
        if a.kind == "personal":  # raw score on a personal scale is not comparable to a lyceum bar
            return ResultView(a, None)
        return ResultView(a, await self._comparison(a.user_id, a.score or 0.0))

    async def result(self, user_id: UUID, attempt_id: UUID) -> ResultView:
        a = await self._owned(user_id, attempt_id, lock=True)
        if a.expired(self._now()):
            await self._finalize(a, reason="auto")
        if a.active:
            raise Conflict("attempt not submitted yet", code="attempt_in_progress")
        return await self._result_view(a)

    async def history(self, user_id: UUID, limit: int = 20) -> list[MockAttempt]:
        return await self._r.history(user_id, limit)

    async def prediction(self, user_id: UUID) -> PredictionView:
        hist = [
            (
                a.score or 0.0,
                float(
                    (a.result or {}).get("max_total")
                    or max_score([s["weight"] for s in a.sections])
                ),
            )
            for a in await self._r.history(user_id, 10, exclude_personal=True)
        ]
        p = predict(hist)
        return PredictionView(p, await self._comparison(user_id, p.value) if p else None)

    async def has_active(self, user_id: UUID) -> bool:
        a = await self._r.active_for(user_id)
        return a is not None and not a.expired(self._now())
