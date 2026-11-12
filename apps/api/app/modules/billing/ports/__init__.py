from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.modules.billing.domain.click import Invoice
from app.modules.billing.domain.plans import Plan, Subscription


class PlanRepository(Protocol):
    async def get(self, code: str) -> Plan | None: ...
    async def list(self, *, active_only: bool) -> list[Plan]: ...
    async def all_by_code(self) -> dict[str, Plan]: ...
    async def add(self, plan: Plan) -> None: ...
    async def save(self, plan: Plan) -> None: ...
    async def delete(self, code: str) -> None: ...
    async def has_references(self, code: str) -> bool: ...


class SubscriptionRepository(Protocol):
    async def get(self, subscription_id: UUID) -> Subscription | None: ...
    async def for_user(self, user_id: UUID) -> list[Subscription]: ...
    async def active_for_user(
        self, user_id: UUID, plan_code: str, now: datetime
    ) -> Subscription | None: ...
    async def lock(self, user_id: UUID, plan_code: str) -> None:
        """Serialise grants for one (user, plan) until the transaction ends."""
        ...

    async def add(self, sub: Subscription) -> None: ...
    async def save(self, sub: Subscription) -> None: ...


class InvoiceRepository(Protocol):
    async def create(
        self, *, user_id: UUID, plan_code: str, period_months: int, amount_uzs: int
    ) -> Invoice: ...
    async def find_open(
        self, *, user_id: UUID, plan_code: str, period_months: int, amount_uzs: int
    ) -> Invoice | None:
        """Newest still-pending invoice no Click transaction has touched, for reuse."""
        ...

    async def get(self, invoice_id: UUID, *, for_update: bool = False) -> Invoice | None: ...
    async def save(self, invoice: Invoice) -> None: ...


@dataclass(frozen=True, slots=True)
class GrantTarget:
    disabled: bool
    guest: bool


class GrantTargets(Protocol):
    """Looks up the account an admin is about to grant a plan to (owned by identity)."""

    async def get(self, user_id: UUID) -> GrantTarget | None: ...


class PaymentProvider(Protocol):
    """A payment gateway: builds the pay URL and processes its server callbacks."""

    name: str

    def checkout_url(self, invoice: Invoice) -> str: ...
