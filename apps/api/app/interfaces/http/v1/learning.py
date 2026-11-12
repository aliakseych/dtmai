from datetime import date, datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.interfaces.http.v1._media import MediaOut, to_media
from app.modules.catalog import facade as catalog
from app.modules.catalog.domain.models import pick_name
from app.modules.gamification import facade as gamification
from app.modules.identity.wiring import IdentityServiceDep
from app.modules.learning import facade as learning_facade
from app.modules.learning.application.service import (
    AnswerResult,
    FinishView,
    PlacementView,
    SessionView,
    WeakArea,
)
from app.modules.learning.domain.stats import UserStats
from app.modules.learning.ports import Item
from app.modules.learning.wiring import LearningServiceDep
from app.shared.db import get_session
from app.shared.deps import CurrentUser
from app.shared.errors import Forbidden, NotFound, ProblemDetails
from app.shared.events import commit_and_dispatch, dispatch_pending
from app.shared.locale import pick_locale
from app.shared.security import decode_access_token

ERR: dict[int | str, dict[str, Any]] = {
    401: {"model": ProblemDetails, "description": "Unauthorized"},
    403: {"model": ProblemDetails, "description": "Forbidden"},
    404: {"model": ProblemDetails, "description": "Not found"},
    409: {"model": ProblemDetails, "description": "Conflict"},
    422: {"model": ProblemDetails, "description": "Validation failed"},
}

router = APIRouter(tags=["learning"])
Session = Annotated[AsyncSession, Depends(get_session)]
AcceptLanguage = Annotated[str | None, Header()]


class ItemOut(BaseModel):
    """A question without its answer."""

    id: UUID
    subject_id: UUID
    topic_id: UUID
    type_id: UUID
    kind: str
    language: str
    stem: str
    media: list[MediaOut]
    payload: dict[str, Any]
    passage_id: UUID | None
    children: list["ItemOut"] = Field(
        default_factory=list,
        description="kind=passage_group only: the child questions (same shape, no answers) in passage order. "
        'Answer the group with response {"answers": {child_id: child_response}}.',
    )

    @classmethod
    def of(cls, i: Item) -> "ItemOut":
        return cls(
            id=i.id,
            subject_id=i.subject_id,
            topic_id=i.topic_id,
            type_id=i.type_id,
            kind=i.kind,
            language=i.language,
            stem=i.stem,
            media=to_media(i.media),
            payload=i.payload,
            passage_id=i.passage_id,
            children=[cls.of(c) for c in i.children],
        )


class SessionOut(BaseModel):
    id: UUID
    mode: str
    status: str
    subject_id: UUID | None
    total: int
    answered: int
    correct: int
    items: list[ItemOut]
    hearts: int | None
    unlimited_hearts: bool
    ends_at: datetime | None = Field(default=None, description="Rush only: server deadline")

    @classmethod
    def of(cls, v: SessionView) -> "SessionOut":
        return cls(
            id=v.id,
            mode=v.mode,
            status=v.status,
            subject_id=v.subject_id,
            total=v.total,
            answered=v.answered,
            correct=v.correct,
            items=[ItemOut.of(i) for i in v.items],
            hearts=v.hearts,
            unlimited_hearts=v.unlimited_hearts,
            ends_at=v.ends_at,
        )


class LessonStartIn(BaseModel):
    lesson_id: UUID
    language: str = Field(min_length=2, max_length=10, description="Content language (uz, ru, en)")


class DrillStartIn(BaseModel):
    subject_id: UUID
    topic_id: UUID | None = None
    type_id: UUID | None = None
    language: str = Field(min_length=2, max_length=10)
    count: int = Field(default=10, ge=1, le=30)
    source_id: UUID | None = None
    level: Literal["easy", "medium", "hard"] | None = None
    unsolved_only: bool = False


class ReviewStartIn(BaseModel):
    subject_id: UUID
    language: str = Field(min_length=2, max_length=10)
    count: int = Field(default=10, ge=1, le=30)


