import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.__main__ import trusted_proxies
from app.interfaces.http.v1.billing import GrantIn
from app.modules.billing.application.service import BillingService
from app.modules.billing.domain.plans import (
    FREE_WHILE_PAYMENTS_OFF,
    GrantSource,
    PaymentsMisconfigured,
    Plan,
    Subscription,
)
from app.modules.billing.ports import GrantTarget
from app.modules.billing.settings import BillingSettings
from app.shared.errors import Conflict, Forbidden, NotFound

NOW = datetime(2026, 11, 11, 12, 0, tzinfo=UTC)
NAMES = {"uz-Latn": "a", "uz-Cyrl": "б", "ru": "в", "en": "d"}


class Plans:
    def __init__(self, *plans: Plan) -> None:
        self.by = {p.code: p for p in plans}

    async def get(self, code: str) -> Plan | None:
        return self.by.get(code)

    async def all_by_code(self) -> dict[str, Plan]:
        return dict(self.by)


class Subs:
    def __init__(self) -> None:
        self.rows: list[Subscription] = []
        self.locks: list[tuple[UUID, str]] = []
        self.saved: list[Subscription] = []

    async def lock(self, user_id: UUID, plan_code: str) -> None:
        self.locks.append((user_id, plan_code))

    async def active_for_user(
        self, user_id: UUID, plan_code: str, now: datetime
    ) -> Subscription | None:
        return next(
            (
                s
                for s in self.rows
                if s.user_id == user_id and s.plan_code == plan_code and s.is_active(now)
            ),
            None,
        )

    async def add(self, sub: Subscription) -> None:
        self.rows.append(sub)

    async def save(self, sub: Subscription) -> None:
        self.saved.append(sub)

    async def for_user(self, user_id: UUID) -> list[Subscription]:
        return [s for s in self.rows if s.user_id == user_id]


class Provider:
    name = "fake"

    def checkout_url(self, invoice: Any) -> str:
        return "https://pay"


class Invoices:
    def __init__(self) -> None:
        self.created = 0

    async def create(self, **kw: Any) -> Any:
        self.created += 1
        return object()


class Targets:
    def __init__(self, target: GrantTarget | None) -> None:
        self.target = target

    async def get(self, user_id: UUID) -> GrantTarget | None:
        return self.target


def make(
    *,
    enabled: bool = True,
    secret: str = "s",
    plans: Plans | None = None,
    target: GrantTarget | None = GrantTarget(disabled=False, guest=False),
) -> tuple[BillingService, Subs, Invoices]:
    free = Plan("free", NAMES, 0)
    paid = Plan("pro", NAMES, 49000, features=frozenset({"ai_tutor"}))
    subs, invoices = Subs(), Invoices()
    svc = BillingService(
        None,  # type: ignore[arg-type]
        plans or Plans(free, paid),
        subs,
        invoices,
        Provider(),  # type: ignore[arg-type]
        BillingSettings(payments_enabled=enabled, click_secret_key=secret, click_service_id="1"),
        Targets(target),
    )
    return svc, subs, invoices


@pytest.fixture(autouse=True)
def _no_events(monkeypatch: pytest.MonkeyPatch) -> None:
    async def noop(*_a: Any, **_k: Any) -> None:
        return None

    monkeypatch.setattr("app.modules.billing.application.service.publish", noop)


def test_click_refused_when_secret_empty() -> None:
    svc, _, _ = make(secret="")
    with pytest.raises(PaymentsMisconfigured) as e:
        asyncio.run(svc.process_click({}))
    assert e.value.status == 503


def test_grant_locks_user_and_plan() -> None:
    svc, subs, _ = make()
    uid = uuid4()
    asyncio.run(svc.grant(uid, "pro", months=1, now=NOW))
    assert subs.locks == [(uid, "pro")]


def test_guest_checkout_forbidden() -> None:
    svc, _, invoices = make()
    with pytest.raises(Forbidden):
        asyncio.run(svc.checkout(uuid4(), "pro", is_guest=True))
    assert invoices.created == 0


