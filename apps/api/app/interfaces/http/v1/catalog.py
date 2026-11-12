from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.bank import facade as bank
from app.modules.catalog import facade
from app.modules.catalog.domain import models as dom
from app.modules.catalog.domain.progress import derive_path_progress
from app.modules.catalog.wiring import CatalogServiceDep
from app.modules.learning import facade as learning
from app.shared.db import get_session
from app.shared.deps import OptionalUser, require_role
from app.shared.errors import NotFound, ProblemDetails
from app.shared.security import Principal

ERR: dict[int | str, dict[str, Any]] = {
    401: {"model": ProblemDetails},
    403: {"model": ProblemDetails},
    404: {"model": ProblemDetails},
    409: {"model": ProblemDetails},
    422: {"model": ProblemDetails},
}
Names = dict[str, str]

router = APIRouter(tags=["catalog"])
# Every admin route requires the admin role (router-level dependency).
admin_router = APIRouter(
    tags=["catalog-admin"], dependencies=[Depends(require_role("admin"))], responses=ERR
)
AdminUser = Annotated[Principal, Depends(require_role("admin"))]
Session = Annotated[AsyncSession, Depends(get_session)]


# ---- output models ------------------------------------------------------------------------
class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SubjectOut(_Out):
    id: UUID
    code: str
    names: Names
    weight: float
    active: bool
    position: int
    question_count: int = Field(
        default=0,
        description="Verified, learner-servable questions (in the requested language); 0 = no content yet (learner list only)",
    )


class ReferenceSheetOut(_Out):
    """Learner view: one locale, already resolved with fallback."""

    subject_id: UUID
    locale: str
    content: str = Field(description="Markdown with $…$ / $$…$$ KaTeX")
    source: str
    updated_at: datetime


class ReferenceSheetAdminOut(_Out):
    id: UUID
    subject_id: UUID
    contents: Names
    source: str
    active: bool
    updated_at: datetime


class ReferenceSheetIn(BaseModel):
    contents: Names
    source: str = ""
    active: bool = True


class TopicOut(_Out):
    id: UUID
    subject_id: UUID
    parent_id: UUID | None
    code: str | None
    names: Names
    position: int
    active: bool


class QuestionTypeOut(_Out):
    id: UUID
    code: str
    kind: str
    names: Names
    config: dict[str, Any]
    generation_prompt: str = ""
    rules: dict[str, Any] = {}
    active: bool = True
    position: int = 0


class PathOut(_Out):
    id: UUID
    subject_id: UUID
    language: str
    names: Names
    status: str
    position: int


class UnitOut(_Out):
    id: UUID
    path_id: UUID
    names: Names
    position: int


class TheoryCard(_Out):
    title: str = Field(min_length=1)
    body_md: str
    example_md: str | None = None


class LessonOut(_Out):
    id: UUID
    unit_id: UUID
    names: Names
    topic_ids: list[UUID]
    type_ids: list[UUID]
    question_count: int
    legendary: bool
    theory: list[TheoryCard]
    position: int


class BlueprintOut(_Out):
    id: UUID
    code: str
    version: int
    names: Names
    kind: str
    sections: list[dict[str, Any]]
    duration_min: int
    status: str
    source_id: UUID | None


class QuestionBaseOut(_Out):
    id: UUID
    code: str
    names: Names
    kind: str
    year: int | None
    provenance: str
    license_note: str
    active: bool
    archived: bool
    position: int


class ProgressOut(_Out):
    completed_lessons: int
    total_lessons: int
    state: Literal["locked", "open", "done"]


class LearnerLessonOut(_Out):
    id: UUID
    progress: ProgressOut
    title: str
    names: Names
    topic_ids: list[UUID]
    type_ids: list[UUID]
    question_count: int
    legendary: bool
    pool: int
    theory: list[TheoryCard]
    has_theory: bool


class LearnerUnitOut(_Out):
    id: UUID
    progress: ProgressOut
    title: str
    names: Names
    lessons: list[LearnerLessonOut]


