import json
from functools import lru_cache
from pathlib import Path
from uuid import UUID

from sqlalchemy import and_, delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.lyceums.application.admission import SeedDocs
from app.modules.lyceums.domain.admission import (
    SOURCE_ADMIN,
    SOURCE_SEED,
    ContactCard,
    PlanRow,
    Seats,
    SeedContactEntry,
    SeedDirection,
    SeedPlanEntry,
)
from app.modules.lyceums.infrastructure.orm import (
    AdmissionPlanRow,
    LyceumContactRow,
    LyceumRow,
    PlanTombstoneRow,
    SeedMatchRow,
    YearlyStatRow,
)
from app.shared.ids import new_id

SEED_DIR = Path(__file__).resolve().parent.parent / "seed"


@lru_cache
def load_seed_docs(directory: Path = SEED_DIR) -> SeedDocs:
    plan_doc = json.loads((directory / "admission_plan_2026.json").read_text("utf-8"))
    contact_doc = json.loads((directory / "contacts.json").read_text("utf-8"))
    plan = tuple(
        SeedPlanEntry(
            ref=e["n"],
            name=e["name"],
            directions=tuple(
                SeedDirection(
                    direction_code=d["code"],
                    language_name=d["language"],
                    seats=Seats(uz=d["seats"]["uz"], ru=d["seats"]["ru"], qq=d["seats"]["qq"]),
                )
                for d in e["directions"]
            ),
        )
        for e in plan_doc["lyceums"]
    )
    contacts = tuple(
        SeedContactEntry(
            ref=e["n"],
            name=e["name"],
            district=e["district"],
            phones=tuple(e["phones"]),
            telegram=e["telegram"],
        )
        for e in contact_doc["lyceums"]
    )
    return SeedDocs(plan_year=plan_doc["year"], plan=plan, contacts=contacts)


def _plan(r: AdmissionPlanRow) -> PlanRow:
    return PlanRow(
        lyceum_id=r.lyceum_id,
        year=r.year,
        direction_code=r.direction_code,
        language_name=r.language_name,
        seats=Seats(uz=r.seats_uz, ru=r.seats_ru, qq=r.seats_qq),
        source=r.source,
    )


