from datetime import UTC, datetime, timedelta

from app.modules.learning.domain.elo import Level, compute_elo_delta, expected_score, level_for
from app.modules.learning.domain.srs import MIN_EASE, RELEARN_DELAY, new_card

NOW = datetime(2026, 1, 5, 12, 0, tzinfo=UTC)


def test_new_card_due_soon() -> None:
    c = new_card(NOW)
    assert c.lapses == 1 and c.due_at == NOW + RELEARN_DELAY
    assert not c.is_due(NOW) and c.is_due(NOW + RELEARN_DELAY)


def test_correct_reviews_grow_interval() -> None:
    c = new_card(NOW)
    c.review(True, NOW)
    assert c.interval_days == 1
    c.review(True, NOW)
    assert c.interval_days == 3
    c.review(True, NOW)
    assert c.interval_days > 3 and c.due_at == NOW + timedelta(days=c.interval_days)


def test_wrong_resets_and_floors_ease() -> None:
    c = new_card(NOW)
    for _ in range(3):
        c.review(True, NOW)
    for _ in range(20):
        c.review(False, NOW)
    assert c.reps == 0 and c.interval_days == 0 and c.ease == MIN_EASE


def test_mastered() -> None:
    c = new_card(NOW)
    for _ in range(12):
        c.review(True, NOW)
    assert c.mastered


def test_elo_symmetry_and_direction() -> None:
    assert expected_score(1000, 1000) == 0.5
    assert compute_elo_delta(1000, 1000, True, Level.MEDIUM) == 16
    assert compute_elo_delta(1000, 1000, False, Level.MEDIUM) == -16
    assert compute_elo_delta(1000, 1000, True, Level.ORIGINAL) == 32


def test_elo_time_penalty_and_min_step() -> None:
    fast = compute_elo_delta(1000, 1200, True, Level.EASY, 1)
    slow = compute_elo_delta(1000, 1200, True, Level.EASY, 600)
    assert fast >= slow >= 1
    assert compute_elo_delta(3000, 800, True, Level.EASY, 5) == 1
    assert compute_elo_delta(1000, 1200, False, Level.EASY, 5) <= -1


def test_level_for() -> None:
    assert level_for(1000, official=False) is Level.EASY
    assert level_for(1200, official=False) is Level.MEDIUM
    assert level_for(1500, official=False) is Level.HARD
    assert level_for(1000, official=True) is Level.ORIGINAL