class LearnerPathOut(_Out):
    id: UUID
    subject_id: UUID
    language: str
    names: Names
    units: list[LearnerUnitOut]


class AuditOut(_Out):
    id: int
    actor: str | None
    action: str
    entity: str
    entity_id: UUID | None
    before: dict[str, Any] | None
    after: dict[str, Any] | None


class LaunchGateRow(_Out):
    lesson_id: UUID
    path_id: UUID
    subject_id: UUID
    language: str
    title: str
    pool: int
    needed: int
    visible: bool


class ReorderIn(BaseModel):
    ids: list[UUID]


# ---- input models -------------------------------------------------------------------------
class SubjectIn(BaseModel):
    code: str
    names: Names
    weight: float = 1.0
    active: bool = True
    position: int | None = None


class SubjectPatch(BaseModel):
    names: Names | None = None
    weight: float | None = None
    active: bool | None = None
    position: int | None = None
    code: str | None = None


class TopicIn(BaseModel):
    subject_id: UUID
    parent_id: UUID | None = None
    code: str | None = None
    names: Names
    position: int | None = None
    active: bool = True


class TopicPatch(BaseModel):
    parent_id: UUID | None = None
    code: str | None = None
    names: Names | None = None
    position: int | None = None
    active: bool | None = None


class QuestionTypeIn(BaseModel):
    code: str
    kind: Literal[
        "single_choice",
        "multi_choice",
        "numeric",
        "short_text",
        "matching",
        "ordering",
        "passage_group",
    ]
    names: Names
    config: dict[str, Any] = {}
    generation_prompt: str = ""
    rules: dict[str, Any] = {}
    active: bool = True
    position: int | None = None


class QuestionTypePatch(BaseModel):
    code: str | None = None
    kind: (
        Literal[
            "single_choice",
            "multi_choice",
            "numeric",
            "short_text",
            "matching",
            "ordering",
            "passage_group",
        ]
        | None
    ) = None
    names: Names | None = None
    config: dict[str, Any] | None = None
    generation_prompt: str | None = None
    rules: dict[str, Any] | None = None
    active: bool | None = None
    position: int | None = None


class PathIn(BaseModel):
    subject_id: UUID
    language: str
    names: Names
    position: int | None = None


class PathPatch(BaseModel):
    language: str | None = None
    names: Names | None = None
    position: int | None = None


class UnitIn(BaseModel):
    path_id: UUID
    names: Names
    position: int | None = None


class UnitPatch(BaseModel):
    names: Names | None = None
    position: int | None = None


class LessonIn(BaseModel):
    unit_id: UUID
    names: Names
    topic_ids: list[UUID] = []
    type_ids: list[UUID] = []
    question_count: int = Field(default=10, ge=1, le=30)
    legendary: bool = False
    theory: list[TheoryCard] = Field(default=[], max_length=12)
    position: int | None = None


class LessonPatch(BaseModel):
    names: Names | None = None
    topic_ids: list[UUID] | None = None
    type_ids: list[UUID] | None = None
    question_count: int | None = Field(default=None, ge=1, le=30)
    legendary: bool | None = None
    theory: list[TheoryCard] | None = Field(default=None, max_length=12)
    position: int | None = None


class BlueprintIn(BaseModel):
    code: str
    names: Names
    kind: Literal["official", "generated", "template"]
    sections: list[dict[str, Any]]
    duration_min: int
    source_id: UUID | None = None


class BlueprintPatch(BaseModel):
    names: Names | None = None
    kind: Literal["official", "generated", "template"] | None = None
    sections: list[dict[str, Any]] | None = None
    duration_min: int | None = None
    source_id: UUID | None = None


QKind = Literal["previous_year", "bluebook", "ai_generated", "harvested", "custom"]


class QuestionBaseIn(BaseModel):
    code: str
    names: Names
    kind: QKind
    year: int | None = None
    provenance: str = ""
    license_note: str = ""
    active: bool = True
    position: int | None = None


