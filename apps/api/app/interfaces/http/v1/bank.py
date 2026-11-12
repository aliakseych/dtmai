from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.interfaces.http.v1._media import MediaOut, to_media
from app.modules.bank import facade as bank_facade
from app.modules.bank.application.service import BankService, CreateQuestionCmd, _cmd_from_dict
from app.modules.bank.domain.models import Passage, Question, QuestionFilter
from app.modules.bank.settings import get_bank_settings
from app.modules.bank.wiring import BankServiceDep
from app.modules.catalog import facade as catalog
from app.modules.catalog.wiring import CatalogServiceDep
from app.modules.learning import facade as learning
from app.shared.audit import audit_admin
from app.shared.db import get_session
from app.shared.deps import CurrentUser, require_role
from app.shared.errors import NotFound, ProblemDetails
from app.shared.security import Principal

ERR: dict[int | str, dict[str, Any]] = {
    401: {"model": ProblemDetails},
    403: {"model": ProblemDetails},
    404: {"model": ProblemDetails},
    409: {"model": ProblemDetails},
    422: {"model": ProblemDetails},
}
Status = Literal[
    "draft", "auto_agreed", "escalated", "needs_human", "verified", "hidden", "retired"
]

router = APIRouter(tags=["bank"])
# Every admin route requires the admin role (router-level dependency).
admin_router = APIRouter(tags=["bank-admin"], dependencies=[Depends(require_role("admin"))])
AdminUser = Annotated[Principal, Depends(require_role("admin"))]


# ---- schemas -----------------------------------------------------------------------------
class ReportIn(BaseModel):
    reason: str = Field(default="", max_length=500)


class ReportOut(BaseModel):
    hidden: bool


class QuestionBody(BaseModel):
    subject_id: UUID
    topic_id: UUID
    type_id: UUID
    kind: str
    language: str
    stem: str
    payload: dict[str, Any] = Field(default_factory=dict)
    answer: dict[str, Any] = Field(default_factory=dict)
    difficulty: float = 1000.0
    media: list[Any] = Field(default_factory=list)
    passage_id: UUID | None = None
    source_id: UUID | None = None
    source_ref: dict[str, Any] | None = None
    status: Status = "draft"
    answer_official: bool = False
    translation_group_id: UUID | None = None
    children: list["QuestionBody"] = Field(default_factory=list)


class QuestionPatch(BaseModel):
    stem: str | None = None
    payload: dict[str, Any] | None = None
    answer: dict[str, Any] | None = None
    topic_id: UUID | None = None
    type_id: UUID | None = None
    difficulty: float | None = None
    media: list[Any] | None = None
    passage_id: UUID | None = None
    source_id: UUID | None = None
    source_ref: dict[str, Any] | None = None
    translation_group_id: UUID | None = None
    language: str | None = None


class QuestionAdminOut(BaseModel):
    id: UUID
    subject_id: UUID
    topic_id: UUID
    type_id: UUID
    kind: str
    language: str
    stem: str
    media: list[Any]
    payload: dict[str, Any]
    answer: dict[str, Any]
    answer_official: bool
    difficulty: float
    passage_id: UUID | None
    parent_id: UUID | None
    source_id: UUID | None
    source_ref: dict[str, Any] | None
    translation_group_id: UUID | None
    status: Status
    attempts: int
    correct_rate: float | None
    report_count: int


class QuestionPage(BaseModel):
    items: list[QuestionAdminOut]
    total: int


class StatusIn(BaseModel):
    status: Status
    reason: str = Field(default="", max_length=500)


class BulkStatusIn(StatusIn):
    ids: list[UUID] = Field(min_length=1, max_length=1000)


class BulkStatusOut(BaseModel):
    updated: int


class ImportIn(BaseModel):
    items: list[dict[str, Any]] = Field(min_length=1, max_length=2000)


class ImportError_(BaseModel):
    index: int
    error: str


class ImportOut(BaseModel):
    created: list[UUID]
    errors: list[ImportError_]


class CreatedOut(BaseModel):
    id: UUID


class ExplanationIn(BaseModel):
    text: str = Field(min_length=1)
    model: str = ""