def test_click_grant_survives_zero_price_plan() -> None:
    zeroed = Plan("pro", NAMES, 0)
    svc, subs, _ = make(plans=Plans(Plan("free", NAMES, 0), zeroed))
    sub = asyncio.run(
        svc.grant(uuid4(), "pro", months=1, source=GrantSource.CLICK, invoice_id=uuid4(), now=NOW)
    )
    assert sub.source is GrantSource.CLICK and subs.rows == [sub]


def test_admin_grant_still_rejects_free_plan() -> None:
    from app.shared.errors import NotFound

    svc, _, _ = make(plans=Plans(Plan("free", NAMES, 0), Plan("pro", NAMES, 0)))
    with pytest.raises(NotFound):
        asyncio.run(svc.grant(uuid4(), "pro", months=1, now=NOW))


def test_grant_in_requires_aware_until() -> None:
    with pytest.raises(ValidationError):
        GrantIn(user_id=uuid4(), plan_code="pro", until="2026-12-31T23:59:59")  # type: ignore[arg-type]
    ok = GrantIn(user_id=uuid4(), plan_code="pro", until="2026-12-31T23:59:59+05:00")  # type: ignore[arg-type]
    assert ok.until is not None and ok.until.tzinfo is not None


def test_renewal_by_click_overwrites_source() -> None:
    svc, subs, _ = make()
    uid = uuid4()
    asyncio.run(svc.grant(uid, "pro", months=1, source=GrantSource.ADMIN, now=NOW))
    renewed = asyncio.run(
        svc.grant(uid, "pro", months=1, source=GrantSource.CLICK, now=NOW + timedelta(days=1))
    )
    assert renewed.source is GrantSource.CLICK and subs.saved == [renewed]


def test_my_billing_includes_free_features_when_payments_off() -> None:
    svc, _, _ = make(enabled=False, secret="")
    mine = asyncio.run(svc.my_billing(uuid4(), NOW))
    assert FREE_WHILE_PAYMENTS_OFF <= mine.entitlements.features
    svc_on, _, _ = make(enabled=True)
    assert (
        not FREE_WHILE_PAYMENTS_OFF
        & asyncio.run(svc_on.my_billing(uuid4(), NOW)).entitlements.features
    )


def test_subscription_repo_persists_source() -> None:
    import inspect

    from app.modules.billing.infrastructure.repositories import SqlSubscriptionRepository

    assert "row.source" in inspect.getsource(SqlSubscriptionRepository.save)


def test_trusted_proxies_never_wildcard() -> None:
    assert trusted_proxies({"FORWARDED_ALLOW_IPS": "10.0.0.2"}) == "10.0.0.2"
    with pytest.raises(SystemExit):
        trusted_proxies({"FORWARDED_ALLOW_IPS": "*"})
    assert trusted_proxies({}) != "*"


def test_nginx_click_location_matches_real_path() -> None:
    from pathlib import Path

    conf = (
        Path(__file__).resolve().parents[4] / "deploy/nginx/sites/api.dtm-ai.uz.conf"
    ).read_text()
    assert "location /v1/billing/click/" in conf
    assert "$proxy_add_x_forwarded_for" not in conf


def test_admin_grant_refused_for_disabled_user() -> None:
    svc, subs, _ = make(target=GrantTarget(disabled=True, guest=False))
    with pytest.raises(Conflict) as exc:
        asyncio.run(svc.admin_grant(uuid4(), "pro", months=1))
    assert exc.value.code == "user_disabled"
    assert subs.saved == [] and subs.rows == []


def test_admin_grant_unknown_user() -> None:
    svc, _, _ = make(target=None)
    with pytest.raises(NotFound):
        asyncio.run(svc.admin_grant(uuid4(), "pro", months=1))


def test_admin_grant_warns_for_guest() -> None:
    svc, _, _ = make(target=GrantTarget(disabled=False, guest=True))
    _, warnings = asyncio.run(svc.admin_grant(uuid4(), "pro", months=1))
    assert warnings == ["guest_account"]


def test_admin_grant_no_warning_for_regular_user() -> None:
    svc, _, _ = make()
    _, warnings = asyncio.run(svc.admin_grant(uuid4(), "pro", months=1))
    assert warnings == []
