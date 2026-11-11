from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.domain.click import (
    ACTION_COMPLETE,
    ClickError,
    ClickOutcome,
    ClickRequest,
    Invoice,
    handle_click,
)
from app.modules.billing.domain.plans import (
    FREE_PLAN_CODE,
    GrantSource,
    Plan,
    Subscription,
    add_months,
    resolve_entitlements,
)
from app.modules.billing.ports import (
    InvoiceRepository,
    PaymentProvider,
    PlanRepository,
    SubscriptionRepository,
)
from app.modules.billing.settings import BillingSettings
from app.shared.entitlements import Entitlements
from app.shared.errors import Conflict, NotFound, ValidationFailed
from app.shared.events import Event, publish
from app.shared.ids import new_id


@dataclass(frozen=True, slots=True)
class MyBilling:
    entitlements: Entitlements
    subscription: Subscription | None  # the subscription that currently provides the plan


class BillingService:
    def __init__(
        self,
        session: AsyncSession,
        plans: PlanRepository,
        subs: SubscriptionRepository,
        invoices: InvoiceRepository,
        provider: PaymentProvider,
        settings: BillingSettings,
    ) -> None:
        self._session = session
        self._plans = plans
        self._subs = subs
        self._invoices = invoices
        self._provider = provider
        self._settings = settings

    # --- plans (admin CRUD) -------------------------------------------------
    async def list_plans(self, *, active_only: bool) -> list[Plan]:
        return await self._plans.list(active_only=active_only)

    async def create_plan(self, plan: Plan) -> Plan:
        if await self._plans.get(plan.code):
            raise Conflict("plan code already exists", code="plan_exists")
        await self._plans.add(plan)
        return plan

    async def update_plan(self, code: str, **changes: Any) -> Plan:
        plan = await self._plans.get(code)
        if plan is None:
            raise NotFound("plan not found", code="plan_not_found")
        for key, value in changes.items():
            setattr(plan, key, value)
        plan.validate()
        await self._plans.save(plan)
        return plan

    async def delete_plan(self, code: str) -> None:
        if code == FREE_PLAN_CODE:
            raise Conflict("the free plan cannot be deleted", code="free_plan_protected")
        if await self._plans.get(code) is None:
            raise NotFound("plan not found", code="plan_not_found")
        if await self._plans.has_references(code):
            raise Conflict("plan is used by subscriptions; deactivate it instead", code="plan_in_use")
        await self._plans.delete(code)

    # --- entitlements -------------------------------------------------------
    async def my_billing(self, user_id: UUID, now: datetime | None = None) -> MyBilling:
        now = now or datetime.now(UTC)
        subs = await self._subs.for_user(user_id)
        plans = await self._plans.all_by_code()
        ent = resolve_entitlements(subs, plans, now)
        current = next((s for s in subs if s.is_active(now) and s.plan_code == ent.plan_code), None)
        return MyBilling(ent, current)

    async def grant(
        self,
        user_id: UUID,
        plan_code: str,
        *,
        months: int | None = None,
        until: datetime | None = None,
        source: GrantSource = GrantSource.ADMIN,
        invoice_id: UUID | None = None,
        now: datetime | None = None,
    ) -> Subscription:
        """Grant/extend a plan; prepaid periods stack. Publishes EntitlementGranted."""
        now = now or datetime.now(UTC)
        plan = await self._plans.get(plan_code)
        if plan is None or plan.is_free:
            raise NotFound("paid plan not found", code="plan_not_found")
        if (months is None) == (until is None):
            raise ValidationFailed("give exactly one of months or until", code="invalid_grant")
        if until is not None and until <= now:
            raise ValidationFailed("until must be in the future", code="invalid_grant")
        existing = await self._subs.active_for_user(user_id, plan_code, now)
        if existing is not None:
            if months is not None:
                existing.extend(months, now)
            elif until is not None:
                existing.until = max(existing.until, until)
            existing.source = source
            await self._subs.save(existing)
            sub = existing
        else:
            sub = Subscription(
                id=new_id(), user_id=user_id, plan_code=plan_code, started_at=now,
                until=until if until is not None else add_months(now, months or 0),
                source=source, invoice_id=invoice_id,
            )
            await self._subs.add(sub)
        await publish(
            self._session,
            Event(
                "EntitlementGranted",
                {"user_id": str(user_id), "plan_code": plan_code, "until": sub.until.isoformat()},
            ),
        )
        return sub

    async def revoke(self, subscription_id: UUID, now: datetime | None = None) -> Subscription:
        sub = await self._subs.get(subscription_id)
        if sub is None:
            raise NotFound("subscription not found", code="subscription_not_found")
        sub.revoke(now or datetime.now(UTC))
        await self._subs.save(sub)
        return sub

    async def user_subscriptions(self, user_id: UUID) -> list[Subscription]:
        return await self._subs.for_user(user_id)

    # --- payments -----------------------------------------------------------
    def ensure_payments_enabled(self) -> None:
        if not self._settings.payments_enabled:
            raise NotFound("payments are not available", code="payments_disabled")

    async def checkout(self, user_id: UUID, plan_code: str) -> tuple[Invoice, str]:
        self.ensure_payments_enabled()
        plan = await self._plans.get(plan_code)
        if plan is None or not plan.active or plan.is_free:
            raise NotFound("plan not found", code="plan_not_found")
        invoice = await self._invoices.create(
            user_id=user_id, plan_code=plan.code, period_months=plan.period_months,
            amount_uzs=plan.price_uzs,
        )
        return invoice, self._provider.checkout_url(invoice)

    async def process_click(self, raw: dict[str, str], now: datetime | None = None) -> dict[str, Any]:
        """One Click prepare/complete callback; always answers with a Click error envelope."""
        self.ensure_payments_enabled()
        now = now or datetime.now(UTC)
        try:
            req = ClickRequest.parse(raw)
        except ValidationFailed:
            return _envelope(raw, None, ClickOutcome(ClickError.BAD_REQUEST))
        invoice: Invoice | None = None
        try:
            invoice = await self._invoices.get(UUID(req.merchant_trans_id), for_update=True)
        except ValueError:
            invoice = None
        outcome = handle_click(
            req, invoice,
            secret=self._settings.click_secret_key, service_id=self._settings.click_service_id,
            now=now,
        )
        if invoice is not None and outcome.error in (ClickError.SUCCESS, ClickError.TRANSACTION_CANCELED):
            await self._invoices.save(invoice)
        if outcome.paid and invoice is not None:
            await self.grant(
                invoice.user_id, invoice.plan_code, months=invoice.period_months,
                source=GrantSource.CLICK, invoice_id=invoice.id, now=now,
            )
        return _envelope(raw, invoice, outcome, complete=req.action == str(ACTION_COMPLETE))


def _envelope(
    raw: dict[str, str], invoice: Invoice | None, outcome: ClickOutcome, *, complete: bool = False
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "click_trans_id": raw.get("click_trans_id", ""),
        "merchant_trans_id": raw.get("merchant_trans_id", ""),
        "error": int(outcome.error),
        "error_note": outcome.note,
    }
    if invoice is not None:
        body["merchant_prepare_id"] = invoice.seq
        if complete:
            body["merchant_confirm_id"] = invoice.seq
    return body
