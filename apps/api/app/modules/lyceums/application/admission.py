from collections.abc import Callable
from dataclasses import dataclass, field
from uuid import UUID

from app.modules.lyceums.domain.admission import (
    KIND_CONTACT,
    KIND_PLAN,
    MATCH_ADMIN,
    MATCH_AUTO,
    SOURCE_ADMIN,
    SOURCE_SEED,
    AdmissionCompetition,
    ContactCard,
    PlanRow,
    SeedContactEntry,
    SeedPlanEntry,
    admission_competition,
    normalize_direction_code,
    normalize_language_name,
    normalize_telegram,
    validate_phones,
    validate_seats,
)
from app.modules.lyceums.domain.matching import match_names
from app.modules.lyceums.ports import AdmissionStore
from app.shared.errors import NotFound, ValidationFailed


@dataclass(frozen=True, slots=True)
class SeedDocs:
    plan_year: int
    plan: tuple[SeedPlanEntry, ...]
    contacts: tuple[SeedContactEntry, ...]


@dataclass(frozen=True, slots=True)
class SeedUnmatched:
    kind: str
    ref: int
    name: str
    ambiguous: bool


@dataclass(slots=True)
class ImportReport:
    matched: dict[str, int] = field(default_factory=lambda: {KIND_PLAN: 0, KIND_CONTACT: 0})
    unmatched: list[SeedUnmatched] = field(default_factory=list)
    plan_rows_written: int = 0
    contacts_written: int = 0
    skipped_admin_edits: int = 0
    skipped_deleted: int = 0


@dataclass(frozen=True, slots=True)
class SeedMatchView:
    kind: str
    ref: int
    name: str
    lyceum_id: UUID | None
    lyceum_name: str | None
    source: str | None


@dataclass(frozen=True, slots=True)
class LyceumAdmission:
    plan_year: int | None
    plan: tuple[PlanRow, ...]
    contact: ContactCard | None
    competition: AdmissionCompetition