class PlacementStartIn(BaseModel):
    subject_id: UUID
    language: str = Field(min_length=2, max_length=10)


class RushStartIn(BaseModel):
    subject_id: UUID
    language: str = Field(min_length=2, max_length=10)


class AnswerIn(BaseModel):
    question_id: UUID
    response: dict[str, Any] = Field(
        description='Kind-specific response. For kind=passage_group: {"answers": {child_id: child_response}}; '
        "the group is correct only if every child is correct, unanswered children count as wrong."
    )
    time_ms: int | None = Field(default=None, ge=0)


class AnswerOut(BaseModel):
    correct: bool
    correct_response: dict[str, Any]
    elo_delta: int
    hearts: int | None
    unlimited_hearts: bool
    answered: int
    total: int
    session_done: bool
    next_item: ItemOut | None = Field(description="Placement only: the next adaptive question")
    streak: int | None = Field(default=None, description="Rush only: current streak")
    points: int | None = Field(default=None, description="Rush only: running score")

    @classmethod
    def of(cls, r: AnswerResult) -> "AnswerOut":
        return cls(
            correct=r.correct,
            correct_response=r.correct_response,
            elo_delta=r.elo_delta,
            hearts=r.hearts,
            unlimited_hearts=r.unlimited_hearts,
            answered=r.answered,
            total=r.total,
            session_done=r.session_done,
            next_item=ItemOut.of(r.next_item) if r.next_item else None,
            streak=r.streak,
            points=r.points,
        )


class FinishOut(BaseModel):
    id: UUID
    mode: str
    status: str
    correct: int
    answered: int
    total: int
    xp_base: int
    start_unit_index: int | None
    best_streak: int | None = Field(default=None, description="Rush only")
    points: int | None = Field(default=None, description="Rush only")

    @classmethod
    def of(cls, v: FinishView) -> "FinishOut":
        return cls(**{k: getattr(v, k) for k in cls.model_fields})


class PlacementOut(BaseModel):
    start_unit_index: int
    ability: float | None
    skipped: bool

    @classmethod
    def of(cls, v: PlacementView) -> "PlacementOut":
        return cls(start_unit_index=v.start_unit_index, ability=v.ability, skipped=v.skipped)


class WeakAreaOut(BaseModel):
    topic_id: UUID | None
    topic_name: str | None = None
    type_id: UUID
    score: float
    attempts: int

    @classmethod
    def of(cls, w: WeakArea, topic_name: str | None = None) -> "WeakAreaOut":
        return cls(
            topic_id=w.topic_id,
            topic_name=topic_name,
            type_id=w.type_id,
            score=w.score,
            attempts=w.attempts,
        )


async def _with_topic_names(
    session: AsyncSession, areas: list[WeakArea], locale: str
) -> list[WeakAreaOut]:
    names: dict[UUID, str] = {}
    for tid in {w.topic_id for w in areas if w.topic_id}:
        try:
            names[tid] = pick_name((await catalog.get_topic(session, tid)).names, locale)
        except NotFound:
            pass
    return [WeakAreaOut.of(w, names.get(w.topic_id) if w.topic_id else None) for w in areas]


class ReviewSummaryOut(BaseModel):
    due: int


class MergeGuestIn(BaseModel):
    guest_access_token: str


class OkOut(BaseModel):
    ok: bool = True


class DailyStatOut(BaseModel):
    date: date
    xp: int
    answered: int
    correct: int


class SubjectStatOut(BaseModel):
    subject_id: UUID
    answered: int
    correct: int
    mastery: float | None = Field(
        description="0..1, attempts-weighted over topics/types; null when unknown"
    )


class MockStatOut(BaseModel):
    mock_id: UUID
    taken_at: datetime
    score: float
    max_score: float


