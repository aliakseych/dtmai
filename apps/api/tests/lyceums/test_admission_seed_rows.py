"""Seed plan rows: re-matching releases the old lyceum's rows; admin deletions are tombstoned."""

from uuid import UUID, uuid4

import pytest

from app.modules.lyceums.application.admission import AdmissionService, SeedDocs
from app.modules.lyceums.domain.admission import (
    KIND_PLAN,
    SOURCE_ADMIN,
    SOURCE_SEED,
    ContactCard,
    PlanRow,
    Seats,
    SeedDirection,
    SeedPlanEntry,
)
from app.shared.errors import NotFound

A, B = uuid4(), uuid4()
SEED = SeedDocs(
    plan_year=2026,
    plan=(
        SeedPlanEntry(
            ref=1,
            name="One",
            directions=(SeedDirection("5110100", None, Seats(uz=10, ru=0, qq=0)),),
        ),
    ),
    contacts=(),
)


class FakeStore:
    def __init__(self) -> None:
        self.rows: dict[tuple[UUID, int, str, str], PlanRow] = {}
        self.tombstones: set[tuple[UUID, int, str, str]] = set()
        self._matches: dict[int, tuple[UUID | None, str]] = {}

    @staticmethod
    def _k(lid: UUID, year: int, code: str, lang: str | None) -> tuple[UUID, int, str, str]:
        return (lid, year, code, lang or "")

    async def lyceum_names(self) -> dict[UUID, str]:
        return {A: "A", B: "B"}

    async def matches(self, kind: str) -> dict[int, tuple[UUID | None, str]]:
        return dict(self._matches)

    async def save_match(self, kind: str, ref: int, lyceum_id: UUID | None, source: str) -> None:
        self._matches[ref] = (lyceum_id, source)

    async def upsert_plan_seed(self, row: PlanRow) -> bool:
        key = self._k(row.lyceum_id, row.year, row.direction_code, row.language_name)
        if key in self.rows and self.rows[key].source != SOURCE_SEED:
            return False
        self.rows[key] = row
        return True

    async def delete_plan(self, lid: UUID, year: int, code: str, lang: str | None) -> str | None:
        row = self.rows.pop(self._k(lid, year, code, lang), None)
        return row.source if row else None

    async def tombstone_plan(self, lid: UUID, year: int, code: str, lang: str | None) -> None:
        self.tombstones.add(self._k(lid, year, code, lang))

    async def is_plan_tombstoned(self, lid: UUID, year: int, code: str, lang: str | None) -> bool:
        return self._k(lid, year, code, lang) in self.tombstones

    async def delete_seed_plan(
        self, lid: UUID, year: int, keys: list[tuple[str, str | None]]
    ) -> None:
        for code, lang in keys:
            key = self._k(lid, year, code, lang)
            if key in self.rows and self.rows[key].source == SOURCE_SEED:
                del self.rows[key]

    async def delete_seed_contact(self, lid: UUID) -> None:
        return None

    async def upsert_contact_seed(self, card: ContactCard) -> bool:
        return True

    async def put_plan_admin(self, row: PlanRow) -> None:
        self.rows[self._k(row.lyceum_id, row.year, row.direction_code, row.language_name)] = row


def _svc() -> tuple[AdmissionService, FakeStore]:
    store = FakeStore()
    return AdmissionService(store, lambda: SEED), store  # type: ignore[arg-type]


async def test_rematch_removes_previous_lyceums_seed_rows() -> None:
    svc, store = _svc()
    await svc.set_match(KIND_PLAN, 1, A)
    assert {k[0] for k in store.rows} == {A}
    await svc.set_match(KIND_PLAN, 1, B)
    assert {k[0] for k in store.rows} == {B}
    await svc.set_match(KIND_PLAN, 1, None)
    assert store.rows == {}


async def test_rematch_keeps_admin_edited_rows() -> None:
    svc, store = _svc()
    await svc.set_match(KIND_PLAN, 1, A)
    await svc.put_plan_row(A, 2026, "5110100", None, 99, 0, 0)
    assert store.rows[(A, 2026, "5110100", "")].source == SOURCE_ADMIN
    await svc.set_match(KIND_PLAN, 1, B)
    assert (A, 2026, "5110100", "") in store.rows


async def test_admin_deleted_seed_row_is_not_reimported() -> None:
    svc, store = _svc()
    await svc.set_match(KIND_PLAN, 1, A)
    await svc.delete_plan_row(A, 2026, "5110100", None)
    assert store.rows == {}
    report = await svc.import_seed()  # re-run of the seed import
    assert store.rows == {}
    assert report.plan_rows_written == 0 and report.skipped_deleted == 1
    await svc.set_match(KIND_PLAN, 1, A)  # re-pointing at the same lyceum does not resurrect it
    assert store.rows == {}


async def test_deleting_an_admin_row_leaves_no_tombstone() -> None:
    svc, store = _svc()
    await svc.put_plan_row(A, 2026, "5110100", None, 5, 0, 0)
    await svc.delete_plan_row(A, 2026, "5110100", None)
    assert store.tombstones == set()


async def test_deleting_a_missing_row_raises() -> None:
    svc, _ = _svc()
    with pytest.raises(NotFound):
        await svc.delete_plan_row(A, 2026, "5110100", None)
