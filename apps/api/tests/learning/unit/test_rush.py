from datetime import UTC, datetime, timedelta

from app.modules.learning.domain import rush

T0 = datetime(2026, 1, 5, 12, 0, tzinfo=UTC)


def test_multiplier_steps_and_caps() -> None:
    assert [rush.multiplier(n) for n in (1, 4, 5, 9, 10, 99)] == [1, 1, 2, 2, 3, 3]


def test_score_counts_streak_and_resets_on_wrong() -> None:
    s = rush.score([True, True, False, True])
    assert (s.correct, s.wrong, s.best_streak, s.points) == (3, 1, 2, 30)


def test_score_multiplier_applies_from_fifth_in_a_row() -> None:
    s = rush.score([True] * 5)
    assert s.points == 4 * 10 + 20 and s.best_streak == 5


def test_score_empty() -> None:
    assert rush.score([]) == rush.RushScore(0, 0, 0, 0)


def test_xp_zero_without_correct() -> None:
    assert rush.xp(0, 0) == 0


def test_xp_rewards_streak_and_is_capped() -> None:
    assert rush.xp(4, 4) == 4
    assert rush.xp(10, 10) == 10 + 6
    assert rush.xp(500, 500) == rush.XP_CAP


def test_deadline_and_grace() -> None:
    end = rush.deadline(T0)
    assert end == T0 + timedelta(seconds=60)
    assert not rush.is_expired(end + timedelta(seconds=rush.GRACE_SECONDS), end)
    assert rush.is_expired(end + timedelta(seconds=rush.GRACE_SECONDS + 1), end)