class ExplanationOut(BaseModel):
    locale: str
    text: str | None


class CoverageRow(BaseModel):
    subject_id: UUID
    topic_id: UUID
    type_id: UUID
    language: str
    verified: int
    min_pool: int
    ok: bool


class PassageIn(BaseModel):
    language: str
    text: str = Field(min_length=1)
    title: str | None = None
    media: list[Any] = Field(default_factory=list)
    source_id: UUID | None = None


class PassagePatch(BaseModel):
    language: str | None = None
    text: str | None = None
    title: str | None = None
    media: list[Any] | None = None
    source_id: UUID | None = None


class PassageOut(BaseModel):
    id: UUID
    language: str
    title: str | None
    text: str
    media: list[Any]
    source_id: UUID | None


def _out(q: Question) -> QuestionAdminOut:
    return QuestionAdminOut(
        id=q.id,
        subject_id=q.subject_id,
        topic_id=q.topic_id,
        type_id=q.type_id,
        kind=q.kind,
        language=q.language,
        stem=q.stem,
        media=q.media,
        payload=q.payload,
        answer=q.answer,
        answer_official=q.answer_official,
        difficulty=q.difficulty,
        passage_id=q.passage_id,
        parent_id=q.parent_id,
        source_id=q.source_id,
        source_ref=q.source_ref,
        translation_group_id=q.translation_group_id,
        status=q.status,  # type: ignore[arg-type]
        attempts=q.attempts,
        correct_rate=q.correct_rate,
        report_count=q.report_count,
    )


def _passage(p: Passage) -> PassageOut:
    return PassageOut(
        id=p.id,
        language=p.language,
        title=p.title,
        text=p.text,
        media=p.media,
        source_id=p.source_id,
    )


def _cmd(body: QuestionBody, actor: str) -> CreateQuestionCmd:
    return _cmd_from_dict(body.model_dump(mode="json"), actor)


# ---- learner -----------------------------------------------------------------------------
Level = Literal["easy", "medium", "hard"]


class BankBaseOut(BaseModel):
    id: UUID
    code: str
    names: dict[str, str]
    kind: str
    year: int | None
    total: int
    solved: int


class BankTypeOut(BaseModel):
    """One (topic, question type) cell. total/solved honour the level filter; easy/medium/hard
    are the cell's totals per level (source filter applied, level filter not)."""

    topic_id: UUID
    type_id: UUID
    type_names: dict[str, str]
    kind: str
    total: int
    solved: int
    easy: int
    medium: int
    hard: int


class BankOverviewOut(BaseModel):
    total: int
    solved: int
    easy: int
    medium: int
    hard: int
    bases: list[BankBaseOut]
    types: list[BankTypeOut]


def build_overview(
    rows: list[bank_facade.FacetRow],
    *,
    bases: list[dict[str, Any]],
    types: dict[UUID, Any],
    source_id: UUID | None,
    level: str | None,
) -> BankOverviewOut:
    """Aggregate facet rows. Bases list ignores both filters (it is the filter itself); only
    active bases that actually hold verified questions are offered."""
    per_base: dict[UUID, list[int]] = {}
    for r in rows:
        if r.source_id is not None:
            t = per_base.setdefault(r.source_id, [0, 0])
            t[0] += r.total
            t[1] += r.solved
    base_out = [
        BankBaseOut(
            id=b["id"],
            code=b["code"],
            names=b["names"],
            kind=b["kind"],
            year=b.get("year"),
            total=per_base[b["id"]][0],
            solved=per_base[b["id"]][1],
        )
        for b in sorted(bases, key=lambda x: (x.get("position", 0), x["code"]))
        if b["active"] and per_base.get(b["id"], [0])[0] > 0
    ]
    cells: dict[tuple[UUID, UUID], dict[str, int]] = {}
    for r in rows:
        if source_id is not None and r.source_id != source_id:
            continue
        c = cells.setdefault(
            (r.topic_id, r.type_id),
            {"total": 0, "solved": 0, "easy": 0, "medium": 0, "hard": 0},
        )
        c[r.level] += r.total
        if level is None or level == r.level:
            c["total"] += r.total
            c["solved"] += r.solved
    out = [
        BankTypeOut(
            topic_id=tid,
            type_id=ty,
            type_names=types[ty].names,
            kind=types[ty].kind,
            **c,
        )
        for (tid, ty), c in cells.items()
        if ty in types and c["total"] > 0
    ]
    return BankOverviewOut(
        total=sum(c.total for c in out),
        solved=sum(c.solved for c in out),
        easy=sum(c.easy for c in out),
        medium=sum(c.medium for c in out),
        hard=sum(c.hard for c in out),
        bases=base_out,
        types=out,
    )


