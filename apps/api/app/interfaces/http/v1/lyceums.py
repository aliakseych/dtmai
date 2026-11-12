from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.wiring import build_identity_service
from app.modules.lyceums.application.admission import LyceumAdmission
from app.modules.lyceums.application.importer import list_runs, start_run
from app.modules.lyceums.application.rep import PostInput
from app.modules.lyceums.domain.admission import MAX_PHONES, ContactCard
from app.modules.lyceums.domain.fields import (
    normalize_speciality_code,
    validate_field_subject_ids,
)
from app.modules.lyceums.domain.models import (
    ImportRun,
    competition_ratio,
    validate_passing_score,
)
from app.modules.lyceums.domain.rep import (
    Post,
    PostStatus,
    RepMembership,
)
from app.modules.lyceums.infrastructure.orm import EducationLanguageRow, LyceumRow
from app.modules.lyceums.infrastructure.repositories import (
    SqlFields,
    SqlImportRuns,
    SqlLyceumQueries,
    StatView,
)
from app.modules.lyceums.wiring import (
    build_admission_service,
    build_profile_service,
    build_rep_service,
)
from app.shared.audit import audit_admin
from app.shared.db import get_session
from app.shared.deps import CurrentUser, require_role
from app.shared.errors import NotFound, ProblemDetails
from app.shared.locale import pick_locale
from app.shared.security import Principal

router = APIRouter(tags=["lyceums"])
admin_router = APIRouter(tags=["lyceums-admin"], dependencies=[Depends(require_role("admin"))])

ERR: dict[int | str, dict[str, Any]] = {
    401: {"model": ProblemDetails, "description": "Unauthorized"},
    403: {"model": ProblemDetails, "description": "Forbidden"},
    404: {"model": ProblemDetails, "description": "Not found"},
    422: {"model": ProblemDetails, "description": "Validation failed"},
}

SessionDep = Annotated[AsyncSession, Depends(get_session)]
Admin = Annotated[Principal, Depends(require_role("admin"))]


DormitoryStatusLiteral = Literal["available", "limited", "none", "unknown"]


class CityNamesOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    uz_latn: str = Field(alias="uz-Latn")
    uz_cyrl: str = Field(alias="uz-Cyrl")
    ru: str
    en: str


class CityOut(BaseModel):
    code: str
    names: CityNamesOut
    lyceum_count: int


class NamesOut(BaseModel):
    uz: str
    ru: str
    en: str


class ContactCardOut(BaseModel):
    phones: list[str]
    telegram: str | None


class ContactCardIn(BaseModel):
    phones: list[str] = Field(max_length=MAX_PHONES)
    telegram: str | None = Field(default=None, max_length=200)


class PlanRowOut(BaseModel):
    direction_code: str
    language_name: str | None
    seats_uz: int
    seats_ru: int
    seats_qq: int
    seats_total: int
    source: str
    applications: int | None
    ratio: float | None


class PlanRowIn(BaseModel):
    year: int = Field(ge=2000, le=2100)
    direction_code: str = Field(max_length=16)
    language_name: str | None = Field(default=None, max_length=64)
    seats_uz: int = Field(ge=0)
    seats_ru: int = Field(ge=0)
    seats_qq: int = Field(ge=0)


class AdmissionOut(BaseModel):
    year: int | None
    seats_total: int
    plan: list[PlanRowOut]
    ratio: float | None
    applications_year: int | None
    contact: ContactCardOut | None


class SeedMatchOut(BaseModel):
    kind: Literal["plan", "contact"]
    ref: int
    name: str
    lyceum_id: UUID | None
    lyceum_name: str | None
    source: str | None


class SeedMatchIn(BaseModel):
    lyceum_id: UUID | None = None


class LyceumSummary(BaseModel):
    id: UUID
    code: str
    names: NamesOut
    city: str | None
    logo_url: str | None
    campus_photo_url: str | None
    dormitory_status: DormitoryStatusLiteral
    latest_year: int | None
    quota: int | None
    applications: int | None
    competition_ratio: float | None
    competition: float | None
    competition_year: int | None
    field_codes: list[str]
    seats_total: int | None
    admission_ratio: float | None
    contact: ContactCardOut | None


