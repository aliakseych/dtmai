"""DB tests: league settlement never takes cross-user stats locks (no deadlock), clamps late
events, and refuses to drop tiers that still have open cohorts.

The concurrency test commits real rows (two sessions) and cleans up after itself.
"""

import asyncio
import os
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.modules.gamification.infrastructure import orm
from app.modules.gamification.infrastructure.repositories import (
    SqlLeagueRepository,
    SqlStatsRepository,
)
from app.modules.gamification.ports import Tier
from app.shared.errors import ValidationFailed
from tests.gamification.test_league_settlement_db import (
    NEW_WEEK,
    OLD_WEEK,
    TIERS,
    _guard,
    _seed_last_week,
    _service,
)

URL = os.environ.get("DATABASE_URL", "")
pytestmark = pytest.mark.skipif(not URL.startswith("postgresql"), reason="needs Postgres")

NOW = datetime(2031, 1, 14, 6, 0, tzinfo=UTC)


async def test_rollover_settles_per_cohort_without_touching_stats():
    engine = create_async_engine(URL)
    try:
        async with engine.connect() as conn:
            tx = await conn.begin()
            await _guard(conn)
            s = AsyncSession(bind=conn, expire_on_commit=False)
            ids = await _seed_last_week(s, tier=1)
            svc = _service(s, NOW)
            assert await svc.rollover() >= 1
            stats = await SqlStatsRepository(s).get_or_create(ids[0], NOW, 5)
            assert stats.league_tier == 1, "settlement must not rewrite user_stats"
            m = await SqlLeagueRepository(s).membership(ids[0], OLD_WEEK)
            assert m is not None and m.settled and m.outcome == "promoted"
            assert await svc.rollover() == 0
            await tx.rollback()
    finally:
        await engine.dispose()


async def test_late_event_in_settled_week_counts_in_current_week():
    engine = create_async_engine(URL)
    try:
        async with engine.connect() as conn:
            tx = await conn.begin()
            await _guard(conn)
            s = AsyncSession(bind=conn, expire_on_commit=False)
            ids = await _seed_last_week(s, tier=1)
            svc = _service(s, NOW)
            await svc.rollover()
            stats = await SqlStatsRepository(s).get_or_create(ids[1], NOW, 5)
            await svc._league_xp(stats, OLD_WEEK, 7)
            league = SqlLeagueRepository(s)
            old = await league.membership(ids[1], OLD_WEEK)
            new = await league.membership(ids[1], NEW_WEEK)
            assert old is not None and old.xp == 50
            assert new is not None and new.xp == 7
            await tx.rollback()
    finally:
        await engine.dispose()


async def test_shrinking_tiers_rejected_with_open_cohorts_and_index_clamped():
    engine = create_async_engine(URL)
    try:
        async with engine.connect() as conn:
            tx = await conn.begin()
            await _guard(conn)
            s = AsyncSession(bind=conn, expire_on_commit=False)
            ids = await _seed_last_week(s, tier=2)  # unsettled cohort at tier 2
            svc = _service(s, NOW)
            with pytest.raises(ValidationFailed):
                await svc.set_tiers(TIERS[:2])
            # Direct shrink (e.g. legacy data): settlement and views clamp instead of crashing.
            await SqlLeagueRepository(s).replace_tiers(TIERS[:2])
            assert await svc.rollover() >= 1
            stats = await SqlStatsRepository(s).get_or_create(ids[0], NOW, 5)
            await svc._league_xp(stats, NEW_WEEK, 5)
            assert stats.league_tier == 1
            await tx.rollback()
    finally:
        await engine.dispose()


async def test_concurrent_lazy_settlement_does_not_deadlock():
    engine = create_async_engine(URL, pool_size=4)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    cohort = uuid4()
    users: list[UUID] = [uuid4(), uuid4()]
    saved: list[Tier] = []
    try:
        async with engine.connect() as conn:
            await _guard(conn)
        async with maker() as s:
            saved = await SqlLeagueRepository(s).tiers()
            await SqlLeagueRepository(s).replace_tiers(TIERS)
            s.add(orm.LeagueCohortRow(id=cohort, week_start=OLD_WEEK, tier_idx=1))
            await s.flush()
            stats = SqlStatsRepository(s)
            for order, uid in enumerate(users):
                st = await stats.get_or_create(uid, NOW, 5)
                st.league_tier = 1
                await stats.save(st)
                s.add(
                    orm.LeagueMemberRow(
                        cohort_id=cohort,
                        user_id=uid,
                        week_start=OLD_WEEK,
                        xp=100 - order * 50,
                        joined_order=order,
                    )
                )
            await s.commit()

        async def act(uid: UUID, gate: asyncio.Barrier) -> None:
            async with maker() as s:
                svc = _service(s, NOW)
                st = await SqlStatsRepository(s).get_or_create(uid, NOW, 5)  # locks own row
                await gate.wait()  # both hold their stats lock before touching league rows
                await svc._league_xp(st, NEW_WEEK, 10)
                await SqlStatsRepository(s).save(st)
                await s.commit()

        async def cron() -> None:
            async with maker() as s:
                svc = _service(s, NOW)
                while await svc.settle_next_cohort():
                    await s.commit()
                await s.commit()

        gate = asyncio.Barrier(2)
        await asyncio.wait_for(
            asyncio.gather(act(users[0], gate), act(users[1], gate), cron()), timeout=20
        )

        async with maker() as s:
            league = SqlLeagueRepository(s)
            top = await league.membership(users[0], NEW_WEEK)
            low = await league.membership(users[1], NEW_WEEK)
            assert top is not None and top.tier_idx == 2 and top.xp == 10
            assert low is not None and low.tier_idx == 1 and low.xp == 10
    finally:
        async with maker() as s:
            await s.execute(
                delete(orm.LeagueCohortRow).where(
                    orm.LeagueCohortRow.week_start.in_([OLD_WEEK, NEW_WEEK])
                )
            )
            await s.execute(delete(orm.UserStatsRow).where(orm.UserStatsRow.user_id.in_(users)))
            if saved:
                await SqlLeagueRepository(s).replace_tiers(saved)
            await s.commit()
        await engine.dispose()