class SqlAdmissionStore:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def lyceum_names(self) -> dict[UUID, str]:
        rows = await self._s.execute(select(LyceumRow.id, LyceumRow.name_uz))
        return {r.id: r.name_uz for r in rows}

    async def matches(self, kind: str) -> dict[int, tuple[UUID | None, str]]:
        rows = await self._s.scalars(select(SeedMatchRow).where(SeedMatchRow.kind == kind))
        return {r.seed_ref: (r.lyceum_id, r.source) for r in rows}

    async def save_match(self, kind: str, ref: int, lyceum_id: UUID | None, source: str) -> None:
        stmt = insert(SeedMatchRow).values(
            kind=kind, seed_ref=ref, lyceum_id=lyceum_id, source=source
        )
        await self._s.execute(
            stmt.on_conflict_do_update(
                index_elements=[SeedMatchRow.kind, SeedMatchRow.seed_ref],
                set_={"lyceum_id": lyceum_id, "source": source},
            )
        )

    def _plan_key(self, lyceum_id: UUID, year: int, code: str, language: str | None):  # noqa: ANN202
        return and_(
            AdmissionPlanRow.lyceum_id == lyceum_id,
            AdmissionPlanRow.year == year,
            AdmissionPlanRow.direction_code == code,
            func.coalesce(AdmissionPlanRow.language_name, "") == (language or ""),
        )

    async def _put_plan(self, row: PlanRow, *, only_seed: bool) -> bool:
        existing = await self._s.scalar(
            select(AdmissionPlanRow).where(
                self._plan_key(row.lyceum_id, row.year, row.direction_code, row.language_name)
            )
        )
        if existing is None:
            self._s.add(
                AdmissionPlanRow(
                    id=new_id(),
                    lyceum_id=row.lyceum_id,
                    year=row.year,
                    direction_code=row.direction_code,
                    language_name=row.language_name,
                    seats_uz=row.seats.uz,
                    seats_ru=row.seats.ru,
                    seats_qq=row.seats.qq,
                    seats_total=row.seats.total,
                    source=row.source,
                )
            )
        elif only_seed and existing.source != SOURCE_SEED:
            return False
        else:
            existing.seats_uz, existing.seats_ru, existing.seats_qq = (
                row.seats.uz,
                row.seats.ru,
                row.seats.qq,
            )
            existing.seats_total = row.seats.total
            existing.source = row.source
        await self._s.flush()
        return True

    async def upsert_plan_seed(self, row: PlanRow) -> bool:
        return await self._put_plan(row, only_seed=True)

    async def put_plan_admin(self, row: PlanRow) -> None:
        await self._put_plan(row, only_seed=False)

    async def delete_plan(
        self, lyceum_id: UUID, year: int, direction_code: str, language_name: str | None
    ) -> str | None:
        return await self._s.scalar(
            delete(AdmissionPlanRow)
            .where(self._plan_key(lyceum_id, year, direction_code, language_name))
            .returning(AdmissionPlanRow.source)
        )

    async def tombstone_plan(
        self, lyceum_id: UUID, year: int, direction_code: str, language_name: str | None
    ) -> None:
        await self._s.execute(
            insert(PlanTombstoneRow)
            .values(
                lyceum_id=lyceum_id,
                year=year,
                direction_code=direction_code,
                language_name=language_name or "",
            )
            .on_conflict_do_nothing()
        )

    async def is_plan_tombstoned(
        self, lyceum_id: UUID, year: int, direction_code: str, language_name: str | None
    ) -> bool:
        found = await self._s.get(
            PlanTombstoneRow, (lyceum_id, year, direction_code, language_name or "")
        )
        return found is not None

    async def delete_seed_plan(
        self, lyceum_id: UUID, year: int, keys: list[tuple[str, str | None]]
    ) -> None:
        for code, language in keys:
            await self._s.execute(
                delete(AdmissionPlanRow).where(
                    self._plan_key(lyceum_id, year, code, language),
                    AdmissionPlanRow.source == SOURCE_SEED,
                )
            )

    async def delete_seed_contact(self, lyceum_id: UUID) -> None:
        await self._s.execute(
            delete(LyceumContactRow).where(
                LyceumContactRow.lyceum_id == lyceum_id, LyceumContactRow.source == SOURCE_SEED
            )
        )

    async def _put_contact(self, card: ContactCard, *, only_seed: bool) -> bool:
        existing = await self._s.get(LyceumContactRow, card.lyceum_id)
        if existing is None:
            self._s.add(
                LyceumContactRow(
                    lyceum_id=card.lyceum_id,
                    phones=list(card.phones),
                    telegram=card.telegram,
                    source=card.source,
                )
            )
        elif only_seed and existing.source != SOURCE_SEED:
            return False
        else:
            existing.phones = list(card.phones)
            existing.telegram = card.telegram
            existing.source = card.source
        await self._s.flush()
        return True

    async def upsert_contact_seed(self, card: ContactCard) -> bool:
        return await self._put_contact(card, only_seed=True)

    async def put_contact_admin(self, card: ContactCard) -> None:
        await self._put_contact(
            ContactCard(card.lyceum_id, card.phones, card.telegram, SOURCE_ADMIN), only_seed=False
        )

    async def plan_for(self, lyceum_ids: list[UUID]) -> list[PlanRow]:
        if not lyceum_ids:
            return []
        latest = (
            select(AdmissionPlanRow.lyceum_id, func.max(AdmissionPlanRow.year).label("year"))
            .where(AdmissionPlanRow.lyceum_id.in_(lyceum_ids))
            .group_by(AdmissionPlanRow.lyceum_id)
            .subquery()
        )
        rows = await self._s.scalars(
            select(AdmissionPlanRow)
            .join(
                latest,
                and_(
                    AdmissionPlanRow.lyceum_id == latest.c.lyceum_id,
                    AdmissionPlanRow.year == latest.c.year,
                ),
            )
            .order_by(AdmissionPlanRow.direction_code, AdmissionPlanRow.language_name)
        )
        return [_plan(r) for r in rows]

    async def contacts_for(self, lyceum_ids: list[UUID]) -> dict[UUID, ContactCard]:
        if not lyceum_ids:
            return {}
        rows = await self._s.scalars(
            select(LyceumContactRow).where(LyceumContactRow.lyceum_id.in_(lyceum_ids))
        )
        return {
            r.lyceum_id: ContactCard(r.lyceum_id, tuple(r.phones or ()), r.telegram, r.source)
            for r in rows
        }

    async def stat_rows(self, lyceum_ids: list[UUID]) -> list[tuple[UUID, int, str, int]]:
        if not lyceum_ids:
            return []
        rows = await self._s.execute(
            select(
                YearlyStatRow.lyceum_id,
                YearlyStatRow.year,
                YearlyStatRow.speciality_code,
                YearlyStatRow.applications,
            ).where(YearlyStatRow.lyceum_id.in_(lyceum_ids))
        )
        return [(r.lyceum_id, r.year, r.speciality_code, r.applications) for r in rows]