class FieldOut(BaseModel):
    code: str
    name: str
    subject_ids: list[UUID]
    mapped: bool


class FieldSubjectsIn(BaseModel):
    subject_ids: list[UUID] = Field(max_length=10)


class LanguageOut(BaseModel):
    id: UUID
    code: str
    names: NamesOut


class StatOut(BaseModel):
    id: UUID
    language_id: UUID
    speciality_code: str
    name: str
    year: int
    quota: int
    applications: int
    competition_ratio: float | None
    passing_score: float | None


class YearSummary(BaseModel):
    year: int
    quota: int
    applications: int
    competition_ratio: float | None


class ContactsOut(BaseModel):
    phone: str | None = None
    telegram: str | None = None
    email: str | None = None


class ProfileOut(BaseModel):
    logo_url: str | None
    campus_photo_url: str | None
    gallery_urls: list[str]
    description: dict[str, str]
    courses: list[str]
    university_name: str | None
    city: str | None
    website: str | None
    contacts: ContactsOut
    verified_rep: bool
    dormitory_status: DormitoryStatusLiteral
    dormitory_description: dict[str, str]


class PostOut(BaseModel):
    id: UUID
    lyceum_id: UUID
    kind: str
    title: str
    body: str
    starts_at: datetime | None
    link: str | None
    status: str
    reject_reason: str | None
    created_at: datetime | None
    updated_at: datetime | None
    published_at: datetime | None


class LyceumDetail(BaseModel):
    id: UUID
    code: str
    names: NamesOut
    years: list[YearSummary]
    stats: list[StatOut]
    profile: ProfileOut
    posts: list[PostOut]
    dreamers_count: int
    field_codes: list[str]
    admission: AdmissionOut


class ImportRunOut(BaseModel):
    id: UUID
    year: int
    status: str
    lyceums: int
    stats: int
    errors: int
    error: str | None
    created_at: datetime | None
    finished_at: datetime | None


class ImportIn(BaseModel):
    year: int = Field(ge=2000, le=2100)


class PassingScoreIn(BaseModel):
    passing_score: float | None = None


def _names(row: LyceumRow | EducationLanguageRow) -> NamesOut:
    return NamesOut(uz=row.name_uz, ru=row.name_ru or row.name_uz, en=row.name_en or row.name_uz)


def _profile(row: LyceumRow) -> ProfileOut:
    contacts = row.contacts or {}
    return ProfileOut(
        logo_url=row.logo_url,
        campus_photo_url=row.campus_photo_url,
        gallery_urls=list(row.gallery_urls or []),
        description=dict(row.description or {}),
        courses=list(row.courses or []),
        university_name=row.university_name,
        city=row.city,
        website=row.website,
        contacts=ContactsOut(
            phone=contacts.get("phone"),
            telegram=contacts.get("telegram"),
            email=contacts.get("email"),
        ),
        verified_rep=bool(row.verified_rep),
        dormitory_status=row.dormitory_status or "unknown",  # type: ignore[arg-type]
        dormitory_description=dict(row.dormitory_description or {}),
    )


def _post(p: Post) -> PostOut:
    return PostOut(
        id=p.id,
        lyceum_id=p.lyceum_id,
        kind=p.kind.value,
        title=p.title,
        body=p.body,
        starts_at=p.starts_at,
        link=p.link,
        status=p.status.value,
        reject_reason=p.reject_reason,
        created_at=p.created_at,
        updated_at=p.updated_at,
        published_at=p.published_at,
    )


def _stat(s: StatView) -> StatOut:
    return StatOut(
        id=s.id,
        language_id=s.language_id,
        speciality_code=s.speciality_code,
        name=s.name,
        year=s.year,
        quota=s.quota,
        applications=s.applications,
        competition_ratio=competition_ratio(s.applications, s.quota),
        passing_score=s.passing_score,
    )


def _run(r: ImportRun) -> ImportRunOut:
    return ImportRunOut(
        id=r.id,
        year=r.year,
        status=r.status.value,
        lyceums=r.lyceums,
        stats=r.stats,
        errors=r.errors,
        error=r.error,
        created_at=r.created_at,
        finished_at=r.finished_at,
    )


