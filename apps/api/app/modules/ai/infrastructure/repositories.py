from datetime import timedelta
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.ai.domain.budget import Limits, within_quota
from app.modules.ai.domain.routing import ModelRoute, Task
from app.modules.ai.infrastructure.clock import tashkent_today
from app.modules.ai.infrastructure.orm import LedgerRow, LimitsRow, ModelRouteRow
from app.modules.ai.ports import LedgerEntry, SpendReport, SpendRow
from app.shared.ids import new_id


def _route(r: ModelRouteRow) -> ModelRoute:
    return ModelRoute(
        task=Task(r.task),
        slot=r.slot,
        model=r.model,
        temperature=r.temperature,
        max_tokens=r.max_tokens,
        price_in_micro_per_mtok=r.price_in_micro_per_mtok,
        price_out_micro_per_mtok=r.price_out_micro_per_mtok,
        enabled=r.enabled,
    )


class SqlAIConfigRepository:
    """Each call uses its own short transaction so AI bookkeeping is independent of the request UoW."""

    def __init__(self, maker: async_sessionmaker[AsyncSession]) -> None:
        self._maker = maker

    async def routes_for(self, task: Task) -> list[ModelRoute]:
        async with self._maker() as s:
            rows = await s.scalars(
                select(ModelRouteRow)
                .where(ModelRouteRow.task == task.value, ModelRouteRow.enabled.is_(True))
                .order_by(ModelRouteRow.slot)
            )
            return [_route(r) for r in rows]

    async def all_routes(self) -> list[ModelRoute]:
        async with self._maker() as s:
            rows = await s.scalars(
                select(ModelRouteRow).order_by(ModelRouteRow.task, ModelRouteRow.slot)
            )
            return [_route(r) for r in rows]

    async def upsert_route(self, route: ModelRoute, actor: UUID) -> None:
        values = {
            "task": route.task.value,
            "slot": route.slot,
            "model": route.model,
            "temperature": route.temperature,
            "max_tokens": route.max_tokens,
            "price_in_micro_per_mtok": route.price_in_micro_per_mtok,
            "price_out_micro_per_mtok": route.price_out_micro_per_mtok,
            "enabled": route.enabled,
            "updated_by": actor,
        }
        async with self._maker() as s, s.begin():
            stmt = insert(ModelRouteRow).values(**values)
            await s.execute(
                stmt.on_conflict_do_update(
                    index_elements=["task", "slot"],
                    set_={k: v for k, v in values.items() if k not in ("task", "slot")}
                    | {"updated_at": func.now()},
                )
            )

    async def delete_route(self, task: Task, slot: int) -> bool:
        async with self._maker() as s, s.begin():
            res = await s.execute(
                delete(ModelRouteRow).where(
                    ModelRouteRow.task == task.value, ModelRouteRow.slot == slot
                )
            )
            return bool(res.rowcount)  # type: ignore[attr-defined]

    async def limits(self) -> Limits:
        async with self._maker() as s:
            row = await s.get(LimitsRow, 1)
            if row is None:
                return Limits(True, 0, 0)
            return Limits(row.enabled, row.daily_spend_cap_micro, row.user_daily_token_budget)

    async def set_limits(self, limits: Limits, actor: UUID) -> None:
        values = {
            "id": 1,
            "enabled": limits.enabled,
            "daily_spend_cap_micro": limits.daily_spend_cap_micro,
            "user_daily_token_budget": limits.user_daily_token_budget,
            "updated_by": actor,
        }
        async with self._maker() as s, s.begin():
            stmt = insert(LimitsRow).values(**values)
            await s.execute(
                stmt.on_conflict_do_update(
                    index_elements=["id"],
                    set_={k: v for k, v in values.items() if k != "id"}
                    | {"updated_at": func.now()},
                )
            )