class StatsOut(BaseModel):
    xp_total: int
    streak_current: int
    streak_best: int
    lessons_completed: int
    accuracy: float = Field(description="correct / answered over all time, 0..1")
    daily: list[DailyStatOut] = Field(
        description="Last 30 Tashkent days, oldest first, zero-filled"
    )
    by_subject: list[SubjectStatOut]
    mocks: list[MockStatOut] = Field(description="Recent submitted mocks, newest first")

    @classmethod
    def of(cls, s: UserStats) -> "StatsOut":
        return cls(
            xp_total=s.xp_total,
            streak_current=s.streak_current,
            streak_best=s.streak_best,
            lessons_completed=s.lessons_completed,
            accuracy=s.accuracy,
            daily=[
                DailyStatOut(date=d.date, xp=d.xp, answered=d.answered, correct=d.correct)
                for d in s.daily
            ],
            by_subject=[
                SubjectStatOut(
                    subject_id=x.subject_id,
                    answered=x.answered,
                    correct=x.correct,
                    mastery=x.mastery,
                )
                for x in s.by_subject
            ],
            mocks=[
                MockStatOut(
                    mock_id=m.mock_id, taken_at=m.taken_at, score=m.score, max_score=m.max_score
                )
                for m in s.mocks
            ],
        )


@router.get("/me/stats", response_model=StatsOut, responses=ERR, operation_id="learning_my_stats")
async def my_stats(user: CurrentUser, session: Session) -> StatsOut:
    return StatsOut.of(await learning_facade.user_stats(session, user.user_id))


@router.post(
    "/lessons/start", response_model=SessionOut, responses=ERR, operation_id="learning_start_lesson"
)
async def start_lesson(
    body: LessonStartIn, user: CurrentUser, svc: LearningServiceDep
) -> SessionOut:
    return SessionOut.of(await svc.start_lesson(user.user_id, body.lesson_id, body.language))


@router.post(
    "/drills/start", response_model=SessionOut, responses=ERR, operation_id="learning_start_drill"
)
async def start_drill(
    body: DrillStartIn, user: CurrentUser, svc: LearningServiceDep, session: Session
) -> SessionOut:
    if body.source_id is not None:
        await catalog.require_learner_base(session, body.source_id)
    return SessionOut.of(
        await svc.start_drill(
            user.user_id,
            body.subject_id,
            body.topic_id,
            body.type_id,
            body.language,
            body.count,
            source_id=body.source_id,
            level=body.level,
            unsolved_only=body.unsolved_only,
        )
    )


@router.post(
    "/review/start", response_model=SessionOut, responses=ERR, operation_id="learning_start_review"
)
async def start_review(
    body: ReviewStartIn, user: CurrentUser, svc: LearningServiceDep
) -> SessionOut:
    return SessionOut.of(
        await svc.start_review(user.user_id, body.subject_id, body.language, body.count)
    )


@router.get(
    "/review/summary",
    response_model=ReviewSummaryOut,
    responses=ERR,
    operation_id="learning_review_summary",
)
async def review_summary(
    user: CurrentUser, svc: LearningServiceDep, subject_id: UUID | None = None
) -> ReviewSummaryOut:
    return ReviewSummaryOut(due=await svc.due_count(user.user_id, subject_id))


@router.post(
    "/placement/start",
    response_model=SessionOut,
    responses=ERR,
    operation_id="learning_start_placement",
)
async def start_placement(
    body: PlacementStartIn, user: CurrentUser, svc: LearningServiceDep
) -> SessionOut:
    return SessionOut.of(await svc.start_placement(user.user_id, body.subject_id, body.language))


@router.post(
    "/rush/start", response_model=SessionOut, responses=ERR, operation_id="learning_start_rush"
)
async def start_rush(body: RushStartIn, user: CurrentUser, svc: LearningServiceDep) -> SessionOut:
    """Question Rush: 60 s of verified questions; `ends_at` is the server deadline."""
    return SessionOut.of(await svc.start_rush(user.user_id, body.subject_id, body.language))


