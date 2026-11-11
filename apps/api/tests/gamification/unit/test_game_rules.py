from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest

from app.modules.gamification.domain.hearts import Hearts
from app.modules.gamification.domain.league import (
    Outcome,
    Standing,
    choose_cohort,
    next_tier,
    settle_cohort,
    week_start,
)
from app.modules.gamification.domain.streak import Streak, tashkent_day

HOUR = timedelta(hours=1)
T0 = datetime(2026, 1, 5, 8, 0, tzinfo=UTC)


def test_tashkent_day_boundary() -> None:
    assert tashkent_day(datetime(2026, 1, 1, 18, 59, tzinfo=UTC)) == date(2026, 1, 1)
    assert tashkent_day(datetime(2026, 1, 1, 19, 0, tzinfo=UTC)) == date(2026, 1, 2)
    with pytest.raises(ValueError):
        tashkent_day(datetime(2026, 1, 1))


def test_streak_extend_same_day_and_reset() -> None:
    s = Streak()
    d = date(2026, 1, 1)
    assert s.record_activity(d).extended and s.current == 1
    assert not s.record_activity(d).extended
    s.record_activity(d + timedelta(days=1))
    assert s.current == 2
    r = s.record_activity(d + timedelta(days=5))
    assert r.reset and s.current == 1 and s.longest == 2


def test_streak_freeze_covers_missed_days() -> None:
    s = Streak(current=4, longest=4, last_day=date(2026, 1, 1), freezes=2)
    r = s.record_activity(date(2026, 1, 3))
    assert r.freezes_used == 1 and s.current == 5 and s.freezes == 1
    assert s.current_on(date(2026, 1, 6)) == 0
    assert s.at_risk_on(date(2026, 1, 4)) and not s.active_on(date(2026, 1, 4))


def test_freeze_cap() -> None:
    s = Streak(freezes=2)
    assert not s.add_freeze(2)
    assert s.add_freeze(3) and s.freezes == 3


def test_hearts_partial_refill_keeps_timer() -> None:
    h = Hearts(2, T0)
    h.refill(T0 + 2 * HOUR + HOUR // 2, 5, HOUR)
    assert h.count == 4 and h.updated_at == T0 + 2 * HOUR
    assert h.next_refill_at(5, HOUR) == T0 + 3 * HOUR


def test_hearts_lose_floor_and_unlimited() -> None:
    h = Hearts(5, T0)
    assert h.lose(T0, 5, HOUR, unlimited=False) == 4 and h.updated_at == T0
    assert h.lose(T0, 5, HOUR, unlimited=True) == 4
    z = Hearts(0, T0)
    assert z.lose(T0, 5, HOUR, unlimited=False) == 0
    assert Hearts(1, T0).gain(10, 5) == 5


def _standings(n: int) -> list[Standing]:
    return [Standing(uuid4(), xp=(n - i) * 10, joined_order=i) for i in range(n)]


def test_league_promotion_and_demotion() -> None:
    st = _standings(10)
    out = settle_cohort(st, tier_idx=1, tier_count=3, promote=2, demote=2)
    by_rank = {s.rank: s.outcome for s in out}
    assert by_rank[1] is Outcome.PROMOTED and by_rank[2] is Outcome.PROMOTED
    assert by_rank[3] is Outcome.STAYED
    assert by_rank[9] is Outcome.DEMOTED and by_rank[10] is Outcome.DEMOTED


def test_league_edges() -> None:
    st = _standings(10)
    top = settle_cohort(st, tier_idx=2, tier_count=3, promote=2, demote=2)
    assert Outcome.PROMOTED not in {s.outcome for s in top}
    bottom = settle_cohort(st, tier_idx=0, tier_count=3, promote=2, demote=2)
    assert Outcome.DEMOTED not in {s.outcome for s in bottom}
    zero = [Standing(uuid4(), 0, i) for i in range(10)]
    assert Outcome.PROMOTED not in {s.outcome for s in settle_cohort(zero, 1, 3, 2, 2)}
    tiny = settle_cohort(_standings(3), 1, 3, 2, 2)
    assert Outcome.DEMOTED not in {s.outcome for s in tiny}


def test_tie_break_and_tiers() -> None:
    a, b = Standing(uuid4(), 10, 5), Standing(uuid4(), 10, 1)
    out = settle_cohort([a, b], 0, 3, 1, 0)
    assert out[0].user_id == b.user_id
    assert next_tier(0, Outcome.DEMOTED, 3) == 0 and next_tier(2, Outcome.PROMOTED, 3) == 2
    assert next_tier(1, Outcome.PROMOTED, 3) == 2


def test_week_start_and_cohort_choice() -> None:
    assert week_start(date(2026, 1, 11)) == date(2026, 1, 5)
    a, b = uuid4(), uuid4()
    assert choose_cohort({a: 10, b: 29}, 30) == b
    assert choose_cohort({a: 30}, 30) is None
