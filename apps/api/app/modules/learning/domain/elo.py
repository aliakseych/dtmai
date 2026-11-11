"""Per-user ELO, ported from legacy `compute_elo_delta` (constants kept identical)."""

from enum import StrEnum

DEFAULT_PLAYER_ELO = 1000
DEFAULT_QUESTION_ELO = 1200
TIME_CAP_SECONDS = 600.0


class Level(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    ORIGINAL = "original"  # official previous-year paper questions


K_FACTOR = {Level.EASY: 32, Level.MEDIUM: 32, Level.HARD: 48, Level.ORIGINAL: 64}
TIME_RATE = {Level.EASY: 0.0005, Level.MEDIUM: 0.0003, Level.HARD: 0.0002, Level.ORIGINAL: 0.0001}


def level_for(difficulty: float, *, official: bool) -> Level:
    if official:
        return Level.ORIGINAL
    if difficulty < 1100:
        return Level.EASY
    if difficulty < 1350:
        return Level.MEDIUM
    return Level.HARD


def expected_score(player_elo: float, question_elo: float) -> float:
    return 1 / (1 + 10 ** ((question_elo - player_elo) / 400))


def compute_elo_delta(
    player_elo: float,
    question_elo: float,
    correct: bool,
    level: Level,
    time_taken: float | None = None,
) -> int:
    raw = K_FACTOR[level] * ((1.0 if correct else 0.0) - expected_score(player_elo, question_elo))
    if time_taken is None:
        return int(round(raw))
    t = min(max(time_taken, 0.0), TIME_CAP_SECONDS)
    rate = TIME_RATE[level]
    if correct:
        return int(round(max(raw * (1 - t * rate), 1)))
    return int(round(min(-abs(raw) * (1 + t * rate), -1)))
