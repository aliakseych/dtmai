from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.interfaces.http.v1._bounds import check_response_size
from app.interfaces.http.v1._media import MediaOut, to_media
from app.modules.assessment.application.service import AttemptView, PredictionView, ResultView
from app.modules.assessment.domain.attempt import MockAttempt
from app.modules.assessment.domain.comparison import Comparison
from app.modules.assessment.domain.prediction import Prediction
from app.modules.assessment.ports import Blueprint, Item
from app.modules.assessment.wiring import AssessmentServiceDep
from app.shared.db import get_session
from app.shared.deps import CurrentUser
from app.shared.errors import ProblemDetails
from app.shared.events import commit_and_dispatch

ERR: dict[int | str, dict[str, Any]] = {
    401: {"model": ProblemDetails, "description": "Unauthorized"},
    403: {"model": ProblemDetails, "description": "Forbidden"},
    404: {"model": ProblemDetails, "description": "Not found"},
    409: {"model": ProblemDetails, "description": "Conflict"},
    422: {"model": ProblemDetails, "description": "Validation failed"},
}

router = APIRouter(tags=["assessment"])


class MockOut(BaseModel):
    id: UUID
    code: str
    names: dict[str, str]
    kind: str
    version: int
    duration_min: int
    question_count: int
    source_id: UUID | None = None

    @classmethod
    def of(cls, b: Blueprint) -> "MockOut":
        return cls(
            id=b.id,
            code=b.code,
            names=b.names,
            kind=b.kind,
            version=b.version,
            duration_min=b.duration_min,
            question_count=sum(int(s.get("count", 0)) for s in b.sections),
            source_id=b.source_id,
        )


class ItemOut(BaseModel):
    id: UUID
    subject_id: UUID
    topic_id: UUID | None
    type_id: UUID
    kind: str
    language: str
    stem: str
    media: list[MediaOut]
    payload: dict[str, Any]
    passage_id: UUID | None
    section: int
    children: list["ItemOut"] = Field(
        default_factory=list,
        description="kind=passage_group only: the child questions (same shape, no answers) in passage order. "
        'Autosave the group under its own id with {"answers": {child_id: child_response}}.',
    )

    @classmethod
    def of(cls, i: Item, section: int) -> "ItemOut":
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
            section=section,
            children=[cls.of(c, section) for c in i.children],
        )


class SectionOut(BaseModel):
    subject_id: UUID
    weight: float
    count: int


class AttemptOut(BaseModel):
    id: UUID
    kind: str
    status: str
    blueprint_id: UUID | None
    blueprint_version: int | None
    language: str
    started_at: datetime
    deadline: datetime
    server_now: datetime
    time_left_s: int
    accepted: bool = Field(
        description="False when an autosave arrived after the deadline and was not applied"
    )
    sections: list[SectionOut]
    items: list[ItemOut]
    answers: dict[str, dict[str, Any]]
    flags: list[UUID]

    @classmethod
    def of(cls, v: AttemptView) -> "AttemptOut":
        a = v.attempt
        section_of = {q["id"]: q["section"] for q in a.questions}
        return cls(
            id=a.id,
            kind=a.kind,
            status=a.status,
            blueprint_id=a.blueprint_id,
            blueprint_version=a.blueprint_version,
            language=a.language,
            started_at=a.started_at,
            deadline=a.deadline,
            server_now=v.server_now,
            time_left_s=v.time_left_s,
            accepted=v.accepted,
            sections=[
                SectionOut(subject_id=UUID(s["subject_id"]), weight=s["weight"], count=s["count"])
                for s in a.sections
            ],
            items=[ItemOut.of(i, section_of[str(i.id)]) for i in v.items],
            answers=a.answers,
            flags=[UUID(f) for f in a.flags],
        )


class BreakdownOut(BaseModel):
    topic_id: UUID | None
    type_id: UUID
    correct: int
    total: int