class QuestionBasePatch(BaseModel):
    code: str | None = None
    names: Names | None = None
    kind: QKind | None = None
    year: int | None = None
    provenance: str | None = None
    license_note: str | None = None
    active: bool | None = None
    position: int | None = None


def _dump(m: BaseModel, *, partial: bool = False) -> dict[str, Any]:
    d = m.model_dump(exclude_unset=partial, mode="python")
    return d


def _crud(
    entity: str, path: str, In: type[BaseModel], Patch: type[BaseModel], Out: type[BaseModel]
) -> None:
    """Register create/get/patch/delete for an entity under admin_router."""

    @admin_router.post(
        path, response_model=Out, status_code=201, operation_id=f"catalog_admin_create_{entity}"
    )
    async def create(body: In, svc: CatalogServiceDep, actor: AdminUser) -> Any:  # type: ignore[valid-type]
        return await svc.create(entity, _dump(body), str(actor.user_id))

    @admin_router.get(
        path + "/{item_id}", response_model=Out, operation_id=f"catalog_admin_get_{entity}"
    )
    async def get(item_id: UUID, svc: CatalogServiceDep) -> Any:
        return await svc.require(entity, item_id)

    @admin_router.patch(
        path + "/{item_id}", response_model=Out, operation_id=f"catalog_admin_update_{entity}"
    )
    async def patch(item_id: UUID, body: Patch, svc: CatalogServiceDep, actor: AdminUser) -> Any:  # type: ignore[valid-type]
        return await svc.update(entity, item_id, _dump(body, partial=True), str(actor.user_id))

    @admin_router.delete(
        path + "/{item_id}", status_code=204, operation_id=f"catalog_admin_delete_{entity}"
    )
    async def delete(item_id: UUID, svc: CatalogServiceDep, actor: AdminUser) -> Response:
        await svc.delete(entity, item_id, str(actor.user_id))
        return Response(status_code=204)

    _ = (create, get, patch, delete)


@admin_router.get(
    "/subjects/{subject_id}/reference",
    response_model=ReferenceSheetAdminOut,
    operation_id="catalog_admin_get_reference",
)
async def admin_get_reference(subject_id: UUID, svc: CatalogServiceDep) -> Any:
    row = await svc.get_reference(subject_id)
    if row is None:
        raise NotFound(f"no reference sheet for subject {subject_id}")
    return row


@admin_router.put(
    "/subjects/{subject_id}/reference",
    response_model=ReferenceSheetAdminOut,
    operation_id="catalog_admin_put_reference",
)
async def admin_put_reference(
    subject_id: UUID, body: ReferenceSheetIn, svc: CatalogServiceDep, actor: AdminUser
) -> Any:
    """Create or replace the subject's reference sheet (one per subject)."""
    return await svc.upsert_reference(subject_id, _dump(body), str(actor.user_id))


@admin_router.delete(
    "/subjects/{subject_id}/reference",
    status_code=204,
    operation_id="catalog_admin_delete_reference",
)
async def admin_delete_reference(
    subject_id: UUID, svc: CatalogServiceDep, actor: AdminUser
) -> Response:
    await svc.delete_reference(subject_id, str(actor.user_id))
    return Response(status_code=204)


_crud("subject", "/subjects", SubjectIn, SubjectPatch, SubjectOut)
_crud("topic", "/topics", TopicIn, TopicPatch, TopicOut)
_crud("question_type", "/question-types", QuestionTypeIn, QuestionTypePatch, QuestionTypeOut)
_crud("path", "/paths", PathIn, PathPatch, PathOut)
_crud("unit", "/units", UnitIn, UnitPatch, UnitOut)
_crud("lesson", "/lessons", LessonIn, LessonPatch, LessonOut)
_crud("blueprint", "/blueprints", BlueprintIn, BlueprintPatch, BlueprintOut)
_crud("question_base", "/question-bases", QuestionBaseIn, QuestionBasePatch, QuestionBaseOut)