@router.get("", response_model=list[LyceumSummary], responses=ERR)
async def search_lyceums(
    session: SessionDep,
    _user: CurrentUser,
    q: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
    sort: Annotated[Literal["competition", "name"], Query()] = "competition",
) -> list[LyceumSummary]:
    queries = SqlLyceumQueries(session)
    rows = await queries.search(q, limit, offset, sort)
    totals = await queries.latest_year_totals([r.id for r in rows])
    field_codes = await SqlFields(session).codes_by_lyceum([r.id for r in rows])
    admissions = await build_admission_service(session).for_lyceums([r.id for r in rows])
    out: list[LyceumSummary] = []
    for r in rows:
        year, quota, apps = totals.get(r.id, (None, None, None))
        adm = admissions[r.id]
        ratio = competition_ratio(apps, quota) if quota is not None and apps is not None else None
        out.append(
            LyceumSummary(
                id=r.id,
                code=r.code,
                names=_names(r),
                city=r.city,
                logo_url=r.logo_url,
                campus_photo_url=r.campus_photo_url,
                dormitory_status=r.dormitory_status or "unknown",  # type: ignore[arg-type]
                latest_year=year,
                quota=quota,
                applications=apps,
                competition_ratio=ratio,
                competition=ratio,
                competition_year=year if ratio is not None else None,
                field_codes=field_codes.get(r.id, []),
                seats_total=sum(p.seats.total for p in adm.plan) or None,
                admission_ratio=adm.competition.lyceum_ratio,
                contact=_contact_out(adm.contact),
            )
        )
    return out


@router.get("/cities", response_model=list[CityOut], operation_id="lyceums_list_cities")
async def list_cities(
    session: SessionDep,
    locale: Annotated[str | None, Query(description="UI locale; overrides Accept-Language")] = None,
    accept_language: Annotated[str | None, Header()] = None,
) -> list[CityOut]:
    """Cities sorted by their name in the request locale."""
    cities = await build_profile_service(session).cities(pick_locale(locale or accept_language))
    return [
        CityOut(
            code=c.code, names=CityNamesOut.model_validate(c.names), lyceum_count=c.lyceum_count
        )
        for c in cities
    ]


@router.get("/fields", response_model=list[FieldOut], operation_id="lyceums_list_fields")
async def list_fields(session: SessionDep) -> list[FieldOut]:
    """Distinct fields of study (edu.uz specialities) with their required subject ids."""
    fields = await SqlFields(session).list_fields()
    return [
        FieldOut(code=f.code, name=f.name, subject_ids=f.subject_ids, mapped=f.mapped)
        for f in sorted(fields, key=lambda f: f.name.casefold())
    ]


# edu.uz returns the Uzbek label in every name_* column of the language classifier;
# the stem of the Uzbek name identifies the language, so English is derived here.
_LANGUAGE_EN = (
    ("o‘zbek", "Uzbek"),
    ("o'zbek", "Uzbek"),
    ("ўзбек", "Uzbek"),
    ("rus", "Russian"),
    ("рус", "Russian"),
    ("qoraqalpoq", "Karakalpak"),
    ("қорақалпоқ", "Karakalpak"),
    ("qozoq", "Kazakh"),
    ("қозоқ", "Kazakh"),
    ("tojik", "Tajik"),
    ("тожик", "Tajik"),
    ("turkman", "Turkmen"),
    ("туркман", "Turkmen"),
    ("qirg", "Kyrgyz"),
    ("қирғиз", "Kyrgyz"),
)


def _language_names(row: EducationLanguageRow) -> NamesOut:
    names = _names(row)
    probe = f"{row.name_uz} {row.name_ru}".lower()
    en = next((en for stem, en in _LANGUAGE_EN if stem in probe), None)
    if en is not None and names.en.strip().lower() in ("", row.name_uz.strip().lower()):
        names.en = en
    return names


@router.get("/languages", response_model=list[LanguageOut], responses=ERR)
async def list_languages(session: SessionDep, _user: CurrentUser) -> list[LanguageOut]:
    rows = await SqlLyceumQueries(session).languages()
    return [LanguageOut(id=r.id, code=r.code, names=_language_names(r)) for r in rows]


