from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.modules.billing.domain.plans import (
    FALLBACK_FREE,
    Plan,
    Subscription,
    SubscriptionStatus,
    add_months,
    resolve_entitlements,
)
from app.shared.errors import ValidationFailed

NOW = datetime(2026, 11, 11, 12, 0, tzinfo=UTC)
NAMES = {"uz-Latn": "a", "uz-Cyrl": "б", "ru": "в", "en": "d"}


def plan(code: str, price: int, **kw: object) -> Plan:
    return Plan(code=code, names=NAMES, price_uzs=price, **kw)  # type: ignore[arg-type]


PLANS = {
    "free": plan("free", 0, limits={"hearts_max": 5}),
    "premium_1m": plan("premium_1m", 49000, features=frozenset({"ai_tutor"})),
}


def sub(code: str, until: datetime, **kw: object) -> Subscription:
    return Subscription(id=uuid4(), user_id=uuid4(), plan_code=code,
                        started_at=NOW - timedelta(days=1), until=until, **kw)  # type: ignore[arg-type]


def test_plan_validation() -> None:
    with pytest.raises(ValidationFailed):
        plan("Bad Code", 1)
    with pytest.raises(ValidationFailed):
        plan("x", -1)
    with pytest.raises(ValidationFailed):
        plan("x", 1, period_months=2)
    with pytest.raises(ValidationFailed):
        Plan(code="x", names={"en": "only"}, price_uzs=1)
    with pytest.raises(ValidationFailed):
        plan("free", 100)


def test_add_months_clamps_day() -> None:
    assert add_months(datetime(2026, 1, 31, tzinfo=UTC), 1) == datetime(2026, 2, 28, tzinfo=UTC)
    assert add_months(datetime(2026, 11, 11, tzinfo=UTC), 3) == datetime(2027, 2, 11, tzinfo=UTC)
    assert add_months(datetime(2026, 11, 11, tzinfo=UTC), 12) == datetime(2027, 11, 11, tzinfo=UTC)


def test_resolve_free_when_no_subscription() -> None:
    ent = resolve_entitlements([], PLANS, NOW)
    assert ent.plan_code == "free" and ent.limit("hearts_max") == 5 and not ent.has("ai_tutor")


def test_resolve_fallback_without_free_row() -> None:
    assert resolve_entitlements([], {}, NOW) is FALLBACK_FREE


def test_resolve_active_premium_and_expiry() -> None:
    active = sub("premium_1m", NOW + timedelta(days=3))
    assert resolve_entitlements([active], PLANS, NOW).has("ai_tutor")
    expired = sub("premium_1m", NOW - timedelta(seconds=1))
    assert resolve_entitlements([expired], PLANS, NOW).plan_code == "free"
    canceled = sub("premium_1m", NOW + timedelta(days=3), status=SubscriptionStatus.CANCELED)
    assert resolve_entitlements([canceled], PLANS, NOW).plan_code == "free"


def test_unknown_plan_ignored() -> None:
    assert resolve_entitlements([sub("gone", NOW + timedelta(days=1))], PLANS, NOW).plan_code == "free"


def test_prepaid_extension_stacks() -> None:
    s = sub("premium_1m", NOW + timedelta(days=10))
    old = s.until
    s.extend(1, NOW)
    assert s.until == add_months(old, 1)


def test_extension_after_expiry_restarts() -> None:
    s = sub("premium_1m", NOW - timedelta(days=5))
    s.extend(1, NOW)
    assert s.is_active(NOW) and s.until == add_months(NOW, 1) and s.started_at == NOW


def test_revoke() -> None:
    s = sub("premium_1m", NOW + timedelta(days=30))
    s.revoke(NOW)
    assert s.status is SubscriptionStatus.CANCELED and not s.is_active(NOW) and s.until == NOW