# ---- admin lists / lifecycle -------------------------------------------------------------
@admin_router.get(
    "/subjects", response_model=list[SubjectOut], operation_id="catalog_admin_list_subjects"
)
async def admin_list_subjects(svc: CatalogServiceDep) -> Any:
    return await svc.repo.list("subject")


@admin_router.get(
    "/topics", response_model=list[TopicOut], operation_id="catalog_admin_list_topics"
)
async def admin_list_topics(svc: CatalogServiceDep, subject_id: UUID) -> Any:
    return await svc.repo.list("topic", subject_id=subject_id)


@admin_router.get(
    "/question-types",
    response_model=list[QuestionTypeOut],
    operation_id="catalog_admin_list_question_types",
)
async def admin_list_types(svc: CatalogServiceDep) -> Any:
    return await svc.repo.list("question_type")


@admin_router.get("/paths", response_model=list[PathOut], operation_id="catalog_admin_list_paths")
async def admin_list_paths(svc: CatalogServiceDep, subject_id: UUID) -> Any:
    return await svc.repo.list("path", subject_id=subject_id)


@admin_router.get("/units", response_model=list[UnitOut], operation_id="catalog_admin_list_units")
async def admin_list_units(svc: CatalogServiceDep, path_id: UUID) -> Any:
    return await svc.repo.list("unit", path_id=path_id)


@admin_router.get(
    "/lessons", response_model=list[LessonOut], operation_id="catalog_admin_list_lessons"
)
async def admin_list_lessons(svc: CatalogServiceDep, unit_id: UUID) -> Any:
    return await svc.repo.list("lesson", unit_id=unit_id)


@admin_router.get(
    "/blueprints", response_model=list[BlueprintOut], operation_id="catalog_admin_list_blueprints"
)
async def admin_list_blueprints(svc: CatalogServiceDep) -> Any:
    return await svc.repo.list("blueprint")


@admin_router.get(
    "/question-bases",
    response_model=list[QuestionBaseOut],
    operation_id="catalog_admin_list_question_bases",
)
async def admin_list_bases(svc: CatalogServiceDep, include_archived: bool = False) -> Any:
    rows = await svc.repo.list("question_base")
    return rows if include_archived else [r for r in rows if not r["archived"]]


@admin_router.post(
    "/question-bases/{item_id}/archive",
    response_model=QuestionBaseOut,
    operation_id="catalog_admin_archive_question_base",
)
async def admin_archive_base(item_id: UUID, svc: CatalogServiceDep, actor: AdminUser) -> Any:
    """Hide a base from learners and default admin lists without deleting its questions."""
    return await svc.update("question_base", item_id, {"archived": True}, str(actor.user_id))


@admin_router.post(
    "/question-bases/{item_id}/unarchive",
    response_model=QuestionBaseOut,
    operation_id="catalog_admin_unarchive_question_base",
)
async def admin_unarchive_base(item_id: UUID, svc: CatalogServiceDep, actor: AdminUser) -> Any:
    return await svc.update("question_base", item_id, {"archived": False}, str(actor.user_id))


@admin_router.post(
    "/topics/reorder", response_model=list[TopicOut], operation_id="catalog_admin_reorder_topics"
)
async def reorder_topics(
    body: ReorderIn, subject_id: UUID, svc: CatalogServiceDep, actor: AdminUser
) -> Any:
    return await svc.reorder("topic", body.ids, str(actor.user_id), subject_id=subject_id)


@admin_router.post(
    "/units/reorder", response_model=list[UnitOut], operation_id="catalog_admin_reorder_units"
)
async def reorder_units(
    body: ReorderIn, path_id: UUID, svc: CatalogServiceDep, actor: AdminUser
) -> Any:
    return await svc.reorder("unit", body.ids, str(actor.user_id), path_id=path_id)


