"""Plans, subscriptions and the pure entitlement resolution rules."""

import calendar
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from app.shared.entitlements import Entitlements
from app.shared.errors import DomainError, ValidationFailed

FREE_PLAN_CODE = "free"
# Features granted to everyone while payments are switched off (nothing can be bought).
FREE_WHILE_PAYMENTS_OFF = frozenset({"personal_mock"})
ALLOWED_PERIODS = (1, 3, 12)
LOCALES = ("uz-Latn", "uz-Cyrl", "ru", "en")
# Built-in fallback used only when the admin has deleted/deactivated the `free` row.
FALLBACK_FREE = Entitlements(
    FREE_PLAN_CODE, frozenset(), {"hearts_max": 5, "ai_explanations_per_day": 3}
)


class PaymentsMisconfigured(DomainError):
    status = 503
    code = "payments_misconfigured"


def add_months(moment: datetime, months: int) -> datetime:
    month_index = moment.month - 1 + months
    year, month = moment.year + month_index // 12, month_index % 12 + 1
    day = min(moment.day, calendar.monthrange(year, month)[1])
    return moment.replace(year=year, month=month, day=day)


@dataclass(slots=True)
class Plan:
    code: str
    names: dict[str, str]
    price_uzs: int
    period_months: int = 1
    features: frozenset[str] = frozenset()
    limits: dict[str, int] = field(default_factory=dict)
    active: bool = True
    sort_order: int = 0

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        code = self.code
        if not code or not code.replace("_", "").replace("-", "").isalnum() or code != code.lower():
            raise ValidationFailed(
                "plan code must be lowercase [a-z0-9_-]", code="invalid_plan_code"
            )
        if self.price_uzs < 0:
            raise ValidationFailed("price must be >= 0", code="invalid_price")
        if self.period_months not in ALLOWED_PERIODS:
            raise ValidationFailed("period_months must be 1, 3 or 12", code="invalid_period")
        missing = [loc for loc in LOCALES if not self.names.get(loc, "").strip()]
        if missing:
            raise ValidationFailed(
                f"missing plan names: {', '.join(missing)}", code="invalid_names"
            )
        if self.code == FREE_PLAN_CODE and self.price_uzs != 0:
            raise ValidationFailed("the free plan must cost 0", code="invalid_price")

    @property
    def is_free(self) -> bool:
        return self.price_uzs == 0

    def entitlements(self) -> Entitlements:
        return Entitlements(self.code, frozenset(self.features), dict(self.limits))


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELED = "canceled"


class GrantSource(StrEnum):
    ADMIN = "admin"
    CLICK = "click"


@dataclass(slots=True)
class Subscription:
    id: UUID
    user_id: UUID
    plan_code: str
    started_at: datetime
    until: datetime
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    source: GrantSource = GrantSource.ADMIN
    invoice_id: UUID | None = None

    def is_active(self, now: datetime) -> bool:
        return self.status is SubscriptionStatus.ACTIVE and self.until > now

    def extend(self, months: int, now: datetime) -> None:
        """Prepaid periods stack: a renewal starts when the current period ends."""
        if months <= 0:
            raise ValidationFailed("period must be positive", code="invalid_period")
        base = self.until if self.is_active(now) else now
        if not self.is_active(now):
            self.started_at = now
        self.until = add_months(base, months)
        self.status = SubscriptionStatus.ACTIVE

    def revoke(self, now: datetime) -> None:
        if self.status is SubscriptionStatus.CANCELED:
            return
        self.status = SubscriptionStatus.CANCELED
        self.until = min(self.until, now)


def resolve_entitlements(
    subscriptions: list[Subscription], plans: dict[str, Plan], now: datetime
) -> Entitlements:
    """Best active subscription wins (latest `until`); otherwise the `free` plan row."""
    live = [s for s in subscriptions if s.is_active(now) and s.plan_code in plans]
    if live:
        best = max(live, key=lambda s: s.until)
        return plans[best.plan_code].entitlements()
    free = plans.get(FREE_PLAN_CODE)
    return free.entitlements() if free else FALLBACK_FREE
