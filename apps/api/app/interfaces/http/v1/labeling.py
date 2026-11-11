from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.domain.models import User
from app.modules.identity.wiring import IdentityServiceDep
from app.modules.labeling.application.review import Filters, Review
from app.modules.labeling.infrastructure.config import get_labeling_settings
from app.modules.labeling.infrastructure.orm import GenerationRunRow
from app.modules.labeling.wiring import ActivityDep, GenerationDep, ReviewDep
from app.shared.audit import audit_admin
from app.shared.db import get_session
from app.shared.deps import require_role
from app.shared.errors import NotFound, ProblemDetails
from app.shared.security import Principal

router = APIRouter(tags=["labeling"])
admin_router = APIRouter(tags=["labeling-admin"])

ERR: dict[int | str, dict[str, Any]] = {
    401: {"model": ProblemDetails, "description": "Unauthorized"},
    403: {"model": ProblemDetails, "description": "Forbidden"},
    404: {"model": ProblemDetails, "description": "Not found"},
    409: {"model": ProblemDetails, "description": "Conflict"},
    422: {"model": ProblemDetails, "description": "Validation failed"},
}
SessionDep = Annotated[AsyncSession, Depends(get_session)]
Labeler = Annotated[Principal, Depends(require_role("editor", "labeler", "admin"))]
Admin = Annotated[Principal, Depends(require_role("admin"))]


class QueueFilters(BaseModel):
    subject_id: UUID | None = None
    language: str | None = None
    type_id: UUID | None = None
    topic_id: UUID | None = None
    state: Literal["auto_agreed", "escalated", "needs_human"] | None = None

    def to_domain(self) -> Filters:
        return Filters(self.subject_id, self.language, self.type_id, self.topic_id, self.state)


def filters(
    subject_id: UUID | None = None, language: str | None = None, type_id: UUID | None = None,
    topic_id: UUID | None = None, state: Literal["auto_agreed", "escalated", "needs_human"] | None = None,
) -> Filters:
    return Filters(subject_id, language, type_id, topic_id, state)


FiltersDep = Annotated[Filters, Depends(filters)]


class QueueItemOut(BaseModel):
    question_id: UUID
    state: str
    reason: str
    confidence: float
    subject_id: UUID
    topic_id: UUID | None
    type_id: UUID | None
    language: str


class QueuePage(BaseModel):
    total: int
    items: list[QueueItemOut]


class ReviewQuestionOut(BaseModel):
    id: UUID
    kind: str
    language: str
    stem: str
    media: list[Any]
    payload: dict[str, Any]
    passage_id: UUID | None
    status: str


class VoteOut(BaseModel):
    model: str
    answer: dict[str, Any] | None
    confidence: float


class ReviewOut(BaseModel):
    question: ReviewQuestionOut
    state: str
    reason: str
    suggested: dict[str, Any] | None = Field(description="Null for blind audit items")
    confidence: float | None
    audit_sample_id: UUID | None
    votes: list[VoteOut] = Field(default_factory=list, description="Solver votes; empty for blind audit items")


class DecideIn(BaseModel):
    action: Literal["accept", "edit", "skip", "flag"]
    response: dict[str, Any] | None = None
    time_ms: int = Field(0, ge=0)
    reason: str | None = Field(None, max_length=200)
    audit_sample_id: UUID | None = None


class DecisionOut(BaseModel):
    id: UUID
    question_id: UUID
    action: str
    new_status: str | None
    undone: bool


class AgreementOut(BaseModel):
    audited: int
    matched: int
    rate: float | None


class LabelingStatsOut(BaseModel):
    queue_depth: dict[str, int]
    audit: AgreementOut
    per_labeler: list[dict[str, Any]]


class BulkIn(QueueFilters):
    min_confidence: float = Field(0.9, ge=0, le=1)
    limit: int = Field(200, ge=1, le=2000)
    dry_run: bool = False


class BulkOut(BaseModel):
    approved: int
    failed: int
    audit: AgreementOut


class AuditSampleIn(QueueFilters):
    size: int = Field(50, ge=1, le=1000)


class AuditSampleOut(BaseModel):
    batch_id: UUID
    sampled: int


class GenerationIn(BaseModel):
    subject_id: UUID
    topic_id: UUID
    type_id: UUID
    language: str = Field(max_length=10)
    count: int = Field(ge=1, le=200)
    difficulty: float | None = None
    prompt_template: str | None = None


class GenerationOut(BaseModel):
    id: UUID
    subject_id: UUID
    topic_id: UUID | None
    type_id: UUID
    kind: str
    language: str
    requested: int
    status: str
    created_count: int
    failed_count: int
    error: str | None


class SolveIn(BaseModel):
    question_ids: list[UUID] = Field(min_length=1, max_length=500)


class SolveQueuedOut(BaseModel):
    queued: int


def _agreement(a: Any) -> AgreementOut:
    return AgreementOut(audited=a.audited, matched=a.matched, rate=a.rate)


