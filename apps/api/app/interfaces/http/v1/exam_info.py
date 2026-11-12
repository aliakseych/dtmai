from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, Field

from app.modules.exam_info.domain.models import (
    CertRule,
    ExamEvent,
    ExamProfile,
    FaqItem,
    Section,
    localize,
)
from app.modules.exam_info.wiring import ServiceDep
from app.shared.audit import audit_admin
from app.shared.deps import require_role
from app.shared.errors import ProblemDetails, ValidationFailed
from app.shared.locale import SUPPORTED
from app.shared.security import Principal

SourceUrl = Annotated[str, Field(pattern=r"^https?://", max_length=2048)]

router = APIRouter(tags=["exam-info"])
admin_router = APIRouter(tags=["exam-info-admin"], dependencies=[Depends(require_role("admin"))])

ERR: dict[int | str, dict[str, Any]] = {
    401: {"model": ProblemDetails, "description": "Unauthorized"},
    403: {"model": ProblemDetails, "description": "Forbidden"},
    404: {"model": ProblemDetails, "description": "Not found"},
    409: {"model": ProblemDetails, "description": "Conflict"},
    422: {"model": ProblemDetails, "description": "Validation failed"},
}

Admin = Annotated[Principal, Depends(require_role("admin"))]
# {locale: text} maps keep the contract stable when a locale is added.
Texts = dict[str, str]


def _f(v: Decimal | None) -> float | None:
    return None if v is None else float(v)


class CertRuleOut(BaseModel):
    id: UUID
    section_id: UUID
    cert_type: str
    language_subject_id: UUID | None
    level_label: str | None
    min_value: float | None
    awarded_fraction: float
    note: Texts
    verified: bool
    source_url: str | None
    active: bool


class ExamSectionOut(BaseModel):
    id: UUID
    role: str
    slot: int
    names: Texts
    subject_id: UUID | None
    subject_code: str | None
    choice_group: str | None
    question_count: int | None
    points_per_question: float | None
    max_points: float
    exemptible: bool
    in_app: bool
    available: bool


class ExamProfileOut(BaseModel):
    id: UUID
    code: str
    kind: str
    direction_code: str | None
    group_code: str | None
    names: Texts
    exam_year: int
    exam_date: date | None
    date_verified: bool
    max_score: float
    app_max_score: float
    trust_self_declared: bool
    taper_days: int
    mock_blueprint_id: UUID | None
    source_url: str | None
    verified: bool
    active: bool
    position: int
    sections: list[ExamSectionOut]
    certificate_rules: list[CertRuleOut]
    choices: dict[str, list[UUID]]


class ExamEventOut(BaseModel):
    id: UUID
    exam_year: int
    kind: str
    starts_on: date
    ends_on: date | None
    label: Texts
    verified: bool
    source_url: str | None
    position: int


class FaqOut(BaseModel):
    id: UUID
    key: str
    category: str
    question: str
    answer: str
    verified: bool
    source_url: str | None


class FaqAdminOut(BaseModel):
    id: UUID
    key: str
    category: str
    question: Texts
    answer: Texts
    position: int
    published: bool
    verified: bool
    source_url: str | None
    updated_at: datetime | None


def _cert_rule(r: CertRule) -> CertRuleOut:
    return CertRuleOut(
        id=r.id,
        section_id=r.section_id,
        cert_type=r.cert_type,
        language_subject_id=r.language_subject_id,
        level_label=r.level_label,
        min_value=_f(r.min_value),
        awarded_fraction=float(r.awarded_fraction),
        note=r.note,
        verified=r.verified,
        source_url=r.source_url,
        active=r.active,
    )


def _section(s: Section) -> ExamSectionOut:
    return ExamSectionOut(
        id=s.id,
        role=s.role,
        slot=s.slot,
        names=s.names,
        subject_id=s.subject_id,
        subject_code=s.subject_code,
        choice_group=s.choice_group,
        question_count=s.question_count,
        points_per_question=_f(s.points_per_question),
        max_points=float(s.max_points),
        exemptible=s.exemptible,
        in_app=s.in_app,
        available=s.available,
    )