@router.get("/overview", operation_id="bank_overview", responses=ERR)
async def overview(
    subject_id: UUID,
    language: str,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    cat: CatalogServiceDep,
    source_id: UUID | None = None,
    level: Level | None = None,
) -> BankOverviewOut:
    """Learner question bank of one subject: verified questions per topic/question type with the
    caller's solved counts, filterable by question base and difficulty level."""
    if source_id is not None:
        await catalog.require_learner_base(session, source_id)
    solved = await learning.solved_question_ids(session, user.user_id)
    rows = await bank_facade.facets(session, subject_id, language, solved)
    types = {t.id: t for t in await catalog.list_question_types(session)}
    return build_overview(
        rows,
        bases=[b for b in await cat.repo.list("question_base") if not b["archived"]],
        types=types,
        source_id=source_id,
        level=level,
    )


class PublicPassageOut(BaseModel):
    id: UUID
    text: str
    media: list[MediaOut]


@router.get(
    "/passages/{passage_id}",
    operation_id="bank_get_passage",
    response_model=PublicPassageOut,
    responses=ERR,
)
async def get_public_passage(passage_id: UUID, svc: BankServiceDep) -> PublicPassageOut:
    """Reading passage shared by items of a session (public: ids are unguessable UUIDs)."""
    p = await svc.repo.get_passage(passage_id)
    if p is None:
        raise NotFound("passage not found", code="passage_not_found")
    return PublicPassageOut(id=p.id, text=p.text, media=to_media(p.media))


@router.post("/questions/{question_id}/report", operation_id="bank_report_question", responses=ERR)
async def report_question(
    question_id: UUID, body: ReportIn, user: CurrentUser, svc: BankServiceDep
) -> ReportOut:
    return ReportOut(
        hidden=await svc.report(
            question_id, user.user_id, body.reason, is_guest="guest" in user.roles
        )
    )


