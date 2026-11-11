from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.lyceums.domain.models import (
    ImportRun,
    ImportStatus,
    SourceLanguage,
    SourceLyceum,
    SourceSpeciality,
)
from app.modules.lyceums.infrastructure.orm import (
    EducationLanguageRow,
    ImportRunRow,
    LyceumRow,
    YearlyStatRow,
)
from app.shared.ids import new_id


@dataclass(frozen=True, slots=True)
class StatView:
    id: UUID
    lyceum_id: UUID
    language_id: UUID
    speciality_code: str
    name: str
    year: int
    quota: int
    applications: int
    passing_score: float | None


def _run(row: ImportRunRow) -> ImportRun:
    counts = row.counts or {}
    return ImportRun(
        id=row.id, year=row.year, status=ImportStatus(row.status), requested_by=row.requested_by,
        created_at=row.created_at, finished_at=row.finished_at,
        lyceums=counts.get("lyceums", 0), stats=counts.get("stats", 0),
        errors=counts.get("errors", 0), error=row.error,
    )


class SqlImportRuns:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(self, year: int, requested_by: UUID | None) -> ImportRun:
        row = ImportRunRow(
            id=new_id(), year=year, status=ImportStatus.PENDING.value,
            requested_by=requested_by, counts={},
        )
        self._s.add(row)
        await self._s.flush()
        await self._s.refresh(row)
        return _run(row)

    async def get(self, run_id: UUID) -> ImportRun | None:
        row = await self._s.get(ImportRunRow, run_id)
        return _run(row) if row else None

    async def save(self, run: ImportRun) -> None:
        row = await self._s.get(ImportRunRow, run.id)
        if row is None:
            return
        row.status = run.status.value
        row.error = run.error
        row.finished_at = run.finished_at
        row.counts = {"lyceums": run.lyceums, "stats": run.stats, "errors": run.errors}
        await self._s.flush()

    async def list(self, limit: int) -> list[ImportRun]:
        rows = await self._s.scalars(
            select(ImportRunRow).order_by(ImportRunRow.created_at.desc()).limit(limit)
        )
        return [_run(r) for r in rows]


class SqlImportSink:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def upsert_lyceum(self, item: SourceLyceum) -> UUID:
        stmt = insert(LyceumRow).values(
            id=new_id(), external_id=item.external_id, code=item.code,
            name_uz=item.name_uz, name_en=item.name_en, name_ru=item.name_ru,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[LyceumRow.external_id],
            set_={"code": item.code, "name_uz": item.name_uz,
                  "name_en": item.name_en, "name_ru": item.name_ru},
        ).returning(LyceumRow.id)
        return (await self._s.execute(stmt)).scalar_one()

    async def upsert_language(self, item: SourceLanguage) -> UUID:
        stmt = insert(EducationLanguageRow).values(
            id=new_id(), external_id=item.external_id, code=item.code,
            name_uz=item.name_uz, name_en=item.name_en, name_ru=item.name_ru,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[EducationLanguageRow.external_id],
            set_={"code": item.code, "name_uz": item.name_uz,
                  "name_en": item.name_en, "name_ru": item.name_ru},
        ).returning(EducationLanguageRow.id)
        return (await self._s.execute(stmt)).scalar_one()

    async def upsert_stat(
        self, *, lyceum_id: UUID, language_id: UUID, year: int, item: SourceSpeciality
    ) -> None:
        stmt = insert(YearlyStatRow).values(
            id=new_id(), lyceum_id=lyceum_id, language_id=language_id, year=year,
            speciality_code=item.code, name=item.name,
            quota=item.quota, applications=item.applications,
        )
        # passing_score is deliberately not touched: admins enter it manually.
        stmt = stmt.on_conflict_do_update(
            constraint="uq_yearly_stats_key",
            set_={"name": item.name, "quota": item.quota, "applications": item.applications},
        )
        await self._s.execute(stmt)


class SqlLyceumQueries:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def search(self, q: str | None, limit: int, offset: int) -> list[LyceumRow]:
        stmt = select(LyceumRow).order_by(LyceumRow.name_uz).limit(limit).offset(offset)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(
                or_(LyceumRow.name_uz.ilike(like), LyceumRow.name_ru.ilike(like),
                    LyceumRow.name_en.ilike(like), LyceumRow.code == q.strip())
            )
        return list(await self._s.scalars(stmt))

    async def get(self, lyceum_id: UUID) -> LyceumRow | None:
        return await self._s.get(LyceumRow, lyceum_id)

    async def languages(self) -> list[EducationLanguageRow]:
        rows = list(await self._s.scalars(select(EducationLanguageRow).order_by(
            EducationLanguageRow.external_id)))
        # Uzbek and Russian are the dominant instruction languages; show them first.
        first = ("o'zbek", "o‘zbek", "uzbek", "рус", "russ")
        def rank(r: EducationLanguageRow) -> int:
            names = f"{r.name_uz} {r.name_en} {r.name_ru}".lower()
            return next((i for i, k in enumerate(first) if k in names), len(first))
        return sorted(rows, key=rank)

    async def stats_for(self, lyceum_id: UUID) -> list[StatView]:
        rows = await self._s.scalars(
            select(YearlyStatRow).where(YearlyStatRow.lyceum_id == lyceum_id)
            .order_by(YearlyStatRow.year.desc(), YearlyStatRow.speciality_code)
        )
        return [self._view(r) for r in rows]

    async def latest_year_totals(
        self, lyceum_ids: list[UUID]
    ) -> dict[UUID, tuple[int, int, int]]:
        """lyceum_id -> (year, quota, applications) for the newest imported year."""
        if not lyceum_ids:
            return {}
        latest = (
            select(YearlyStatRow.lyceum_id, func.max(YearlyStatRow.year).label("y"))
            .where(YearlyStatRow.lyceum_id.in_(lyceum_ids))
            .group_by(YearlyStatRow.lyceum_id).subquery()
        )
        stmt = (
            select(
                YearlyStatRow.lyceum_id, YearlyStatRow.year,
                func.sum(YearlyStatRow.quota), func.sum(YearlyStatRow.applications),
            )
            .join(latest, (latest.c.lyceum_id == YearlyStatRow.lyceum_id)
                  & (latest.c.y == YearlyStatRow.year))
            .group_by(YearlyStatRow.lyceum_id, YearlyStatRow.year)
        )
        return {
            r[0]: (r[1], int(r[2] or 0), int(r[3] or 0)) for r in (await self._s.execute(stmt))
        }

    async def set_passing_score(self, stat_id: UUID, score: float | None) -> StatView | None:
        row = await self._s.get(YearlyStatRow, stat_id)
        if row is None:
            return None
        row.passing_score = score
        await self._s.flush()
        return self._view(row)

    @staticmethod
    def _view(r: YearlyStatRow) -> StatView:
        return StatView(r.id, r.lyceum_id, r.language_id, r.speciality_code, r.name, r.year,
                        r.quota, r.applications, r.passing_score)
