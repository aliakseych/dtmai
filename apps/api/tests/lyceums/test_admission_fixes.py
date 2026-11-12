import asyncio
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.interfaces.http.v1.lyceums import ContactCardIn
from app.modules.lyceums.application.admission import AdmissionService, SeedDocs
from app.modules.lyceums.domain.admission import (
    KIND_PLAN,
    MATCH_ADMIN,
    MATCH_AUTO,
    SOURCE_ADMIN,
    SOURCE_SEED,
    PlanRow,
    Seats,
    SeedDirection,
    SeedPlanEntry,
)
from app.modules.lyceums.domain.matching import name_tokens
from app.modules.lyceums.domain.models import validate_year
from app.shared.errors import Conflict, ValidationFailed

LYC_A, LYC_B = uuid4(), uuid4()
DIR = SeedDirection("3910002", None, Seats(10, 0, 0))
SEED = SeedDocs(
    plan_year=2026,
    plan=(SeedPlanEntry(1, "A", (DIR,)), SeedPlanEntry(2, "B", (DIR,))),
    contacts=(),
)


class Store:
    def __init__(self, source: str | None = SOURCE_SEED) -> None:
        self.match: dict[int, tuple[UUID | None, str]] = {}
        self.deleted_source = source
        self.tombstones: list[tuple[UUID, int, str, str | None]] = []
        self.released: list[UUID] = []

    async def lyceum_names(self) -> dict[UUID, str]:
        return {LYC_A: "A", LYC_B: "B"}

    async def matches(self, kind: str) -> dict[int, tuple[UUID | None, str]]:
        return dict(self.match)

    async def save_match(self, kind: str, ref: int, lyceum_id: UUID | None, source: str) -> None:
        self.match[ref] = (lyceum_id, source)

    async def delete_plan(
        self, lyceum_id: UUID, year: int, code: str, lang: str | None
    ) -> str | None:
        return self.deleted_source

    async def tombstone_plan(self, lyceum_id: UUID, year: int, code: str, lang: str | None) -> None:
        self.tombstones.append((lyceum_id, year, code, lang))

    async def delete_seed_plan(self, lyceum_id: UUID, year: int, keys: list) -> None:  # type: ignore[type-arg]
        self.released.append(lyceum_id)

    async def is_plan_tombstoned(self, *a: object) -> bool:
        return False

    async def upsert_plan_seed(self, row: PlanRow) -> bool:
        return True


def svc(store: Store) -> AdmissionService:
    return AdmissionService(store, lambda: SEED)  # type: ignore[arg-type]


def test_delete_of_edited_seed_row_is_tombstoned() -> None:
    store = Store(source=SOURCE_ADMIN)  # an admin edit flipped the source
    store.match[1] = (LYC_A, MATCH_ADMIN)
    asyncio.run(svc(store).delete_plan_row(LYC_A, 2026, "3910002", None))
    assert store.tombstones == [(LYC_A, 2026, "3910002", None)]


def test_delete_of_admin_only_row_is_not_tombstoned() -> None:
    store = Store(source=SOURCE_ADMIN)
    store.match[1] = (LYC_A, MATCH_ADMIN)
    asyncio.run(svc(store).delete_plan_row(LYC_A, 2026, "3910999", None))
    assert store.tombstones == []


def test_set_match_conflicts_with_other_admin_match() -> None:
    store = Store()
    store.match[1] = (LYC_A, MATCH_ADMIN)
    with pytest.raises(Conflict):
        asyncio.run(svc(store).set_match(KIND_PLAN, 2, LYC_A))


def test_set_match_releases_other_auto_match() -> None:
    store = Store()
    store.match[1] = (LYC_A, MATCH_AUTO)
    asyncio.run(svc(store).set_match(KIND_PLAN, 2, LYC_A))
    assert store.match[1] == (None, MATCH_AUTO)
    assert store.match[2] == (LYC_A, MATCH_ADMIN)


def test_validate_year_upper_bound() -> None:
    from datetime import UTC, datetime

    assert validate_year(datetime.now(UTC).year + 1)
    with pytest.raises(ValidationFailed):
        validate_year(datetime.now(UTC).year + 2)
    with pytest.raises(ValidationFailed):
        validate_year(1999)


def test_noise_words_with_x_are_filtered() -> None:
    assert name_tokens("Toshkent ixtisoslashgan litseyi") == name_tokens("Toshkent")


def test_contact_card_phone_cap_matches_domain() -> None:
    ContactCardIn(phones=["+998901234567"] * 8)
    with pytest.raises(ValidationError):
        ContactCardIn(phones=["+998901234567"] * 9)