@admin_router.post(
    "/lessons/reorder", response_model=list[LessonOut], operation_id="catalog_admin_reorder_lessons"
)
async def reorder_lessons(
    body: ReorderIn, unit_id: UUID, svc: CatalogServiceDep, actor: AdminUser
) -> Any:
    return await svc.reorder("lesson", body.ids, str(actor.user_id), unit_id=unit_id)


@admin_router.post(
    "/paths/{item_id}/publish", response_model=PathOut, operation_id="catalog_admin_publish_path"
)
async def publish_path(item_id: UUID, svc: CatalogServiceDep, actor: AdminUser) -> Any:
    return await svc.set_path_status(item_id, "published", str(actor.user_id))


@admin_router.post(
    "/paths/{item_id}/unpublish",
    response_model=PathOut,
    operation_id="catalog_admin_unpublish_path",
)
async def unpublish_path(item_id: UUID, svc: CatalogServiceDep, actor: AdminUser) -> Any:
    return await svc.set_path_status(item_id, "draft", str(actor.user_id))


@admin_router.post(
    "/blueprints/{item_id}/publish",
    response_model=BlueprintOut,
    operation_id="catalog_admin_publish_blueprint",
)
async def publish_blueprint(item_id: UUID, svc: CatalogServiceDep, actor: AdminUser) -> Any:
    return await svc.publish_blueprint(item_id, str(actor.user_id))


@admin_router.post(
    "/blueprints/{item_id}/clone",
    response_model=BlueprintOut,
    status_code=201,
    operation_id="catalog_admin_clone_blueprint",
)
async def clone_blueprint(item_id: UUID, svc: CatalogServiceDep, actor: AdminUser) -> Any:
    return await svc.clone_blueprint(item_id, str(actor.user_id))


