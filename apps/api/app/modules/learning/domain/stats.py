"""Per-learner statistics assembled from learning, gamification and assessment data."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from uuid import UUID

STATS_DAYS = 30


@dataclass(frozen=True, slots=True)
class Progress:
    """Gamification side: lifetime counters plus xp per day."""

    xp_total: int
    streak_current: int
    streak_best: int
    lessons_completed: int
    daily_xp: dict[date, int]


@dataclass(frozen=True, slots=True)
class SubjectAnswers:
    subject_id: UUID | None
    answered: int
    correct: int
    mastery: float | None  # attempts-weighted mean of topic/type mastery, 0..1


@dataclass(frozen=True, slots=True)
class MockResult:
    mock_id: UUID
    taken_at: datetime
    score: float
    max_score: float


@dataclass(frozen=True, slots=True)
class DailyStat:
    date: date
    xp: int
    answered: int
    correct: int


@dataclass(frozen=True, slots=True)
class SubjectStat:
    subject_id: UUID
    answered: int
    correct: int
    mastery: float | None


@dataclass(frozen=True, slots=True)
class UserStats:
    xp_total: int
    streak_current: int
    streak_best: int
    lessons_completed: int
    accuracy: float  # correct / answered over all time, 0 when nothing was answered
    daily: list[DailyStat]
    by_subject: list[SubjectStat]
    mocks: list[MockResult]


def build_stats(
    progress: Progress,
    daily_answers: dict[date, tuple[int, int]],
    subjects: list[SubjectAnswers],
    mocks: list[MockResult],
    today: date,
    days: int = STATS_DAYS,
) -> UserStats:
    """Zero-filled `days`-day series ending today (oldest first); accuracy spans all answers."""
    series = []
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        answered, correct = daily_answers.get(day, (0, 0))
        series.append(DailyStat(day, progress.daily_xp.get(day, 0), answered, correct))
    answered_total = sum(s.answered for s in subjects)
    correct_total = sum(s.correct for s in subjects)
    return UserStats(
        xp_total=progress.xp_total,
        streak_current=progress.streak_current,
        streak_best=progress.streak_best,
        lessons_completed=progress.lessons_completed,
        accuracy=correct_total / answered_total if answered_total else 0.0,
        daily=series,
        by_subject=[
            SubjectStat(s.subject_id, s.answered, s.correct, s.mastery) for s in subjects if s.subject_id is not None
        ],
        mocks=mocks,
    )
