from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.domain.click import Invoice, InvoiceStatus
from app.modules.billing.domain.plans import GrantSource, Plan, Subscription, SubscriptionStatus
from app.modules.billing.infrastructure.orm import InvoiceRow, PlanRow, SubscriptionRow
from app.shared.ids import new_id


def _plan(r: PlanRow) -> Plan:
    return Plan(
        code=r.code,
        names=dict(r.names),
        price_uzs=r.price_uzs,
        period_months=r.period_months,
        features=frozenset(r.features or []),
        limits={k: int(v) for k, v in (r.limits or {}).items()},
        active=r.active,
        sort_order=r.sort_order,
    )


def _fill(r: PlanRow, p: Plan) -> None:
    r.names, r.price_uzs, r.period_months = dict(p.names), p.price_uzs, p.period_months
    r.features, r.limits = sorted(p.features), dict(p.limits)
    r.active, r.sort_order = p.active, p.sort_order


class SqlPlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(self, code: str) -> Plan | None:
        row = await self._s.get(PlanRow, code)
        return _plan(row) if row else None

    async def list(self, *, active_only: bool) -> list[Plan]:
        q = select(PlanRow).order_by(PlanRow.sort_order, PlanRow.price_uzs)
        if active_only:
            q = q.where(PlanRow.active.is_(True))
        return [_plan(r) for r in await self._s.scalars(q)]

    async def all_by_code(self) -> dict[str, Plan]:
        return {r.code: _plan(r) for r in await self._s.scalars(select(PlanRow))}

    async def add(self, plan: Plan) -> None:
        row = PlanRow(code=plan.code)
        _fill(row, plan)
        self._s.add(row)
        await self._s.flush()

    async def save(self, plan: Plan) -> None:
        row = await self._s.get(PlanRow, plan.code)
        if row is not None:
            _fill(row, plan)
            await self._s.flush()

    async def delete(self, code: str) -> None:
        row = await self._s.get(PlanRow, code)
        if row is not None:
            await self._s.delete(row)
            await self._s.flush()

    async def has_references(self, code: str) -> bool:
        sub = await self._s.scalar(
            select(SubscriptionRow.id).where(SubscriptionRow.plan_code == code).limit(1)
        )
        inv = await self._s.scalar(
            select(InvoiceRow.id).where(InvoiceRow.plan_code == code).limit(1)
        )
        return sub is not None or inv is not None


def _sub(r: SubscriptionRow) -> Subscription:
    return Subscription(
        id=r.id,
        user_id=r.user_id,
        plan_code=r.plan_code,
        started_at=r.started_at,
        until=r.until,
        status=SubscriptionStatus(r.status),
        source=GrantSource(r.source),
        invoice_id=r.invoice_id,
    )


class SqlSubscriptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(self, subscription_id: UUID) -> Subscription | None:
        row = await self._s.get(SubscriptionRow, subscription_id)
        return _sub(row) if row else None

    async def for_user(self, user_id: UUID) -> list[Subscription]:
        q = (
            select(SubscriptionRow)
            .where(SubscriptionRow.user_id == user_id)
            .order_by(SubscriptionRow.until.desc())
        )
        return [_sub(r) for r in await self._s.scalars(q)]

    async def active_for_user(
        self, user_id: UUID, plan_code: str, now: datetime
    ) -> Subscription | None:
        q = (
            select(SubscriptionRow)
            .where(
                SubscriptionRow.user_id == user_id,
                SubscriptionRow.plan_code == plan_code,
                SubscriptionRow.status == SubscriptionStatus.ACTIVE.value,
                SubscriptionRow.until > now,
            )
            .order_by(SubscriptionRow.until.desc())
            .limit(1)
            .with_for_update()
        )
        row = await self._s.scalar(q)
        return _sub(row) if row else None

    async def lock(self, user_id: UUID, plan_code: str) -> None:
        key = func.hashtextextended(f"billing.grant:{user_id}:{plan_code}", 0)
        await self._s.execute(select(func.pg_advisory_xact_lock(key)))

    async def add(self, sub: Subscription) -> None:
        self._s.add(
            SubscriptionRow(
                id=sub.id,
                user_id=sub.user_id,
                plan_code=sub.plan_code,
                status=sub.status.value,
                source=sub.source.value,
                started_at=sub.started_at,
                until=sub.until,
                invoice_id=sub.invoice_id,
            )
        )
        await self._s.flush()

    async def save(self, sub: Subscription) -> None:
        row = await self._s.get(SubscriptionRow, sub.id)
        if row is not None:
            row.status, row.until, row.started_at = sub.status.value, sub.until, sub.started_at
            row.source = sub.source.value
            await self._s.flush()


def _invoice(r: InvoiceRow) -> Invoice:
    return Invoice(
        id=r.id,
        seq=r.seq,
        user_id=r.user_id,
        plan_code=r.plan_code,
        period_months=r.period_months,
        amount_uzs=r.amount_uzs,
        status=InvoiceStatus(r.status),
        click_trans_id=r.click_trans_id,
        click_paydoc_id=r.click_paydoc_id,
        paid_at=r.paid_at,
        canceled_at=r.canceled_at,
    )


class SqlInvoiceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(
        self, *, user_id: UUID, plan_code: str, period_months: int, amount_uzs: int
    ) -> Invoice:
        row = InvoiceRow(
            id=new_id(),
            user_id=user_id,
            plan_code=plan_code,
            period_months=period_months,
            amount_uzs=amount_uzs,
            status=InvoiceStatus.PENDING.value,
        )
        self._s.add(row)
        await self._s.flush()
        await self._s.refresh(row)  # loads the identity `seq`
        return _invoice(row)

    async def find_open(
        self, *, user_id: UUID, plan_code: str, period_months: int, amount_uzs: int
    ) -> Invoice | None:
        row = await self._s.scalar(
            select(InvoiceRow)
            .where(
                InvoiceRow.user_id == user_id,
                InvoiceRow.plan_code == plan_code,
                InvoiceRow.period_months == period_months,
                InvoiceRow.amount_uzs == amount_uzs,
                InvoiceRow.status == InvoiceStatus.PENDING.value,
                InvoiceRow.click_trans_id.is_(None),
            )
            .order_by(InvoiceRow.created_at.desc())
            .limit(1)
        )
        return _invoice(row) if row else None

    async def get(self, invoice_id: UUID, *, for_update: bool = False) -> Invoice | None:
        q = select(InvoiceRow).where(InvoiceRow.id == invoice_id)
        if for_update:
            q = q.with_for_update()
        row = await self._s.scalar(q)
        return _invoice(row) if row else None

    async def save(self, invoice: Invoice) -> None:
        row = await self._s.get(InvoiceRow, invoice.id)
        if row is not None:
            row.status, row.click_trans_id = invoice.status.value, invoice.click_trans_id
            row.click_paydoc_id, row.paid_at = invoice.click_paydoc_id, invoice.paid_at
            row.canceled_at = invoice.canceled_at
            await self._s.flush()