class ReviewOut(BaseModel):
    question_id: UUID
    answered: bool
    correct: bool
    response: dict[str, Any] | None
    correct_response: dict[str, Any]


class ComparisonOut(BaseModel):
    year: int | None
    passing_score: float | None
    competition_ratio: float | None
    gap: float | None
    on_track: bool | None

    @classmethod
    def of(cls, c: Comparison) -> "ComparisonOut":
        return cls(
            year=c.year,
            passing_score=c.passing_score,
            competition_ratio=c.competition_ratio,
            gap=c.gap,
            on_track=c.on_track,
        )


class ResultOut(BaseModel):
    attempt_id: UUID
    kind: str
    status: str
    submit_reason: str | None
    submitted_at: datetime | None
    total: float
    max_total: float
    subject_scores: dict[UUID, float]
    correct: int
    questions: int
    breakdown: list[BreakdownOut]
    review: list[ReviewOut]
    comparison: ComparisonOut | None

    @classmethod
    def of(cls, v: ResultView) -> "ResultOut":
        a, r = v.attempt, v.attempt.result or {}
        return cls(
            attempt_id=a.id,
            kind=a.kind,
            status=a.status,
            submit_reason=a.submit_reason,
            submitted_at=a.submitted_at,
            total=r.get("total", 0.0),
            max_total=r.get("max_total", 0.0),
            subject_scores={UUID(k): val for k, val in r.get("subject_scores", {}).items()},
            correct=r.get("correct", 0),
            questions=r.get("questions", 0),
            breakdown=[BreakdownOut(**b) for b in r.get("breakdown", [])],
            review=[ReviewOut(**x) for x in r.get("review", [])],
            comparison=ComparisonOut.of(v.comparison) if v.comparison else None,
        )


class HistoryItemOut(BaseModel):
    attempt_id: UUID
    kind: str
    blueprint_id: UUID | None
    started_at: datetime
    submitted_at: datetime | None
    score: float
    max_total: float
    correct: int = 0
    questions: int = 0

    @classmethod
    def of(cls, a: MockAttempt) -> "HistoryItemOut":
        return cls(
            attempt_id=a.id,
            kind=a.kind,
            blueprint_id=a.blueprint_id,
            started_at=a.started_at,
            submitted_at=a.submitted_at,
            score=a.score or 0.0,
            max_total=float((a.result or {}).get("max_total", 0.0)),
            correct=int((a.result or {}).get("correct", 0)),
            questions=int((a.result or {}).get("questions", 0)),
        )


class PredictionOut(BaseModel):
    value: float
    low: float
    high: float
    attempts: int
    confident: bool = Field(description="False until enough attempts exist for a trustworthy band")

    @classmethod
    def of(cls, p: Prediction) -> "PredictionOut":
        return cls(
            value=p.value, low=p.low, high=p.high, attempts=p.attempts, confident=p.confident
        )


class PredictionViewOut(BaseModel):
    prediction: PredictionOut | None
    comparison: ComparisonOut | None

    @classmethod
    def of(cls, v: PredictionView) -> "PredictionViewOut":
        return cls(
            prediction=PredictionOut.of(v.prediction) if v.prediction else None,
            comparison=ComparisonOut.of(v.comparison) if v.comparison else None,
        )


class StartIn(BaseModel):
    blueprint_id: UUID
    language: str = Field(min_length=2, max_length=10, description="Content language (uz, ru, en)")


class PersonalStartIn(BaseModel):
    subject_id: UUID
    language: str = Field(min_length=2, max_length=10)
    count: int = Field(default=30, ge=5, le=90)


class SaveIn(BaseModel):
    answers: dict[UUID, dict[str, Any]] | None = Field(
        default=None, max_length=200, description="question_id -> response; empty clears"
    )
    flags: list[UUID] | None = Field(
        default=None,
        max_length=200,
        description="Marked-for-review question ids (replaces the set)",
    )

    @field_validator("answers")
    @classmethod
    def _cap_answers(
        cls, v: dict[UUID, dict[str, Any]] | None
    ) -> dict[UUID, dict[str, Any]] | None:
        for resp in (v or {}).values():
            check_response_size(resp)
        return v


