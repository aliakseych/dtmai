"""Hearts with timed refill. Unlimited plans (feature `unlimited_hearts`) never lose hearts."""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(slots=True)
class Hearts:
    count: int
    updated_at: datetime  # start of the current refill interval

    def refill(self, now: datetime, maximum: int, interval: timedelta) -> None:
        if self.count >= maximum:
            self.count = maximum
            self.updated_at = now
            return
        gained = max(0, (now - self.updated_at) // interval)
        if gained:
            self.count = min(maximum, self.count + gained)
            self.updated_at = now if self.count >= maximum else self.updated_at + gained * interval

    def lose(self, now: datetime, maximum: int, interval: timedelta, *, unlimited: bool) -> int:
        """Deduct one heart (never below 0, never blocks). Returns hearts left."""
        self.refill(now, maximum, interval)
        if unlimited or self.count == 0:
            return self.count
        if self.count >= maximum:
            self.updated_at = now  # the refill timer starts when we drop below max
        self.count -= 1
        return self.count

    def gain(self, amount: int, maximum: int) -> int:
        self.count = min(maximum, self.count + max(0, amount))
        return self.count

    def next_refill_at(self, maximum: int, interval: timedelta) -> datetime | None:
        return None if self.count >= maximum else self.updated_at + interval