def _profile(p: ExamProfile) -> ExamProfileOut:
    return ExamProfileOut(
        id=p.id,
        code=p.code,
        kind=p.kind,
        direction_code=p.direction_code,
        group_code=p.group_code,
        names=p.names,
        exam_year=p.exam_year,
        exam_date=p.exam_date,
        date_verified=p.date_verified,
        max_score=float(p.max_score),
        app_max_score=float(sum((s.max_points for s in p.planned_sections), Decimal(0))),
        trust_self_declared=p.trust_self_declared,
        taper_days=p.taper_days,
        mock_blueprint_id=p.mock_blueprint_id,
        source_url=p.source_url,
        verified=p.verified,
        active=p.active,
        position=p.position,
        sections=[_section(s) for s in p.sections],
        certificate_rules=[_cert_rule(r) for r in p.rules],
        choices={g: list(ids) for g, ids in p.choices.items()},
    )


def _event(e: ExamEvent) -> ExamEventOut:
    return ExamEventOut(
        id=e.id,
        exam_year=e.exam_year,
        kind=e.kind,
        starts_on=e.starts_on,
        ends_on=e.ends_on,
        label=e.label,
        verified=e.verified,
        source_url=e.source_url,
        position=e.position,
    )


def _faq_admin(f: FaqItem) -> FaqAdminOut:
    return FaqAdminOut(
        id=f.id,
        key=f.key,
        category=f.category,
        question=f.question,
        answer=f.answer,
        position=f.position,
        published=f.published,
        verified=f.verified,
        source_url=f.source_url,
        updated_at=f.updated_at,
    )


# --- public ---------------------------------------------------------------------------
@router.get(
    "/profiles",
    response_model=list[ExamProfileOut],
    operation_id="exam_info_list_profiles",
    responses=ERR,
)
async def list_profiles(svc: ServiceDep) -> list[ExamProfileOut]:
    return [_profile(p) for p in await svc.list_profiles(active_only=True)]


@router.get(
    "/profiles/{direction_code}",
    response_model=ExamProfileOut,
    operation_id="exam_info_get_profile",
    responses=ERR,
)
async def get_profile(direction_code: str, svc: ServiceDep) -> ExamProfileOut:
    return _profile(await svc.get_profile_by_direction(direction_code))


@router.get(
    "/events",
    response_model=list[ExamEventOut],
    operation_id="exam_info_list_events",
    responses=ERR,
)
async def list_events(svc: ServiceDep, exam_year: int | None = None) -> list[ExamEventOut]:
    return [_event(e) for e in await svc.list_events(exam_year)]


@router.get("/faq", response_model=list[FaqOut], operation_id="exam_info_list_faq", responses=ERR)
async def list_faq(
    svc: ServiceDep,
    locale: Annotated[str, Query()] = "uz-Latn",
    category: str | None = None,
) -> list[FaqOut]:
    if locale not in SUPPORTED:
        raise ValidationFailed(f"unsupported locale: {locale}", code="unsupported_locale")
    return [
        FaqOut(
            id=f.id,
            key=f.key,
            category=f.category,
            question=localize(f.question, locale),
            answer=localize(f.answer, locale),
            verified=f.verified,
            source_url=f.source_url,
        )
        for f in await svc.list_faq(published_only=True, category=category)
    ]


# --- admin: FAQ ------------------------------------------------------------------------------
class FaqIn(BaseModel):
    key: str = Field(min_length=1, max_length=64)
    category: str = Field(min_length=1, max_length=32)
    question: Texts
    answer: Texts
    position: int = 0
    published: bool = True
    verified: bool = False
    source_url: SourceUrl | None = None