def _review(r: Review) -> ReviewOut:
    q = r.question
    return ReviewOut(
        question=ReviewQuestionOut(
            id=q.id, kind=q.kind, language=q.language, stem=q.stem, media=list(q.media), payload=q.payload,
            passage_id=q.passage_id, status=q.status,
        ),
        state=r.state, reason=r.reason, suggested=r.suggested, confidence=r.confidence,
        audit_sample_id=r.audit_sample_id,
        votes=[VoteOut(model=v.model, answer=v.answer, confidence=v.confidence) for v in r.votes],
    )


def _run(r: GenerationRunRow) -> GenerationOut:
    return GenerationOut(
        id=r.id, subject_id=r.subject_id, topic_id=r.topic_id, type_id=r.type_id, kind=r.kind, language=r.language,
        requested=r.requested, status=r.status, created_count=r.created_count, failed_count=r.failed_count,
        error=r.error,
    )


# ---- cockpit (editor|admin) -------------------------------------------------------------------
@router.get("/queue", operation_id="labeling_list_queue", response_model=QueuePage, responses=ERR)
async def list_queue(
    svc: ReviewDep, _: Labeler, f: FiltersDep, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)
) -> QueuePage:
    total, rows = await svc.list_queue(f, limit, offset)
    return QueuePage(
        total=total,
        items=[
            QueueItemOut(
                question_id=r.question_id, state=r.state, reason=r.reason, confidence=r.confidence,
                subject_id=r.subject_id, topic_id=r.topic_id, type_id=r.type_id, language=r.language,
            )
            for r in rows
        ],
    )


@router.post("/queue/next", operation_id="labeling_next_item", response_model=ReviewOut, responses=ERR)
async def next_item(svc: ReviewDep, who: Labeler, f: FiltersDep) -> ReviewOut:
    return _review(await svc.next_for(who.user_id, f))


@router.get("/queue/{question_id}", operation_id="labeling_get_item", response_model=ReviewOut, responses=ERR)
async def get_item(question_id: UUID, svc: ReviewDep, _: Labeler) -> ReviewOut:
    return _review(await svc.get_review(question_id))


@router.post(
    "/queue/{question_id}/decide", operation_id="labeling_decide", response_model=DecisionOut, responses=ERR
)
async def decide(question_id: UUID, body: DecideIn, svc: ReviewDep, who: Labeler) -> DecisionOut:
    d = await svc.decide(
        who.user_id, question_id, action=body.action, response=body.response, time_ms=body.time_ms,
        reason=body.reason, audit_sample_id=body.audit_sample_id,
    )
    return DecisionOut(id=d.id, question_id=d.question_id, action=d.action, new_status=d.new_status, undone=False)


@router.post("/decisions/{decision_id}/undo", operation_id="labeling_undo", response_model=DecisionOut, responses=ERR)
async def undo(decision_id: UUID, svc: ReviewDep, who: Labeler) -> DecisionOut:
    d = await svc.undo(who.user_id, "admin" in who.roles, decision_id)
    return DecisionOut(
        id=d.id, question_id=d.question_id, action=d.action, new_status=d.prev_status, undone=d.undone_at is not None
    )


@router.get("/stats", operation_id="labeling_stats", response_model=LabelingStatsOut, responses=ERR)
async def stats(svc: ReviewDep, _: Labeler, days: int = Query(7, ge=1, le=90)) -> LabelingStatsOut:
    s = await svc.stats(days)
    per: dict[tuple[Any, str], dict[str, Any]] = {}
    for labeler, action, n, avg_ms in s["per_labeler"]:
        per.setdefault((labeler, ""), {"labeler_id": labeler, "actions": {}, "avg_ms": {}})
        per[(labeler, "")]["actions"][action] = n
        per[(labeler, "")]["avg_ms"][action] = float(avg_ms or 0)
    return LabelingStatsOut(queue_depth=s["queue_depth"], audit=_agreement(s["audit"]), per_labeler=list(per.values()))


# ---- admin ------------------------------------------------------------------------------------
@admin_router.post("/bulk-approve", operation_id="labeling_bulk_approve", response_model=BulkOut, responses=ERR)
async def bulk_approve(body: BulkIn, svc: ReviewDep, who: Admin) -> BulkOut:
    ok, failed, stat = await svc.bulk_approve(
        who.user_id, body.to_domain(), min_confidence=body.min_confidence, limit=body.limit,
        min_agreement=get_labeling_settings().labeling_bulk_min_agreement, dry_run=body.dry_run,
    )
    return BulkOut(approved=ok, failed=failed, audit=_agreement(stat))


@admin_router.post("/audit/sample", operation_id="labeling_audit_sample", response_model=AuditSampleOut, responses=ERR)
async def audit_sample(body: AuditSampleIn, svc: ReviewDep, _: Admin) -> AuditSampleOut:
    batch_id, n = await svc.sample_audit(body.size, body.to_domain())
    return AuditSampleOut(batch_id=batch_id, sampled=n)


@admin_router.get("/audit/agreement", operation_id="labeling_audit_agreement", response_model=AgreementOut, responses=ERR)
async def audit_agreement(svc: ReviewDep, _: Admin, f: FiltersDep) -> AgreementOut:
    return _agreement(await svc.agreement(f))


