"""DB test: joining a new league week settles the previous one first, so the user lands in the
post-settlement tier; week boundaries follow Asia/Tashkent via occurred_at.

Runs against DATABASE_URL inside a rolled-back transaction; skipped when no DB is reachable.
"""

import os
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.modules.gamification.application.service import GamificationService
from app.modules.gamification.infrastructure import orm
from app.modules.gamification.infrastructure.repositories import (
    SqlConfigRepository,
    SqlLeagueRepository,
    SqlRewardsRepository,
    SqlSocialRepository,
    SqlStatsRepository,
)
from app.modules.gamification.ports import Tier
from app.shared.entitlements import entitlements_for

URL = os.environ.get("DATABASE_URL", "")
pytestmark = pytest.mark.skipif(not URL.startswith("postgresql"), reason="needs Postgres")

OLD_WEEK = date(2031, 1, 6)  # Monday
NEW_WEEK = date(2031, 1, 13)  # Monday
TIERS = [Tier(i, f"t{i}", {"en": f"T{i}"}, 30, 1, 1) for i in range(3)]


class _NoProfile:
    async def get(self, _user_id: UUID):  # noqa: ANN202
        return None


def _service(s: AsyncSession, now: datetime) -> GamificationService:
    return GamificationService(
        SqlStatsRepository(s),
        SqlRewardsRepository(s),
        SqlLeagueRepository(s),
        SqlSocialRepository(s),
        SqlConfigRepository(s),
        _NoProfile(),
        entitlements_for,
        now=lambda: now,
    )


async def _seed_last_week(s: AsyncSession, tier: int) -> tuple[UUID, UUID, UUID]:
    """Cohort at `tier` for OLD_WEEK: top (100xp), mid (50xp), bottom (10xp). Returns the ids."""
    await SqlLeagueRepository(s).replace_tiers(TIERS)
    cohort = uuid4()
    s.add(orm.LeagueCohortRow(id=cohort, week_start=OLD_WEEK, tier_idx=tier))
    await s.flush()
    ids = (uuid4(), uuid4(), uuid4())
    stats = SqlStatsRepository(s)
    now = datetime(2031, 1, 7, tzinfo=UTC)
    for order, (uid, xp) in enumerate(zip(ids, (100, 50, 10), strict=True)):
        st = await stats.get_or_create(uid, now, 5)
        st.league_tier = tier
        await stats.save(st)
        s.add(
            orm.LeagueMemberRow(
                cohort_id=cohort, user_id=uid, week_start=OLD_WEEK, xp=xp, joined_order=order
            )
        )
    await s.flush()
    return ids


async def _guard(conn) -> None:  # noqa: ANN001
    for table in ("league_members", "league_cohorts", "league_tiers", "user_stats"):
        if not await conn.run_sync(
            lambda c, t=table: c.dialect.has_table(c, t, schema="gamification")
        ):
            pytest.skip("gamification schema not migrated")


@pytest.mark.parametrize(
    ("who", "expected_tier"),
    [(0, 2), (1, 1), (2, 0)],
    ids=["top-promoted", "middle-stays", "bottom-demoted"],
)
async def test_new_week_joins_at_post_settlement_tier(who: int, expected_tier: int):
    engine = create_async_engine(URL)
    try:
        async with engine.connect() as conn:
            tx = await conn.begin()
            await _guard(conn)
            s = AsyncSession(bind=conn, expire_on_commit=False)
            ids = await _seed_last_week(s, tier=1)
            user = ids[who]

            svc = _service(s, datetime(2031, 1, 14, 6, 0, tzinfo=UTC))
            stats = await SqlStatsRepository(s).get_or_create(
                user, datetime(2031, 1, 14, tzinfo=UTC), 5
            )
            assert stats.league_tier == 1, "precondition: user still at last week's tier"

            await svc._league_xp(stats, NEW_WEEK, 40)

            league = SqlLeagueRepository(s)
            old = await league.membership(user, OLD_WEEK)
            new = await league.membership(user, NEW_WEEK)
            assert old is not None
            assert old.xp == (100, 50, 10)[who], "last week's xp must stay untouched"
            assert new is not None, "user did not join the new week"
            assert new.xp == 40
            assert stats.league_tier == expected_tier, (
                f"in-memory tier {stats.league_tier}, expected post-settlement {expected_tier}"
            )
            assert new.tier_idx == expected_tier, (
                f"joined tier {new.tier_idx} in the new week; expected {expected_tier} "
                "(previous week must be settled before choosing the cohort)"
            )
            cohort = await s.get(orm.LeagueCohortRow, old.cohort_id)
            assert cohort is not None and cohort.settled, "previous cohort not settled"
            await tx.rollback()
    finally:
        await engine.dispose()


async def test_tashkent_midnight_boundary_uses_occurred_at():
    engine = create_async_engine(URL)
    try:
        async with engine.connect() as conn:
            tx = await conn.begin()
            await _guard(conn)
            s = AsyncSession(bind=conn, expire_on_commit=False)
            ids = await _seed_last_week(s, tier=1)
            top, bottom = ids[0], ids[2]
            # Handled long after both events (Tue 06:00 UTC of the new week).
            svc = _service(s, datetime(2031, 1, 14, 6, 0, tzinfo=UTC))
            league = SqlLeagueRepository(s)

            # Sun 2031-01-12 19:30 UTC == Mon 2031-01-13 00:30 Tashkent: the NEW week, although
            # the UTC calendar date still says Sunday (old week).
            after = datetime(2031, 1, 12, 19, 30, tzinfo=UTC)
            await svc.on_session_completed(uuid4(), top, "s-top", "drill", 10, 5, 5, after)
            new = await league.membership(top, NEW_WEEK)
            assert new is not None and new.xp > 0, (
                "00:30 Tashkent Monday must credit the new week (UTC date is still Sunday)"
            )
            assert new.tier_idx == 2, f"promoted user joined tier {new.tier_idx}, expected 2"
            old = await league.membership(top, OLD_WEEK)
            assert old is not None and old.xp == 100, "old week must not receive the xp"

            # Sun 2031-01-12 18:30 UTC == 23:30 Tashkent Sunday: the OLD week, but that cohort
            # was settled above (top's join). A late event must not vanish into a settled week:
            # it is clamped to the current week.
            before = datetime(2031, 1, 12, 18, 30, tzinfo=UTC)
            await svc.on_session_completed(uuid4(), bottom, "s-bot", "drill", 10, 5, 5, before)
            old_b = await league.membership(bottom, OLD_WEEK)
            assert old_b is not None and old_b.xp == 10, "settled week must not receive xp"
            new_b = await league.membership(bottom, NEW_WEEK)
            assert new_b is not None and new_b.xp > 0, "late xp must count in the current week"
            assert new_b.tier_idx == 0, "bottom user joins at the demoted tier"
            await tx.rollback()
    finally:
        await engine.dispose()