# ---- admin -------------------------------------------------------------------------------
@admin_router.get("/questions", operation_id="bank_admin_list_questions", responses=ERR)
async def list_questions(
    svc: BankServiceDep,
    subject_id: UUID | None = None,
    topic_id: UUID | None = None,
    type_id: UUID | None = None,
    language: str | None = None,
    status: Status | None = None,
    source_id: UUID | None = None,
    kind: str | None = None,
    q: str | None = Query(default=None, max_length=200),
    reported: bool = False,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> QuestionPage:
    f = QuestionFilter(
        subject_id, topic_id, type_id, language, status, source_id, kind, q, reported
    )
    items, total = await svc.search(f, limit, offset)
    return QuestionPage(items=[_out(i) for i in items], total=total)


@admin_router.post(
    "/questions", status_code=201, operation_id="bank_admin_create_question", responses=ERR
)
async def create_question(body: QuestionBody, admin: AdminUser, svc: BankServiceDep) -> CreatedOut:
    return CreatedOut(id=await svc.create(_cmd(body, str(admin.user_id))))


@admin_router.post("/questions/import", operation_id="bank_admin_import_questions", responses=ERR)
async def import_questions(body: ImportIn, admin: AdminUser, svc: BankServiceDep) -> ImportOut:
    res = await svc.import_items(body.items, admin.user_id)
    return ImportOut(
        created=res.created, errors=[ImportError_(index=i, error=e) for i, e in res.errors]
    )


@admin_router.post("/questions/bulk-status", operation_id="bank_admin_bulk_status", responses=ERR)
async def bulk_status(body: BulkStatusIn, admin: AdminUser, svc: BankServiceDep) -> BulkStatusOut:
    n = await svc.bulk_set_status(body.ids, body.status, admin.user_id, body.reason)
    return BulkStatusOut(updated=n)


@admin_router.get("/questions/{question_id}", operation_id="bank_admin_get_question", responses=ERR)
async def get_question(question_id: UUID, svc: BankServiceDep) -> QuestionAdminOut:
    return _out(await svc.require(question_id))


@admin_router.patch(
    "/questions/{question_id}", operation_id="bank_admin_update_question", responses=ERR
)
async def update_question(
    question_id: UUID, body: QuestionPatch, admin: AdminUser, svc: BankServiceDep
) -> QuestionAdminOut:
    patch = {k: getattr(body, k) for k in body.model_fields_set}
    return _out(await svc.update(question_id, patch, admin.user_id))


@admin_router.post(
    "/questions/{question_id}/status",
    status_code=204,
    operation_id="bank_admin_set_status",
    responses=ERR,
)
async def set_status(
    question_id: UUID, body: StatusIn, admin: AdminUser, svc: BankServiceDep
) -> Response:
    await svc.set_status(question_id, body.status, admin.user_id, body.reason)
    return Response(status_code=204)


@admin_router.get(
    "/questions/{question_id}/explanations/{locale}",
    operation_id="bank_admin_get_explanation",
    responses=ERR,
)
async def get_explanation(question_id: UUID, locale: str, svc: BankServiceDep) -> ExplanationOut:
    await svc.require(question_id)
    return ExplanationOut(locale=locale, text=await svc.get_explanation(question_id, locale))


@admin_router.put(
    "/questions/{question_id}/explanations/{locale}",
    status_code=204,
    operation_id="bank_admin_put_explanation",
    responses=ERR,
)
async def put_explanation(
    question_id: UUID, locale: str, body: ExplanationIn, svc: BankServiceDep
) -> Response:
    await svc.upsert_explanation(question_id, locale, body.text, body.model or "human")
    return Response(status_code=204)


@admin_router.get("/coverage", operation_id="bank_admin_coverage", responses=ERR)
async def coverage(
    svc: BankServiceDep, subject_id: UUID | None = None, language: str | None = None
) -> list[CoverageRow]:
    """Verified pool per subject/topic/type/language versus CONTENT_MIN_POOL (content launch gate)."""
    min_pool = get_bank_settings().content_min_pool
    rows = await svc.coverage(subject_id, language)
    return [
        CoverageRow(
            subject_id=s,
            topic_id=t,
            type_id=ty,
            language=lang,
            verified=n,
            min_pool=min_pool,
            ok=n >= min_pool,
        )
        for s, t, ty, lang, n in rows
    ]


@admin_router.get("/passages", operation_id="bank_admin_list_passages", responses=ERR)
async def list_passages(
    svc: BankServiceDep,
    language: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[PassageOut]:
    return [_passage(p) for p in await svc.repo.list_passages(language, limit, offset)]


@admin_router.post(
    "/passages", status_code=201, operation_id="bank_admin_create_passage", responses=ERR
)
async def create_passage(body: PassageIn, svc: BankServiceDep) -> CreatedOut:
    pid = await svc.create_passage(
        language=body.language,
        text=body.text,
        title=body.title,
        media=body.media,
        source_id=body.source_id,
    )
    return CreatedOut(id=pid)


@admin_router.get("/passages/{passage_id}", operation_id="bank_admin_get_passage", responses=ERR)
async def get_passage(passage_id: UUID, svc: BankServiceDep) -> PassageOut:
    p = await svc.repo.get_passage(passage_id)
    if p is None:
        raise NotFound("passage not found", code="passage_not_found")
    return _passage(p)


@admin_router.patch(
    "/passages/{passage_id}", operation_id="bank_admin_update_passage", responses=ERR
)
async def update_passage(
    passage_id: UUID, body: PassagePatch, svc: BankServiceDep, who: AdminUser
) -> PassageOut:
    patch = {k: getattr(body, k) for k in body.model_fields_set}
    out = _passage(await svc.update_passage(passage_id, patch))
    audit_admin(who, "bank.passage.update", passage_id=str(passage_id), fields=sorted(patch))
    return out


__all__ = ["BankService", "admin_router", "router"]