@admin_router.get(
    "/faq", response_model=list[FaqAdminOut], operation_id="exam_info_admin_list_faq", responses=ERR
)
async def admin_list_faq(svc: ServiceDep) -> list[FaqAdminOut]:
    return [_faq_admin(f) for f in await svc.list_faq(published_only=False)]


@admin_router.post(
    "/faq",
    response_model=FaqAdminOut,
    status_code=201,
    operation_id="exam_info_admin_create_faq",
    responses=ERR,
)
async def admin_create_faq(body: FaqIn, svc: ServiceDep, who: Admin) -> FaqAdminOut:
    item = await svc.create_faq(updated_by=who.user_id, **body.model_dump())
    audit_admin(who, "exam_info.faq_create", key=item.key)
    return _faq_admin(item)


@admin_router.put(
    "/faq/{faq_id}",
    response_model=FaqAdminOut,
    operation_id="exam_info_admin_update_faq",
    responses=ERR,
)
async def admin_update_faq(faq_id: UUID, body: FaqIn, svc: ServiceDep, who: Admin) -> FaqAdminOut:
    item = await svc.update_faq(faq_id, updated_by=who.user_id, **body.model_dump())
    audit_admin(who, "exam_info.faq_update", key=item.key)
    return _faq_admin(item)


@admin_router.delete(
    "/faq/{faq_id}", status_code=204, operation_id="exam_info_admin_delete_faq", responses=ERR
)
async def admin_delete_faq(faq_id: UUID, svc: ServiceDep, who: Admin) -> Response:
    await svc.delete_faq(faq_id)
    audit_admin(who, "exam_info.faq_delete", id=str(faq_id))
    return Response(status_code=204)


# --- admin: events -------------------------------------------------------------------------------
class EventIn(BaseModel):
    exam_year: int = Field(ge=2025, le=2100)
    kind: str
    starts_on: date
    ends_on: date | None = None
    label: Texts
    verified: bool = False
    source_url: SourceUrl | None = None
    position: int = 0


@admin_router.get(
    "/events",
    response_model=list[ExamEventOut],
    operation_id="exam_info_admin_list_events",
    responses=ERR,
)
async def admin_list_events(svc: ServiceDep) -> list[ExamEventOut]:
    return [_event(e) for e in await svc.list_events()]


@admin_router.post(
    "/events",
    response_model=ExamEventOut,
    status_code=201,
    operation_id="exam_info_admin_create_event",
    responses=ERR,
)
async def admin_create_event(body: EventIn, svc: ServiceDep, who: Admin) -> ExamEventOut:
    event = await svc.create_event(**body.model_dump())
    audit_admin(who, "exam_info.event_create", year=event.exam_year, kind=event.kind)
    return _event(event)


@admin_router.put(
    "/events/{event_id}",
    response_model=ExamEventOut,
    operation_id="exam_info_admin_update_event",
    responses=ERR,
)
async def admin_update_event(
    event_id: UUID, body: EventIn, svc: ServiceDep, who: Admin
) -> ExamEventOut:
    event = await svc.update_event(event_id, **body.model_dump())
    audit_admin(who, "exam_info.event_update", id=str(event_id))
    return _event(event)


@admin_router.delete(
    "/events/{event_id}",
    status_code=204,
    operation_id="exam_info_admin_delete_event",
    responses=ERR,
)
async def admin_delete_event(event_id: UUID, svc: ServiceDep, who: Admin) -> Response:
    await svc.delete_event(event_id)
    audit_admin(who, "exam_info.event_delete", id=str(event_id))
    return Response(status_code=204)


# --- admin: profiles, sections, certificate rules -----------------------------------------------
class ProfilePatch(BaseModel):
    exam_date: date | None = None
    date_verified: bool | None = None
    verified: bool | None = None
    active: bool | None = None
    trust_self_declared: bool | None = None
    taper_days: int | None = Field(default=None, ge=5, le=7)
    mock_blueprint_id: UUID | None = None
    source_url: SourceUrl | None = None
    position: int | None = None


