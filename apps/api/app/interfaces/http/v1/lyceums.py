from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.lyceums.domain.models import (
    ImportRun,
    competition_ratio,
    validate_passing_score,
    validate_year,
)
from app.modules.lyceums.infrastructure.orm import EducationLanguageRow, LyceumRow
from app.modules.lyceums.infrastructure.repositories import (
    SqlImportRuns,
    SqlLyceumQueries,
    StatView,
)
from app.shared.db import get_session
from app.shared.deps import CurrentUser, require_role
from app.shared.errors import NotFound, ProblemDetails

router = APIRouter(tags=["lyceums"])
admin_router = APIRouter(tags=["lyceums-admin"], dependencies=[Depends(require_role("admin"))])

ERR: dict[int | str, dict[str, Any]] = {
    401: {"model": ProblemDetails, "description": "Unauthorized"},
    403: {"model": ProblemDetails, "description": "Forbidden"},
    404: {"model": ProblemDetails, "description": "Not found"},
    422: {"model": ProblemDetails, "description": "Validation failed"},
}

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class NamesOut(BaseModel):
    uz: str
    ru: str
    en: str


class LyceumSummary(BaseModel):
    id: UUID
    code: str
    names: NamesOut
    latest_year: int | None
    quota: int | None
    applications: int | None
    competition_ratio: float | None


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


class LyceumDetail(BaseModel):
    id: UUID
    code: str
    names: NamesOut
    years: list[YearSummary]
    stats: list[StatOut]


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


def _stat(s: StatView) -> StatOut:
    return StatOut(
        id=s.id, language_id=s.language_id, speciality_code=s.speciality_code, name=s.name,
        year=s.year, quota=s.quota, applications=s.applications,
        competition_ratio=competition_ratio(s.applications, s.quota),
        passing_score=s.passing_score,
    )


def _run(r: ImportRun) -> ImportRunOut:
    return ImportRunOut(
        id=r.id, year=r.year, status=r.status.value, lyceums=r.lyceums, stats=r.stats,
        errors=r.errors, error=r.error, created_at=r.created_at, finished_at=r.finished_at,
    )


@router.get("", response_model=list[LyceumSummary], responses=ERR)
async def search_lyceums(
    session: SessionDep,
    _user: CurrentUser,
    q: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[LyceumSummary]:
    queries = SqlLyceumQueries(session)
    rows = await queries.search(q, limit, offset)
    totals = await queries.latest_year_totals([r.id for r in rows])
    out: list[LyceumSummary] = []
    for r in rows:
        year, quota, apps = totals.get(r.id, (None, None, None))
        ratio = competition_ratio(apps, quota) if quota is not None and apps is not None else None
        out.append(LyceumSummary(
            id=r.id, code=r.code, names=_names(r), latest_year=year, quota=quota,
            applications=apps, competition_ratio=ratio,
        ))
    return out


@router.get("/languages", response_model=list[LanguageOut], responses=ERR)
async def list_languages(session: SessionDep, _user: CurrentUser) -> list[LanguageOut]:
    rows = await SqlLyceumQueries(session).languages()
    return [LanguageOut(id=r.id, code=r.code, names=_names(r)) for r in rows]


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
    return LyceumDetail(
        id=row.id, code=row.code, names=_names(row), years=years, stats=[_stat(s) for s in stats]
    )


@admin_router.post("/import", response_model=ImportRunOut, status_code=202, responses=ERR)
async def start_import(body: ImportIn, session: SessionDep, user: CurrentUser) -> ImportRunOut:
    run = await SqlImportRuns(session).create(validate_year(body.year), user.user_id)
    await session.commit()  # the worker must see the row
    from app.interfaces.jobs.lyceums import import_year  # lazy: jobs import the broker

    await import_year.kiq(str(run.id))
    return _run(run)


@admin_router.get("/imports", response_model=list[ImportRunOut], responses=ERR)
async def list_imports(
    session: SessionDep, limit: Annotated[int, Query(ge=1, le=100)] = 20
) -> list[ImportRunOut]:
    return [_run(r) for r in await SqlImportRuns(session).list(limit)]


@admin_router.patch("/stats/{stat_id}", response_model=StatOut, responses=ERR)
async def set_passing_score(stat_id: UUID, body: PassingScoreIn, session: SessionDep) -> StatOut:
    score = validate_passing_score(body.passing_score)
    stat = await SqlLyceumQueries(session).set_passing_score(stat_id, score)
    if stat is None:
        raise NotFound("stat not found", code="stat_not_found")
    return _stat(stat)