@admin_router.get(
    "/audit-log", response_model=list[AuditOut], operation_id="catalog_admin_audit_log"
)
async def audit_log(
    svc: CatalogServiceDep,
    entity: str | None = None,
    entity_id: UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> Any:
    return await svc.audit(entity, entity_id, limit)


@admin_router.get(
    "/launch-gate", response_model=list[LaunchGateRow], operation_id="catalog_admin_launch_gate"
)
async def launch_gate(session: Session, svc: CatalogServiceDep, subject_id: UUID) -> Any:
    """Per-lesson verified pool vs the minimum needed to show the lesson to learners."""
    min_pool = bank.content_min_pool()
    out: list[LaunchGateRow] = []
    for p in await svc.repo.list("path", subject_id=subject_id):
        for u in await svc.repo.list("unit", path_id=p["id"]):
            for le in await svc.repo.list("lesson", unit_id=u["id"]):
                topics = [UUID(t) for t in le["topic_ids"]]
                eff = await facade.expand_topic_ids(session, subject_id, topics) if topics else []
                pool = await bank.count_verified(
                    session,
                    subject_id=subject_id,
                    topic_ids=eff or None,
                    type_ids=[UUID(t) for t in le["type_ids"]] or None,
                    language=p["language"],
                )
                need = max(min_pool, le["question_count"])
                out.append(
                    LaunchGateRow(
                        lesson_id=le["id"],
                        path_id=p["id"],
                        subject_id=subject_id,
                        language=p["language"],
                        title=dom.pick_name(le["names"]),
                        pool=pool,
                        needed=need,
                        visible=pool >= need,
                    )
                )
    return out


# ---- learner ---------------------------------------------------------------------------------
@router.get(
    "/subjects",
    response_model=list[SubjectOut],
    operation_id="catalog_list_subjects",
    responses=ERR,
)
async def list_subjects(
    session: Session,
    language: Annotated[
        Literal["uz", "ru", "en"] | None,
        Query(
            description="Count only questions in this content language (learner's education language)"
        ),
    ] = None,
) -> Any:
    return await subjects_with_counts(session, await facade.list_subjects(session), language)


async def subjects_with_counts(
    session: AsyncSession, subjects: list[Any], language: str | None = None
) -> list[SubjectOut]:
    """Subjects annotated with their verified question count so clients can flag empty ones."""
    out: list[SubjectOut] = []
    for s in subjects:
        total = await bank.count_verified_for_subject(session, s.id, language)
        out.append(SubjectOut.model_validate(s).model_copy(update={"question_count": total}))
    return out


@router.get(
    "/subjects/{subject_id}/reference",
    response_model=ReferenceSheetOut,
    operation_id="catalog_get_reference",
    responses=ERR,
)
async def get_reference(
    subject_id: UUID, session: Session, locale: str = "uz-Latn"
) -> facade.ReferenceSheetDTO:
    """Formula/reference sheet of a subject (404 when the subject has none or it is switched off)."""
    sheet = await facade.get_reference(session, subject_id, locale)
    if sheet is None:
        raise NotFound(f"no reference sheet for subject {subject_id}")
    return sheet


@router.get(
    "/subjects/{subject_id}/topics",
    response_model=list[TopicOut],
    operation_id="catalog_list_topics",
    responses=ERR,
)
async def list_topics(subject_id: UUID, session: Session) -> Any:
    return [t for t in await facade.list_topics(session, subject_id) if t.active]


@router.get(
    "/subjects/{subject_id}/path",
    response_model=LearnerPathOut,
    operation_id="catalog_get_path",
    responses=ERR,
)
async def get_path(
    subject_id: UUID, language: str, session: Session, user: OptionalUser, locale: str = "uz-Latn"
) -> LearnerPathOut:
    """Published path; `progress` is per-user when a bearer token is sent, otherwise nothing is completed."""
    p = await facade.get_path(session, subject_id, language, locale=locale)
    if p is None:
        raise NotFound("No published path for this subject and language")
    done: set[UUID] = set()
    start_unit = 0
    if user is not None:
        done, start_unit = await learning.path_progress(
            session, user.user_id, subject_id, [le.id for u in p.units for le in u.lessons]
        )
    lesson_prog, unit_prog = derive_path_progress(
        [[le.id in done for le in u.lessons] for u in p.units], start_unit
    )
    units = [
        LearnerUnitOut(
            id=u.id,
            title=u.title,
            names=u.names,
            progress=ProgressOut.model_validate(unit_prog[ui], from_attributes=True),
            lessons=[
                LearnerLessonOut(
                    id=le.id,
                    title=le.title,
                    names=le.names,
                    topic_ids=le.topic_ids,
                    type_ids=le.type_ids,
                    question_count=le.question_count,
                    legendary=le.legendary,
                    pool=le.pool,
                    theory=[TheoryCard(**c) for c in le.theory],
                    has_theory=bool(le.theory),
                    progress=ProgressOut.model_validate(lesson_prog[ui][li], from_attributes=True),
                )
                for li, le in enumerate(u.lessons)
            ],
        )
        for ui, u in enumerate(p.units)
    ]
    return LearnerPathOut(
        id=p.id, subject_id=p.subject_id, language=p.language, names=p.names, units=units
    )


@router.get(
    "/blueprints",
    response_model=list[BlueprintOut],
    operation_id="catalog_list_blueprints",
    responses=ERR,
)
async def list_blueprints(
    session: Session, kind: Literal["official", "generated", "template"] | None = None
) -> Any:
    return await facade.list_blueprints(session, kind=kind)


@router.get(
    "/question-bases",
    response_model=list[QuestionBaseOut],
    operation_id="catalog_list_question_bases",
    responses=ERR,
)
async def list_bases(svc: CatalogServiceDep, session: Session) -> Any:
    return await servable_bases(session, await svc.repo.list("question_base"))


async def servable_bases(
    session: AsyncSession, bases: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Active, non-archived bases that hold at least one verified question; empty ones are not learner-facing."""
    return [
        b
        for b in bases
        if b["active"]
        and not b.get("archived", False)
        and await bank.count_verified_by_source(session, b["id"]) > 0
    ]