@router.post(
    "/placement/{subject_id}/skip",
    response_model=PlacementOut,
    responses=ERR,
    operation_id="learning_skip_placement",
)
async def skip_placement(
    subject_id: UUID, user: CurrentUser, svc: LearningServiceDep
) -> PlacementOut:
    return PlacementOut.of(await svc.skip_placement(user.user_id, subject_id))


@router.get(
    "/placement/{subject_id}",
    response_model=PlacementOut | None,
    responses=ERR,
    operation_id="learning_get_placement",
)
async def get_placement(
    subject_id: UUID, user: CurrentUser, svc: LearningServiceDep
) -> PlacementOut | None:
    p = await svc.placement(user.user_id, subject_id)
    return PlacementOut.of(p) if p else None


@router.get(
    "/sessions/{session_id}",
    response_model=SessionOut,
    responses=ERR,
    operation_id="learning_get_session",
)
async def get_session_view(
    session_id: UUID, user: CurrentUser, svc: LearningServiceDep
) -> SessionOut:
    return SessionOut.of(await svc.get(user.user_id, session_id))


@router.post(
    "/sessions/{session_id}/answers",
    response_model=AnswerOut,
    responses=ERR,
    operation_id="learning_answer",
)
async def answer(
    session_id: UUID, body: AnswerIn, user: CurrentUser, svc: LearningServiceDep
) -> AnswerOut:
    return AnswerOut.of(
        await svc.answer(user.user_id, session_id, body.question_id, body.response, body.time_ms)
    )


@router.post(
    "/sessions/{session_id}/finish",
    response_model=FinishOut,
    responses=ERR,
    operation_id="learning_finish",
)
async def finish(
    session_id: UUID, user: CurrentUser, svc: LearningServiceDep, session: Session
) -> FinishOut:
    out = FinishOut.of(await svc.finish(user.user_id, session_id))
    await commit_and_dispatch(
        session
    )  # credit XP/streak/quests now, not on the next scheduler tick
    return out


@router.get(
    "/mastery/{subject_id}",
    response_model=list[WeakAreaOut],
    responses=ERR,
    operation_id="learning_mastery",
)
async def mastery(
    subject_id: UUID,
    user: CurrentUser,
    svc: LearningServiceDep,
    session: Session,
    accept_language: AcceptLanguage = None,
) -> list[WeakAreaOut]:
    return await _with_topic_names(
        session, await svc.mastery(user.user_id, subject_id), pick_locale(accept_language)
    )


@router.get(
    "/weak-areas/{subject_id}",
    response_model=list[WeakAreaOut],
    responses=ERR,
    operation_id="learning_weak_areas",
)
async def weak_areas(
    subject_id: UUID,
    user: CurrentUser,
    svc: LearningServiceDep,
    session: Session,
    limit: int = 5,
    accept_language: AcceptLanguage = None,
) -> list[WeakAreaOut]:
    areas = await svc.weak_areas(user.user_id, subject_id, limit)
    return await _with_topic_names(session, areas, pick_locale(accept_language))


@router.post(
    "/merge-guest", response_model=OkOut, responses=ERR, operation_id="learning_merge_guest"
)
async def merge_guest(
    body: MergeGuestIn,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    identity: IdentityServiceDep,
) -> OkOut:
    """Merge a guest's progress into the signed-in account (needs the guest's own access token)."""
    if "guest" in user.roles:
        raise Forbidden("guests cannot be a merge target", code="guest_cannot_merge")
    guest = decode_access_token(body.guest_access_token)
    if "guest" not in guest.roles:
        raise Forbidden("token does not belong to a guest", code="not_a_guest")
    await dispatch_pending()  # flush the guest's outbox so no event lands after the merge
    await learning_facade.merge_guest(session, guest.user_id, user.user_id)
    await gamification.merge_guest(session, guest.user_id, user.user_id)
    await identity.retire_guest(guest.user_id, user.user_id)
    return OkOut()