@router.get("/{lyceum_id}", response_model=LyceumDetail, responses=ERR)
async def lyceum_detail(lyceum_id: UUID, session: SessionDep, _user: CurrentUser) -> LyceumDetail:
    queries = SqlLyceumQueries(session)
    row = await queries.get(lyceum_id)
    if row is None:
        raise NotFound("lyceum not found", code="lyceum_not_found")
    stats = await queries.stats_for(lyceum_id)
    by_year: dict[int, list[int]] = {}
    for s in stats:
        agg = by_year.setdefault(s.year, [0, 0])
        agg[0] += s.quota
        agg[1] += s.applications
    years = [
        YearSummary(year=y, quota=q, applications=a, competition_ratio=competition_ratio(a, q))
        for y, (q, a) in sorted(by_year.items(), reverse=True)
    ]
    posts = await build_rep_service(session).published(lyceum_id)
    field_codes = (await SqlFields(session).codes_by_lyceum([lyceum_id])).get(lyceum_id, [])
    admission = (await build_admission_service(session).for_lyceums([lyceum_id]))[lyceum_id]
    return LyceumDetail(
        field_codes=field_codes,
        id=row.id,
        code=row.code,
        names=_names(row),
        years=years,
        stats=[_stat(s) for s in stats],
        profile=_profile(row),
        posts=[_post(p) for p in posts],
        admission=_admission_out(admission),
        dreamers_count=await build_identity_service(session).count_dreamers(lyceum_id),
    )


@admin_router.post("/import", response_model=ImportRunOut, status_code=202, responses=ERR)
async def start_import(body: ImportIn, session: SessionDep, user: CurrentUser) -> ImportRunOut:
    run = await start_run(SqlImportRuns(session), body.year, user.user_id)
    await session.commit()  # the worker must see the row
    from app.interfaces.jobs.lyceums import import_year  # lazy: jobs import the broker

    await import_year.kiq(str(run.id))
    return _run(run)


@admin_router.get("/imports", response_model=list[ImportRunOut], responses=ERR)
async def list_imports(
    session: SessionDep, limit: Annotated[int, Query(ge=1, le=100)] = 20
) -> list[ImportRunOut]:
    runs = await list_runs(SqlImportRuns(session), limit)
    await session.commit()
    return [_run(r) for r in runs]


@admin_router.put(
    "/fields/{code}",
    response_model=FieldOut,
    operation_id="lyceums_admin_set_field_subjects",
    responses=ERR,
)
async def set_field_subjects(
    code: str, body: FieldSubjectsIn, session: SessionDep, who: Admin
) -> FieldOut:
    """Set the ordered required subjects of a field; an empty list clears the mapping."""
    code = normalize_speciality_code(code)
    ids = validate_field_subject_ids(body.subject_ids)
    fields = SqlFields(session)
    if not await fields.known_code(code):
        raise NotFound("field not found", code="field_not_found")
    if ids:
        await fields.set_subjects(code, ids)
    else:
        await fields.clear_subjects(code)
    audit_admin(
        who, "lyceums.set_field_subjects", field_code=code, subject_ids=[str(i) for i in ids]
    )
    field = next(f for f in await fields.list_fields() if f.code == code)
    return FieldOut(
        code=field.code, name=field.name, subject_ids=field.subject_ids, mapped=field.mapped
    )


@admin_router.delete(
    "/fields/{code}",
    status_code=204,
    operation_id="lyceums_admin_clear_field_subjects",
    responses=ERR,
)
async def clear_field_subjects(code: str, session: SessionDep, who: Admin) -> Response:
    code = normalize_speciality_code(code)
    await SqlFields(session).clear_subjects(code)
    audit_admin(who, "lyceums.clear_field_subjects", field_code=code)
    return Response(status_code=204)


@admin_router.patch("/stats/{stat_id}", response_model=StatOut, responses=ERR)
async def set_passing_score(stat_id: UUID, body: PassingScoreIn, session: SessionDep) -> StatOut:
    score = validate_passing_score(body.passing_score)
    stat = await SqlLyceumQueries(session).set_passing_score(stat_id, score)
    if stat is None:
        raise NotFound("stat not found", code="stat_not_found")
    return _stat(stat)


# --- representatives ----------------------------------------------------------
class ApplyIn(BaseModel):
    note: str | None = Field(default=None, max_length=1000)


class MembershipOut(BaseModel):
    user_id: UUID
    lyceum_id: UUID
    status: str
    note: str | None
    created_at: datetime | None
    decided_at: datetime | None


