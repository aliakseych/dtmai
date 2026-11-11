"""Question Rush: a 60-second timed run of verified questions with a score streak."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta

RUSH_SECONDS = 60
GRACE_SECONDS = 3  # network slack: an answer sent at most this late still counts
POOL_SIZE = 80  # more than anyone can answer in a minute
BASE_POINTS = 10
STREAK_STEP = 5  # every 5 correct in a row raises the multiplier
MAX_MULTIPLIER = 3
XP_PER_CORRECT = 1
XP_PER_STREAK_STEP = 3
XP_CAP = 60


@dataclass(frozen=True, slots=True)
class RushScore:
    correct: int
    wrong: int
    best_streak: int
    points: int


def multiplier(streak: int) -> int:
    """Score multiplier for a correct answer that brings the streak to `streak`."""
    return min(MAX_MULTIPLIER, 1 + max(0, streak) // STREAK_STEP)


def score(results: Iterable[bool]) -> RushScore:
    correct = wrong = streak = best = points = 0
    for ok in results:
        if ok:
            correct += 1
            streak += 1
            best = max(best, streak)
            points += BASE_POINTS * multiplier(streak)
        else:
            wrong += 1
            streak = 0
    return RushScore(correct, wrong, best, points)


def xp(correct: int, best_streak: int) -> int:
    """League XP for a finished run; a run without a correct answer earns nothing."""
    if correct <= 0:
        return 0
    return min(XP_CAP, correct * XP_PER_CORRECT + (best_streak // STREAK_STEP) * XP_PER_STREAK_STEP)


def deadline(started_at: datetime) -> datetime:
    return started_at + timedelta(seconds=RUSH_SECONDS)


def is_expired(now: datetime, ends_at: datetime) -> bool:
    return now > ends_at + timedelta(seconds=GRACE_SECONDS)
