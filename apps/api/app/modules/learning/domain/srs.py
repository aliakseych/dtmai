"""Spaced repetition of mistakes (SM-2 lite). A card is created on a wrong answer."""

from dataclasses import dataclass
from datetime import datetime, timedelta

START_EASE = 2.5
MIN_EASE = 1.3
MAX_EASE = 3.0
RELEARN_DELAY = timedelta(minutes=10)
MASTERED_REPS = 5
MASTERED_DAYS = 30


@dataclass(slots=True)
class Card:
    ease: float = START_EASE
    interval_days: int = 0
    reps: int = 0
    lapses: int = 0
    due_at: datetime | None = None

    def review(self, correct: bool, now: datetime) -> None:
        if not correct:
            self.lapses += 1
            self.reps = 0
            self.interval_days = 0
            self.ease = max(MIN_EASE, self.ease - 0.2)
            self.due_at = now + RELEARN_DELAY
            return
        self.reps += 1
        if self.reps == 1:
            self.interval_days = 1
        elif self.reps == 2:
            self.interval_days = 3
        else:
            self.interval_days = max(self.interval_days + 1, round(self.interval_days * self.ease))
        self.ease = min(MAX_EASE, self.ease + 0.05)
        self.due_at = now + timedelta(days=self.interval_days)

    def is_due(self, now: datetime) -> bool:
        return self.due_at is not None and self.due_at <= now

    @property
    def mastered(self) -> bool:
        return self.reps >= MASTERED_REPS and self.interval_days >= MASTERED_DAYS


def new_card(now: datetime) -> Card:
    """First wrong answer: relearn soon."""
    c = Card()
    c.lapses = 1
    c.ease = START_EASE - 0.2
    c.due_at = now + RELEARN_DELAY
    return c