class PostIn(BaseModel):
    kind: str
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(default="", max_length=5000)
    starts_at: datetime | None = None
    link: str | None = Field(default=None, max_length=500)


def _membership(m: RepMembership) -> MembershipOut:
    return MembershipOut(
        user_id=m.user_id,
        lyceum_id=m.lyceum_id,
        status=m.status.value,
        note=m.note,
        created_at=m.created_at,
        decided_at=m.decided_at,
    )


def _post_input(b: PostIn) -> PostInput:
    return PostInput(kind=b.kind, title=b.title, body=b.body, starts_at=b.starts_at, link=b.link)


@router.post(
    "/{lyceum_id}/rep/apply", status_code=201, operation_id="lyceums_rep_apply", responses=ERR
)
async def rep_apply(
    lyceum_id: UUID, body: ApplyIn, session: SessionDep, user: CurrentUser
) -> MembershipOut:
    m = await build_rep_service(session).apply(
        user.user_id, lyceum_id, body.note, is_guest="guest" in user.roles
    )
    return _membership(m)


@router.get("/{lyceum_id}/rep/membership", operation_id="lyceums_rep_membership", responses=ERR)
async def rep_membership(lyceum_id: UUID, session: SessionDep, user: CurrentUser) -> MembershipOut:
    m = await build_rep_service(session).membership(user.user_id, lyceum_id)
    if m is None:
        raise NotFound("no application", code="rep_application_not_found")
    return _membership(m)


@router.get("/{lyceum_id}/rep/posts", operation_id="lyceums_rep_list_posts", responses=ERR)
async def rep_list_posts(lyceum_id: UUID, session: SessionDep, user: CurrentUser) -> list[PostOut]:
    posts = await build_rep_service(session).list_own(user.user_id, lyceum_id)
    return [_post(p) for p in posts]


@router.post(
    "/{lyceum_id}/rep/posts", status_code=201, operation_id="lyceums_rep_create_post", responses=ERR
)
async def rep_create_post(
    lyceum_id: UUID, body: PostIn, session: SessionDep, user: CurrentUser
) -> PostOut:
    post = await build_rep_service(session).create_post(user.user_id, lyceum_id, _post_input(body))
    return _post(post)


@router.put(
    "/{lyceum_id}/rep/posts/{post_id}", operation_id="lyceums_rep_update_post", responses=ERR
)
async def rep_update_post(
    lyceum_id: UUID, post_id: UUID, body: PostIn, session: SessionDep, user: CurrentUser
) -> PostOut:
    post = await build_rep_service(session).edit_post(
        user.user_id, lyceum_id, post_id, _post_input(body)
    )
    return _post(post)


@router.delete(
    "/{lyceum_id}/rep/posts/{post_id}",
    status_code=204,
    operation_id="lyceums_rep_delete_post",
    responses=ERR,
)
async def rep_delete_post(
    lyceum_id: UUID, post_id: UUID, session: SessionDep, user: CurrentUser
) -> Response:
    await build_rep_service(session).delete_post(user.user_id, lyceum_id, post_id)
    return Response(status_code=204)


class ContactsIn(BaseModel):
    phone: str | None = None
    telegram: str | None = None
    email: str | None = None


def _sent_changes(body: BaseModel) -> dict[str, Any]:
    """Only the keys the client sent; nested contacts dropped of unset members."""
    changes: dict[str, Any] = {}
    for key in body.model_fields_set:
        value = getattr(body, key)
        if isinstance(value, BaseModel):
            value = value.model_dump(exclude_none=True)
        changes[key] = value
    return changes


class RepProfilePatch(BaseModel):
    description: dict[str, str] | None = None
    courses: list[str] | None = None
    contacts: ContactsIn | None = None
    dormitory_status: DormitoryStatusLiteral | None = None
    dormitory_description: dict[str, str] | None = None


@router.patch("/{lyceum_id}/rep/profile", operation_id="lyceums_rep_update_profile", responses=ERR)
async def rep_update_profile(
    lyceum_id: UUID, body: RepProfilePatch, session: SessionDep, user: CurrentUser
) -> ProfileOut:
    await build_rep_service(session).update_profile(user.user_id, lyceum_id, _sent_changes(body))
    row = await SqlLyceumQueries(session).get(lyceum_id)
    if row is None:
        raise NotFound("lyceum not found", code="lyceum_not_found")
    return _profile(row)


