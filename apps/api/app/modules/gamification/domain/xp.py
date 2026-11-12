"""XP anti-farming: per-session ceiling relative to items answered, plus a daily cap."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class XpCaps:
    daily_cap: int
    session_cap: int
    per_item_cap: int


def clamp_session_xp(base: int, total_items: int, caps: XpCaps) -> int:
    ceiling = min(caps.session_cap, max(0, total_items) * caps.per_item_cap)
    return max(0, min(base, ceiling))


def within_daily_cap(amount: int, earned_today: int, daily_cap: int) -> int:
    return max(0, min(amount, daily_cap - earned_today))
