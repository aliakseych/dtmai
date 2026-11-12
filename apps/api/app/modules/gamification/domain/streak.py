"""Daily streak with freezes. A "day" is a calendar day in Asia/Tashkent."""

from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

TASHKENT = ZoneInfo("Asia/Tashkent")


def tashkent_day(at: datetime) -> date:
    if at.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return at.astimezone(TASHKENT).date()


@dataclass(frozen=True, slots=True)
class StreakResult:
    extended: bool
    reset: bool
    freezes_used: int


@dataclass(slots=True)
class Streak:
    current: int = 0
    longest: int = 0
    last_day: date | None = None
    freezes: int = 0

    def record_activity(self, day: date) -> StreakResult:
        """Register learning activity on `day`. Missed days are covered by freezes, one each."""
        if self.last_day is not None and day <= self.last_day:
            return StreakResult(False, False, 0)
        used = 0
        reset = False
        if self.last_day is None:
            self.current = 1
        else:
            missed = (day - self.last_day).days - 1
            if missed == 0:
                self.current += 1
            elif missed <= self.freezes:
                self.freezes -= missed
                used = missed
                self.current += 1
            else:
                reset = self.current > 0
                self.current = 1
        self.last_day = day
        self.longest = max(self.longest, self.current)
        return StreakResult(True, reset, used)

    def current_on(self, today: date) -> int:
        """Streak length as displayed on `today` (0 once it can no longer be saved by freezes)."""
        if self.last_day is None:
            return 0
        missed = (today - self.last_day).days - 1
        return self.current if missed <= self.freezes else 0

    def active_on(self, today: date) -> bool:
        return self.last_day == today

    def at_risk_on(self, today: date) -> bool:
        return self.current_on(today) > 0 and self.last_day != today

    def add_freeze(self, maximum: int) -> bool:
        if self.freezes >= maximum:
            return False
        self.freezes += 1
        return True