# --- admin: profile, applications, moderation -----------------------------------


class LyceumPatch(BaseModel):
    logo_url: str | None = Field(default=None, max_length=500)
    campus_photo_url: str | None = Field(default=None, max_length=500)
    gallery_urls: list[str] | None = None
    description: dict[str, str] | None = None
    courses: list[str] | None = None
    university_name: str | None = Field(default=None, max_length=300)
    city: str | None = Field(default=None, max_length=100)
    website: str | None = Field(default=None, max_length=500)
    contacts: ContactsIn | None = None
    verified_rep: bool | None = None
    dormitory_status: DormitoryStatusLiteral | None = None
    dormitory_description: dict[str, str] | None = None


class ModerateIn(BaseModel):
    action: Literal["publish", "reject"]
    reason: str | None = Field(default=None, max_length=1000)


@admin_router.patch("/{lyceum_id}", operation_id="lyceums_admin_update_profile", responses=ERR)
async def update_profile(
    lyceum_id: UUID, body: LyceumPatch, session: SessionDep, who: Admin
) -> ProfileOut:
    changes = _sent_changes(body)
    changed = await build_profile_service(session).update(lyceum_id, changes)
    row = await SqlLyceumQueries(session).get(lyceum_id)
    if row is None:
        raise NotFound("lyceum not found", code="lyceum_not_found")
    audit_admin(who, "lyceums.update_profile", lyceum_id=str(lyceum_id), fields=changed)
    return _profile(row)


@admin_router.get(
    "/rep/applications", operation_id="lyceums_admin_list_applications", responses=ERR
)
async def list_applications(session: SessionDep) -> list[MembershipOut]:
    return [_membership(m) for m in await build_rep_service(session).list_applications()]


@admin_router.post(
    "/{lyceum_id}/rep/{user_id}/approve", operation_id="lyceums_admin_approve_rep", responses=ERR
)
async def approve_rep(
    lyceum_id: UUID, user_id: UUID, session: SessionDep, who: Admin
) -> MembershipOut:
    m = await build_rep_service(session).approve(user_id, lyceum_id)
    audit_admin(who, "lyceums.rep_approve", lyceum_id=str(lyceum_id), user_id=str(user_id))
    return _membership(m)


@admin_router.post(
    "/{lyceum_id}/rep/{user_id}/reject",
    status_code=204,
    operation_id="lyceums_admin_reject_rep",
    responses=ERR,
)
async def reject_rep(lyceum_id: UUID, user_id: UUID, session: SessionDep, who: Admin) -> Response:
    await build_rep_service(session).reject_application(user_id, lyceum_id)
    audit_admin(who, "lyceums.rep_reject", lyceum_id=str(lyceum_id), user_id=str(user_id))
    return Response(status_code=204)


