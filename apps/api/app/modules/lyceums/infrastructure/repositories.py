from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.lyceums.domain.models import (
    ImportRun,
    ImportStatus,
    SourceLanguage,
    SourceLyceum,
    SourceSpeciality,
)
from app.modules.lyceums.domain.rep import (
    MembershipStatus,
    Post,
    PostKind,
    PostStatus,
    RepMembership,
)
from app.modules.lyceums.domain.profile import CityView
from app.modules.lyceums.infrastructure.orm import (
    CityRow,
    EducationLanguageRow,
    ImportRunRow,
    LyceumPostRow,
    LyceumRow,
    RepMembershipRow,
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

    async def search(
        self, q: str | None, limit: int, offset: int, sort: str = "competition"
    ) -> list[LyceumRow]:
        """`competition`: latest-year applications/quota descending, unknown last; `name`: A-Z."""
        stmt = select(LyceumRow)
        if sort == "name":
            stmt = stmt.order_by(LyceumRow.name_uz)
        else:
            latest = (
                select(YearlyStatRow.lyceum_id, func.max(YearlyStatRow.year).label("y"))
                .group_by(YearlyStatRow.lyceum_id).subquery()
            )
            totals = (
                select(
                    YearlyStatRow.lyceum_id.label("lyceum_id"),
                    func.sum(YearlyStatRow.quota).label("quota"),
                    func.sum(YearlyStatRow.applications).label("apps"),
                )
                .join(latest, (latest.c.lyceum_id == YearlyStatRow.lyceum_id)
                      & (latest.c.y == YearlyStatRow.year))
                .group_by(YearlyStatRow.lyceum_id).subquery()
            )
            ratio = totals.c.apps / func.nullif(totals.c.quota, 0)
            stmt = (
                stmt.outerjoin(totals, totals.c.lyceum_id == LyceumRow.id)
                .order_by(ratio.desc().nulls_last(), LyceumRow.name_uz)
            )
        stmt = stmt.limit(limit).offset(offset)
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



class SqlLyceumProfiles:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def exists(self, lyceum_id: UUID) -> bool:
        return await self._s.get(LyceumRow, lyceum_id) is not None

    async def mark_verified_rep(self, lyceum_id: UUID) -> None:
        await self._s.execute(
            update(LyceumRow).where(LyceumRow.id == lyceum_id).values(verified_rep=True)
        )

    async def update_fields(self, lyceum_id: UUID, fields: dict[str, object]) -> bool:
        row = await self._s.get(LyceumRow, lyceum_id)
        if row is None:
            return False
        for key, value in fields.items():
            setattr(row, key, value)
        await self._s.flush()
        return True


class SqlCities:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def exists(self, code: str) -> bool:
        return await self._s.get(CityRow, code) is not None

    async def list_with_counts(self) -> list[CityView]:
        counts = (
            select(LyceumRow.city, func.count(LyceumRow.id).label("n"))
            .where(LyceumRow.city.is_not(None)).group_by(LyceumRow.city).subquery()
        )
        stmt = select(CityRow, func.coalesce(counts.c.n, 0)).outerjoin(
            counts, counts.c.city == CityRow.code
        )
        out = [
            CityView(
                code=c.code,
                names={"uz-Latn": c.name_uz_latn, "uz-Cyrl": c.name_uz_cyrl,
                       "ru": c.name_ru, "en": c.name_en},
                lyceum_count=int(n),
            )
            for c, n in (await self._s.execute(stmt))
        ]
        return sorted(out, key=lambda c: c.names["uz-Latn"].casefold())


def _membership(r: RepMembershipRow) -> RepMembership:
    return RepMembership(
        user_id=r.user_id, lyceum_id=r.lyceum_id, status=MembershipStatus(r.status),
        note=r.note, created_at=r.created_at, decided_at=r.decided_at,
    )


class SqlMemberships:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(self, user_id: UUID, lyceum_id: UUID) -> RepMembership | None:
        row = await self._s.get(RepMembershipRow, (user_id, lyceum_id))
        return _membership(row) if row else None

    async def add(self, membership: RepMembership) -> None:
        self._s.add(RepMembershipRow(
            user_id=membership.user_id, lyceum_id=membership.lyceum_id,
            status=membership.status.value, note=membership.note,
        ))
        await self._s.flush()

    async def save(self, membership: RepMembership) -> None:
        row = await self._s.get(RepMembershipRow, (membership.user_id, membership.lyceum_id))
        if row is None:
            return
        row.status, row.note, row.decided_at = (
            membership.status.value, membership.note, membership.decided_at,
        )
        await self._s.flush()

    async def delete(self, user_id: UUID, lyceum_id: UUID) -> None:
        await self._s.execute(delete(RepMembershipRow).where(
            RepMembershipRow.user_id == user_id, RepMembershipRow.lyceum_id == lyceum_id))

    async def list_pending(self, limit: int) -> list[RepMembership]:
        rows = await self._s.scalars(
            select(RepMembershipRow)
            .where(RepMembershipRow.status == MembershipStatus.PENDING.value)
            .order_by(RepMembershipRow.created_at).limit(limit)
        )
        return [_membership(r) for r in rows]


def _post(r: LyceumPostRow) -> Post:
    return Post(
        id=r.id, lyceum_id=r.lyceum_id, author_id=r.author_id, kind=PostKind(r.kind),
        title=r.title, body=r.body, starts_at=r.starts_at, link=r.link,
        status=PostStatus(r.status), reject_reason=r.reject_reason, created_at=r.created_at,
        updated_at=r.updated_at, published_at=r.published_at,
    )


class SqlPosts:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, post: Post) -> None:
        row = LyceumPostRow(id=post.id, lyceum_id=post.lyceum_id, author_id=post.author_id)
        self._fill(row, post)
        self._s.add(row)
        await self._s.flush()
        await self._s.refresh(row)
        post.created_at, post.updated_at = row.created_at, row.updated_at

    @staticmethod
    def _fill(row: LyceumPostRow, p: Post) -> None:
        row.kind, row.title, row.body = p.kind.value, p.title, p.body
        row.starts_at, row.link, row.status = p.starts_at, p.link, p.status.value
        row.reject_reason, row.published_at = p.reject_reason, p.published_at

    async def get(self, post_id: UUID) -> Post | None:
        row = await self._s.get(LyceumPostRow, post_id)
        return _post(row) if row else None

    async def save(self, post: Post) -> None:
        row = await self._s.get(LyceumPostRow, post.id)
        if row is None:
            return
        self._fill(row, post)
        await self._s.flush()
        await self._s.refresh(row)
        post.updated_at = row.updated_at

    async def delete(self, post_id: UUID) -> None:
        await self._s.execute(delete(LyceumPostRow).where(LyceumPostRow.id == post_id))

    async def list_for_lyceum(self, lyceum_id: UUID) -> list[Post]:
        rows = await self._s.scalars(
            select(LyceumPostRow).where(LyceumPostRow.lyceum_id == lyceum_id)
            .order_by(LyceumPostRow.created_at.desc())
        )
        return [_post(r) for r in rows]

    async def list_published(self, lyceum_id: UUID, limit: int) -> list[Post]:
        rows = await self._s.scalars(
            select(LyceumPostRow).where(
                LyceumPostRow.lyceum_id == lyceum_id,
                LyceumPostRow.status == PostStatus.PUBLISHED.value,
            ).order_by(LyceumPostRow.published_at.desc()).limit(limit)
        )
        return [_post(r) for r in rows]

    async def list_by_status(self, status: PostStatus, limit: int) -> list[Post]:
        rows = await self._s.scalars(
            select(LyceumPostRow).where(LyceumPostRow.status == status.value)
            .order_by(LyceumPostRow.created_at).limit(limit)
        )
        return [_post(r) for r in rows]