class SqlLedgerRepository:
    def __init__(self, maker: async_sessionmaker[AsyncSession]) -> None:
        self._maker = maker

    async def add(self, entry: LedgerEntry) -> None:
        async with self._maker() as s, s.begin():
            s.add(
                LedgerRow(
                    id=new_id(),
                    day=tashkent_today(),
                    user_id=entry.user_id,
                    purpose=entry.purpose,
                    task=entry.task,
                    model=entry.model,
                    tokens_in=entry.tokens_in,
                    tokens_out=entry.tokens_out,
                    cost_micro=entry.cost_micro,
                    ok=entry.ok,
                    latency_ms=entry.latency_ms,
                    ref=entry.ref,
                    error=entry.error,
                )
            )

    async def spent_today_micro(self) -> int:
        async with self._maker() as s:
            v = await s.scalar(
                select(func.coalesce(func.sum(LedgerRow.cost_micro), 0)).where(
                    LedgerRow.day == tashkent_today()
                )
            )
            return int(v or 0)

    async def user_tokens_today(self, user_id: UUID) -> int:
        async with self._maker() as s:
            v = await s.scalar(
                select(
                    func.coalesce(func.sum(LedgerRow.tokens_in + LedgerRow.tokens_out), 0)
                ).where(LedgerRow.day == tashkent_today(), LedgerRow.user_id == user_id)
            )
            return int(v or 0)

    async def user_calls_today(self, user_id: UUID, purpose: str) -> int:
        async with self._maker() as s:
            v = await s.scalar(
                select(func.count()).where(
                    LedgerRow.day == tashkent_today(),
                    LedgerRow.user_id == user_id,
                    LedgerRow.purpose == purpose,
                    LedgerRow.ok.is_(True),
                )
            )
            return int(v or 0)

    async def spend_report(self, days: int) -> SpendReport:
        since = tashkent_today() - timedelta(days=max(days, 1) - 1)

        async def group(col: object) -> list[SpendRow]:
            async with self._maker() as s:
                rows = await s.execute(
                    select(
                        col,  # type: ignore[call-overload]
                        func.count(),
                        func.coalesce(func.sum(LedgerRow.tokens_in), 0),
                        func.coalesce(func.sum(LedgerRow.tokens_out), 0),
                        func.coalesce(func.sum(LedgerRow.cost_micro), 0),
                    )
                    .where(LedgerRow.day >= since)
                    .group_by(col)
                    .order_by(col)
                )
                return [SpendRow(str(k), int(c), int(i), int(o), int(m)) for k, c, i, o, m in rows]

        return SpendReport(
            by_day=await group(LedgerRow.day),
            by_task=await group(LedgerRow.task),
            by_model=await group(LedgerRow.model),
            by_purpose=await group(LedgerRow.purpose),
        )


class SqlTutorSlotReservations:
    """Reserve = short transaction under a per-user advisory lock that counts and inserts a counted
    `tutor` ledger row. The LLM call (purpose `tutor_llm`) runs afterwards with no lock or connection held."""

    def __init__(self, maker: async_sessionmaker[AsyncSession]) -> None:
        self._maker = maker

    async def reserve(self, user_id: UUID, limit: int) -> UUID | None:
        key = f"tutor:{user_id}"
        async with self._maker() as s, s.begin():
            await s.execute(select(func.pg_advisory_xact_lock(func.hashtextextended(key, 0))))
            used = int(
                await s.scalar(
                    select(func.count()).where(
                        LedgerRow.day == tashkent_today(),
                        LedgerRow.user_id == user_id,
                        LedgerRow.purpose == "tutor",
                        LedgerRow.ok.is_(True),
                    )
                )
                or 0
            )
            if not within_quota(limit, used):
                return None
            rid = new_id()
            s.add(
                LedgerRow(
                    id=rid,
                    day=tashkent_today(),
                    user_id=user_id,
                    purpose="tutor",
                    task="tutor",
                    model="reservation",
                    ok=True,
                )
            )
            return rid

    async def release(self, reservation_id: UUID) -> None:
        async with self._maker() as s, s.begin():
            await s.execute(delete(LedgerRow).where(LedgerRow.id == reservation_id))