@admin_router.get("/posts", operation_id="lyceums_admin_list_posts", responses=ERR)
async def admin_list_posts(
    session: SessionDep,
    status: PostStatus = PostStatus.PENDING,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> list[PostOut]:
    return [_post(p) for p in await build_rep_service(session).moderation_queue(status, limit)]


@admin_router.post(
    "/posts/{post_id}/moderate", operation_id="lyceums_admin_moderate_post", responses=ERR
)
async def moderate_post(
    post_id: UUID, body: ModerateIn, session: SessionDep, who: Admin
) -> PostOut:
    post = await build_rep_service(session).moderate(
        post_id, publish=body.action == "publish", reason=body.reason
    )
    audit_admin(who, "lyceums.moderate_post", post_id=str(post_id), decision=body.action)
    return _post(post)


# --- admission plan, contacts, seed matching ----------------------------------
def _admission_out(a: LyceumAdmission) -> AdmissionOut:
    ratios = {d.direction_code: d for d in a.competition.directions}
    return AdmissionOut(
        year=a.plan_year,
        seats_total=sum(r.seats.total for r in a.plan),
        plan=[
            PlanRowOut(
                direction_code=r.direction_code,
                language_name=r.language_name,
                seats_uz=r.seats.uz,
                seats_ru=r.seats.ru,
                seats_qq=r.seats.qq,
                seats_total=r.seats.total,
                source=r.source,
                applications=ratios[r.direction_code].applications
                if r.direction_code in ratios
                else None,
                ratio=ratios[r.direction_code].ratio if r.direction_code in ratios else None,
            )
            for r in a.plan
        ],
        ratio=a.competition.lyceum_ratio,
        applications_year=a.competition.applications_year,
        contact=_contact_out(a.contact),
    )


def _contact_out(c: ContactCard | None) -> ContactCardOut | None:
    return None if c is None else ContactCardOut(phones=list(c.phones), telegram=c.telegram)


@admin_router.get(
    "/admission/matches", operation_id="lyceums_admin_list_seed_matches", responses=ERR
)
async def list_seed_matches(session: SessionDep) -> list[SeedMatchOut]:
    views = await build_admission_service(session).match_overview()
    return [
        SeedMatchOut(
            kind=v.kind,
            ref=v.ref,
            name=v.name,
            lyceum_id=v.lyceum_id,
            lyceum_name=v.lyceum_name,
            source=v.source,
        )
        for v in views
    ]


@admin_router.put(
    "/admission/matches/{kind}/{ref}",
    status_code=204,
    operation_id="lyceums_admin_set_seed_match",
    responses=ERR,
)
async def set_seed_match(
    kind: Literal["plan", "contact"], ref: int, body: SeedMatchIn, session: SessionDep, who: Admin
) -> Response:
    await build_admission_service(session).set_match(kind, ref, body.lyceum_id)
    audit_admin(
        who,
        "lyceums.set_seed_match",
        kind=kind,
        ref=ref,
        lyceum_id=str(body.lyceum_id) if body.lyceum_id else None,
    )
    return Response(status_code=204)


@admin_router.put(
    "/{lyceum_id}/admission/plan",
    response_model=PlanRowOut,
    operation_id="lyceums_admin_put_plan_row",
    responses=ERR,
)
async def put_plan_row(
    lyceum_id: UUID, body: PlanRowIn, session: SessionDep, who: Admin
) -> PlanRowOut:
    row = await build_admission_service(session).put_plan_row(
        lyceum_id,
        body.year,
        body.direction_code,
        body.language_name,
        body.seats_uz,
        body.seats_ru,
        body.seats_qq,
    )
    audit_admin(
        who,
        "lyceums.put_plan_row",
        lyceum_id=str(lyceum_id),
        year=row.year,
        direction_code=row.direction_code,
    )
    return PlanRowOut(
        direction_code=row.direction_code,
        language_name=row.language_name,
        seats_uz=row.seats.uz,
        seats_ru=row.seats.ru,
        seats_qq=row.seats.qq,
        seats_total=row.seats.total,
        source=row.source,
        applications=None,
        ratio=None,
    )


@admin_router.delete(
    "/{lyceum_id}/admission/plan",
    status_code=204,
    operation_id="lyceums_admin_delete_plan_row",
    responses=ERR,
)
async def delete_plan_row(
    lyceum_id: UUID,
    session: SessionDep,
    who: Admin,
    year: Annotated[int, Query(ge=2000, le=2100)],
    direction_code: Annotated[str, Query(max_length=16)],
    language_name: Annotated[str | None, Query(max_length=64)] = None,
) -> Response:
    await build_admission_service(session).delete_plan_row(
        lyceum_id, year, direction_code, language_name
    )
    audit_admin(
        who,
        "lyceums.delete_plan_row",
        lyceum_id=str(lyceum_id),
        year=year,
        direction_code=direction_code,
    )
    return Response(status_code=204)


@admin_router.put(
    "/{lyceum_id}/contact",
    response_model=ContactCardOut,
    operation_id="lyceums_admin_put_contact",
    responses=ERR,
)
async def put_contact(
    lyceum_id: UUID, body: ContactCardIn, session: SessionDep, who: Admin
) -> ContactCardOut:
    card = await build_admission_service(session).put_contacts(
        lyceum_id, body.phones, body.telegram
    )
    audit_admin(who, "lyceums.put_contact", lyceum_id=str(lyceum_id))
    return ContactCardOut(phones=list(card.phones), telegram=card.telegram)