class SectionPatch(BaseModel):
    subject_id: UUID | None = None


class ChoiceIn(BaseModel):
    subject_ids: list[UUID]


class CertRuleIn(BaseModel):
    cert_type: str
    language_subject_id: UUID | None = None
    level_label: str | None = None
    min_value: Decimal | None = Field(default=None, ge=0, lt=100000)
    awarded_fraction: Decimal = Decimal(1)
    note: Texts = Field(default_factory=dict)
    verified: bool = False
    source_url: SourceUrl | None = None
    active: bool = True


class CertRuleCreate(CertRuleIn):
    section_id: UUID


@admin_router.get(
    "/profiles",
    response_model=list[ExamProfileOut],
    operation_id="exam_info_admin_list_profiles",
    responses=ERR,
)
async def admin_list_profiles(svc: ServiceDep) -> list[ExamProfileOut]:
    return [_profile(p) for p in await svc.list_profiles(active_only=False)]


@admin_router.patch(
    "/profiles/{profile_id}",
    response_model=ExamProfileOut,
    operation_id="exam_info_admin_update_profile",
    responses=ERR,
)
async def admin_update_profile(
    profile_id: UUID, body: ProfilePatch, svc: ServiceDep, who: Admin
) -> ExamProfileOut:
    fields = body.model_dump(exclude_unset=True)
    profile = await svc.update_profile(profile_id, fields)
    audit_admin(who, "exam_info.profile_update", id=str(profile_id), fields=sorted(fields))
    return _profile(profile)


@admin_router.patch(
    "/sections/{section_id}",
    status_code=204,
    operation_id="exam_info_admin_update_section",
    responses=ERR,
)
async def admin_update_section(
    section_id: UUID, body: SectionPatch, svc: ServiceDep, who: Admin
) -> Response:
    await svc.set_section_subject(section_id, body.subject_id)
    audit_admin(who, "exam_info.section_update", id=str(section_id))
    return Response(status_code=204)


@admin_router.put(
    "/choices/{group}",
    status_code=204,
    operation_id="exam_info_admin_replace_choice",
    responses=ERR,
)
async def admin_replace_choice(group: str, body: ChoiceIn, svc: ServiceDep, who: Admin) -> Response:
    await svc.replace_choice(group, body.subject_ids)
    audit_admin(who, "exam_info.choice_replace", group=group)
    return Response(status_code=204)


@admin_router.post(
    "/certificate-rules",
    response_model=CertRuleOut,
    status_code=201,
    operation_id="exam_info_admin_create_cert_rule",
    responses=ERR,
)
async def admin_create_cert_rule(body: CertRuleCreate, svc: ServiceDep, who: Admin) -> CertRuleOut:
    rule = await svc.create_rule(**body.model_dump())
    audit_admin(who, "exam_info.cert_rule_create", id=str(rule.id))
    return _cert_rule(rule)


@admin_router.put(
    "/certificate-rules/{rule_id}",
    response_model=CertRuleOut,
    operation_id="exam_info_admin_update_cert_rule",
    responses=ERR,
)
async def admin_update_cert_rule(
    rule_id: UUID, body: CertRuleIn, svc: ServiceDep, who: Admin
) -> CertRuleOut:
    rule = await svc.update_rule(rule_id, **body.model_dump())
    audit_admin(who, "exam_info.cert_rule_update", id=str(rule_id))
    return _cert_rule(rule)


@admin_router.delete(
    "/certificate-rules/{rule_id}",
    status_code=204,
    operation_id="exam_info_admin_delete_cert_rule",
    responses=ERR,
)
async def admin_delete_cert_rule(rule_id: UUID, svc: ServiceDep, who: Admin) -> Response:
    await svc.delete_rule(rule_id)
    audit_admin(who, "exam_info.cert_rule_delete", id=str(rule_id))
    return Response(status_code=204)