class AdmissionService:
    def __init__(self, store: AdmissionStore, seed: Callable[[], SeedDocs]) -> None:
        self._store = store
        self._load_seed = seed

    @property
    def _seed(self) -> SeedDocs:
        return self._load_seed()

    # --- seed import --------------------------------------------------------------------
    async def import_seed(self) -> ImportReport:
        report = ImportReport()
        names = await self._store.lyceum_names()
        for kind, entries in self._seed_names().items():
            matches = await self._resolve(kind, entries, names, report)
            report.matched[kind] = len(matches)
            for ref, lyceum_id in matches.items():
                await self._apply(kind, ref, lyceum_id, report)
        return report

    def _seed_names(self) -> dict[str, dict[int, str]]:
        return {
            KIND_PLAN: {e.ref: e.name for e in self._seed.plan},
            KIND_CONTACT: {e.ref: e.name for e in self._seed.contacts},
        }

    async def _resolve(
        self, kind: str, entries: dict[int, str], names: dict[UUID, str], report: ImportReport
    ) -> dict[int, UUID]:
        saved = await self._store.matches(kind)
        manual = {r: m[0] for r, m in saved.items() if m[1] == MATCH_ADMIN and r in entries}
        resolved: dict[int, UUID] = {r: lid for r, lid in manual.items() if lid is not None}
        free_refs = {r: n for r, n in entries.items() if r not in manual}
        free_lyceums = {lid: n for lid, n in names.items() if lid not in set(resolved.values())}
        result = match_names(free_refs, free_lyceums)
        for ref, lyceum_id in result.matched.items():
            resolved[int(ref)] = lyceum_id  # type: ignore[assignment]
            await self._release_if_moved(kind, int(ref), saved, lyceum_id)
            await self._store.save_match(kind, int(ref), lyceum_id, MATCH_AUTO)
        ambiguous = set(result.ambiguous)
        for ref in result.unmatched + result.ambiguous:
            await self._release_if_moved(kind, int(ref), saved, None)
            await self._store.save_match(kind, int(ref), None, MATCH_AUTO)
            report.unmatched.append(
                SeedUnmatched(
                    kind=kind,
                    ref=int(ref),
                    name=entries[int(ref)],  # type: ignore[call-overload]
                    ambiguous=ref in ambiguous,
                )
            )
        return resolved

    async def _release_if_moved(
        self, kind: str, ref: int, saved: dict[int, tuple[UUID | None, str]], new: UUID | None
    ) -> None:
        """A re-matched ref must not leave its seed rows on the previous lyceum."""
        previous = saved.get(ref, (None, ""))[0]
        if previous is None or previous == new:
            return
        if kind == KIND_PLAN:
            entry = next(e for e in self._seed.plan if e.ref == ref)
            await self._store.delete_seed_plan(
                previous,
                self._seed.plan_year,
                [(d.direction_code, d.language_name) for d in entry.directions],
            )
        else:
            await self._store.delete_seed_contact(previous)

    async def _apply(self, kind: str, ref: int, lyceum_id: UUID, report: ImportReport) -> None:
        if kind == KIND_PLAN:
            entry = next(e for e in self._seed.plan if e.ref == ref)
            for d in entry.directions:
                row = PlanRow(
                    lyceum_id=lyceum_id,
                    year=self._seed.plan_year,
                    direction_code=d.direction_code,
                    language_name=d.language_name,
                    seats=d.seats,
                )
                if await self._store.is_plan_tombstoned(
                    lyceum_id, row.year, row.direction_code, row.language_name
                ):
                    report.skipped_deleted += 1
                elif await self._store.upsert_plan_seed(row):
                    report.plan_rows_written += 1
                else:
                    report.skipped_admin_edits += 1
        else:
            contact = next(e for e in self._seed.contacts if e.ref == ref)
            card = ContactCard(
                lyceum_id=lyceum_id, phones=contact.phones, telegram=contact.telegram
            )
            if await self._store.upsert_contact_seed(card):
                report.contacts_written += 1
            else:
                report.skipped_admin_edits += 1

    # --- admin: matching view -----------------------------------------------------------
    async def match_overview(self) -> list[SeedMatchView]:
        names = await self._store.lyceum_names()
        out: list[SeedMatchView] = []
        for kind, entries in self._seed_names().items():
            saved = await self._store.matches(kind)
            for ref, name in entries.items():
                lyceum_id, source = saved.get(ref, (None, None))
                out.append(
                    SeedMatchView(
                        kind=kind,
                        ref=ref,
                        name=name,
                        lyceum_id=lyceum_id,
                        lyceum_name=names.get(lyceum_id) if lyceum_id else None,
                        source=source,
                    )
                )
        return out

    async def set_match(self, kind: str, ref: int, lyceum_id: UUID | None) -> None:
        entries = self._seed_names().get(kind)
        if entries is None or ref not in entries:
            raise NotFound("seed entry not found", code="seed_entry_not_found")
        if lyceum_id is not None and lyceum_id not in await self._store.lyceum_names():
            raise NotFound("lyceum not found", code="lyceum_not_found")
        saved = await self._store.matches(kind)
        await self._release_if_moved(kind, ref, saved, lyceum_id)
        await self._store.save_match(kind, ref, lyceum_id, MATCH_ADMIN)
        if lyceum_id is not None:
            await self._apply(kind, ref, lyceum_id, ImportReport())

    # --- admin: edits -------------------------------------------------------------------
    async def put_plan_row(
        self,
        lyceum_id: UUID,
        year: int,
        direction_code: str,
        language_name: str | None,
        uz: int,
        ru: int,
        qq: int,
    ) -> PlanRow:
        if year < 2000 or year > 2100:
            raise ValidationFailed("year out of range", code="invalid_year")
        await self._require_lyceum(lyceum_id)
        row = PlanRow(
            lyceum_id=lyceum_id,
            year=year,
            direction_code=normalize_direction_code(direction_code),
            language_name=normalize_language_name(language_name),
            seats=validate_seats(uz, ru, qq),
            source=SOURCE_ADMIN,
        )
        await self._store.put_plan_admin(row)
        return row

    async def delete_plan_row(
        self, lyceum_id: UUID, year: int, direction_code: str, language_name: str | None
    ) -> None:
        code = normalize_direction_code(direction_code)
        language = normalize_language_name(language_name)
        source = await self._store.delete_plan(lyceum_id, year, code, language)
        if source is None:
            raise NotFound("plan row not found", code="plan_row_not_found")
        if source == SOURCE_SEED:
            await self._store.tombstone_plan(lyceum_id, year, code, language)

    async def put_contacts(
        self, lyceum_id: UUID, phones: list[str], telegram: str | None
    ) -> ContactCard:
        await self._require_lyceum(lyceum_id)
        card = ContactCard(
            lyceum_id=lyceum_id,
            phones=validate_phones(phones),
            telegram=normalize_telegram(telegram),
            source=SOURCE_ADMIN,
        )
        await self._store.put_contact_admin(card)
        return card

    async def _require_lyceum(self, lyceum_id: UUID) -> None:
        if lyceum_id not in await self._store.lyceum_names():
            raise NotFound("lyceum not found", code="lyceum_not_found")

    # --- read side ----------------------------------------------------------------------
    async def for_lyceums(self, lyceum_ids: list[UUID]) -> dict[UUID, LyceumAdmission]:
        plan = await self._store.plan_for(lyceum_ids)
        contacts = await self._store.contacts_for(lyceum_ids)
        stats = await self._store.stat_rows(lyceum_ids)
        out: dict[UUID, LyceumAdmission] = {}
        for lid in lyceum_ids:
            rows = tuple(r for r in plan if r.lyceum_id == lid)
            competition = admission_competition(
                rows, [(y, c, a) for sl, y, c, a in stats if sl == lid]
            )
            out[lid] = LyceumAdmission(
                plan_year=rows[0].year if rows else None,
                plan=rows,
                contact=contacts.get(lid),
                competition=competition,
            )
        return out