@router.get(
    "/mocks", response_model=list[MockOut], responses=ERR, operation_id="assessment_list_mocks"
)
async def list_mocks(user: CurrentUser, svc: AssessmentServiceDep) -> list[MockOut]:
    return [MockOut.of(b) for b in await svc.list_mocks()]


@router.post("/attempts", response_model=AttemptOut, responses=ERR, operation_id="assessment_start")
async def start(body: StartIn, user: CurrentUser, svc: AssessmentServiceDep) -> AttemptOut:
    return AttemptOut.of(await svc.start(user.user_id, body.blueprint_id, body.language))


@router.post(
    "/attempts/personal",
    response_model=AttemptOut,
    responses=ERR,
    operation_id="assessment_start_personal",
)
async def start_personal(
    body: PersonalStartIn, user: CurrentUser, svc: AssessmentServiceDep
) -> AttemptOut:
    return AttemptOut.of(
        await svc.start_personal(user.user_id, body.subject_id, body.language, body.count)
    )


@router.get(
    "/attempts/active",
    response_model=AttemptOut | None,
    responses=ERR,
    operation_id="assessment_active",
)
async def active(user: CurrentUser, svc: AssessmentServiceDep) -> AttemptOut | None:
    v = await svc.active(user.user_id)
    return AttemptOut.of(v) if v else None


@router.get(
    "/attempts/history",
    response_model=list[HistoryItemOut],
    responses=ERR,
    operation_id="assessment_history",
)
async def history(
    user: CurrentUser, svc: AssessmentServiceDep, limit: int = Query(20, ge=1, le=100)
) -> list[HistoryItemOut]:
    return [HistoryItemOut.of(a) for a in await svc.history(user.user_id, limit)]


@router.get(
    "/prediction",
    response_model=PredictionViewOut,
    responses=ERR,
    operation_id="assessment_prediction",
)
async def prediction(user: CurrentUser, svc: AssessmentServiceDep) -> PredictionViewOut:
    return PredictionViewOut.of(await svc.prediction(user.user_id))


@router.get(
    "/attempts/{attempt_id}",
    response_model=AttemptOut,
    responses=ERR,
    operation_id="assessment_get_attempt",
)
async def get_attempt(attempt_id: UUID, user: CurrentUser, svc: AssessmentServiceDep) -> AttemptOut:
    return AttemptOut.of(await svc.get(user.user_id, attempt_id))


@router.patch(
    "/attempts/{attempt_id}",
    response_model=AttemptOut,
    responses=ERR,
    operation_id="assessment_save",
)
async def save(
    attempt_id: UUID, body: SaveIn, user: CurrentUser, svc: AssessmentServiceDep
) -> AttemptOut:
    answers = {str(k): v for k, v in body.answers.items()} if body.answers is not None else None
    flags = [str(f) for f in body.flags] if body.flags is not None else None
    return AttemptOut.of(await svc.save(user.user_id, attempt_id, answers, flags))


@router.post(
    "/attempts/{attempt_id}/submit",
    response_model=ResultOut,
    responses=ERR,
    operation_id="assessment_submit",
)
async def submit(
    attempt_id: UUID,
    user: CurrentUser,
    svc: AssessmentServiceDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ResultOut:
    out = ResultOut.of(await svc.submit(user.user_id, attempt_id))
    await commit_and_dispatch(session)
    return out


@router.get(
    "/attempts/{attempt_id}/result",
    response_model=ResultOut,
    responses=ERR,
    operation_id="assessment_result",
)
async def result(attempt_id: UUID, user: CurrentUser, svc: AssessmentServiceDep) -> ResultOut:
    return ResultOut.of(await svc.result(user.user_id, attempt_id))