@admin_router.post("/generation-runs", operation_id="labeling_create_generation", response_model=GenerationOut,
                   status_code=202, responses=ERR)
async def create_generation(body: GenerationIn, svc: GenerationDep, session: SessionDep, who: Admin) -> GenerationOut:
    from app.modules.labeling.tasks import run_generation

    run = await svc.create_run(
        subject_id=body.subject_id, topic_id=body.topic_id, type_id=body.type_id, language=body.language,
        count=body.count, difficulty=body.difficulty, prompt_template=body.prompt_template, created_by=who.user_id,
    )
    await session.commit()  # the worker must see the row
    await run_generation.kiq(str(run.id))
    return _run(run)


@admin_router.get("/generation-runs", operation_id="labeling_list_generation", response_model=list[GenerationOut],
                  responses=ERR)
async def list_generation(session: SessionDep, _: Admin, limit: int = Query(50, ge=1, le=200)) -> list[GenerationOut]:
    rows = (
        await session.execute(select(GenerationRunRow).order_by(GenerationRunRow.created_at.desc()).limit(limit))
    ).scalars()
    return [_run(r) for r in rows]


@admin_router.get("/generation-runs/{run_id}", operation_id="labeling_get_generation", response_model=GenerationOut,
                  responses=ERR)
async def get_generation(run_id: UUID, session: SessionDep, _: Admin) -> GenerationOut:
    r = await session.get(GenerationRunRow, run_id)
    if r is None:
        raise NotFound("Generation run not found")
    return _run(r)


@admin_router.post("/solve", operation_id="labeling_enqueue_solve", response_model=SolveQueuedOut, status_code=202,
                   responses=ERR)
async def enqueue_solve(body: SolveIn, _: Admin) -> SolveQueuedOut:
    from app.modules.labeling.tasks import solve_questions

    await solve_questions.kiq([str(q) for q in body.question_ids], "manual")
    return SolveQueuedOut(queued=len(body.question_ids))


class ActivityOut(BaseModel):
    id: UUID
    actor_id: UUID
    actor_name: str | None
    action: str
    question_id: UUID | None
    payload: dict[str, Any]
    duration_ms: int | None
    created_at: datetime


class ActivityPage(BaseModel):
    total: int
    items: list[ActivityOut]


class LeaderboardRowOut(BaseModel):
    actor_id: UUID
    actor_name: str | None
    is_system: bool
    labeled: int
    approved: int
    rejected: int
    avg_duration_ms: float | None
    last_active_at: datetime | None


@admin_router.get("/activity", operation_id="labeling_admin_activity", response_model=ActivityPage, responses=ERR)
async def admin_activity(
    svc: ActivityDep, ids: IdentityServiceDep, who: Admin,
    actor_id: UUID | None = None,
    action: str | None = None,
    date_from: Annotated[datetime | None, Query(alias="from")] = None,
    date_to: Annotated[datetime | None, Query(alias="to")] = None,
    sort: Literal["created_at", "duration_ms", "action"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
) -> ActivityPage:
    total, rows = await svc.list_activity(
        actor_id=actor_id, action=action, start=date_from, end=date_to, sort=sort,
        descending=order == "desc", page=page, size=size,
    )
    names = await ids.get_many({r.actor_user_id for r in rows})
    audit_admin(who, "labeling.activity", actor_id=str(actor_id) if actor_id else None, action=action, page=page)
    return ActivityPage(
        total=total,
        items=[
            ActivityOut(
                id=r.id, actor_id=r.actor_user_id, actor_name=_name(names.get(r.actor_user_id)), action=r.action,
                question_id=r.question_id, payload=r.payload, duration_ms=r.duration_ms, created_at=r.created_at,
            )
            for r in rows
        ],
    )


@admin_router.get(
    "/leaderboard", operation_id="labeling_admin_leaderboard", response_model=list[LeaderboardRowOut], responses=ERR
)
async def admin_leaderboard(
    svc: ActivityDep, ids: IdentityServiceDep, who: Admin,
    date_from: Annotated[datetime | None, Query(alias="from")] = None,
    date_to: Annotated[datetime | None, Query(alias="to")] = None,
    sort: Literal["labeled", "approved", "rejected", "avg_duration"] = "labeled",
    order: Literal["asc", "desc"] = "desc",
) -> list[LeaderboardRowOut]:
    entries = await svc.leaderboard(start=date_from, end=date_to, sort=sort, descending=order == "desc")
    users = await ids.get_many({e.actor_id for e in entries})
    audit_admin(who, "labeling.leaderboard", sort=sort)
    return [
        LeaderboardRowOut(
            actor_id=e.actor_id, actor_name=_name(users.get(e.actor_id)),
            is_system=bool(users.get(e.actor_id) and users[e.actor_id].is_system),
            labeled=e.labeled, approved=e.approved, rejected=e.rejected,
            avg_duration_ms=e.avg_duration_ms, last_active_at=e.last_active_at,
        )
        for e in entries
    ]


def _name(user: User | None) -> str | None:
    return None if user is None else user.name
