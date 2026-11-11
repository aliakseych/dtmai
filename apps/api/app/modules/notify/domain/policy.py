from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time
from enum import StrEnum
from zoneinfo import ZoneInfo

from app.shared.errors import ValidationFailed

TASHKENT = ZoneInfo("Asia/Tashkent")
LOCALES = ("uz-Latn", "uz-Cyrl", "ru", "en")


class Kind(StrEnum):
    STREAK_REMINDER = "streak_reminder"
    LEAGUE_ENDING = "league_ending"
    DAILY_QUESTION = "daily_question"


class Channel(StrEnum):
    TELEGRAM = "telegram"
    PUSH = "push"
    EMAIL = "email"


def tashkent_day(now: datetime) -> date:
    return now.astimezone(TASHKENT).date()


@dataclass(slots=True)
class Preferences:
    """Opt-in by default OFF: nothing is sent until the user enables a channel."""

    user_id: object
    enabled: bool = False
    channels: set[Channel] = field(default_factory=set)
    kinds: set[Kind] = field(default_factory=lambda: set(Kind))
    quiet_start: time = time(22, 0)
    quiet_end: time = time(8, 0)
    max_per_day: int = 2

    def validate(self) -> None:
        if not 0 <= self.max_per_day <= 10:
            raise ValidationFailed("max_per_day must be 0..10", code="invalid_cap")


def in_quiet_hours(prefs: Preferences, now: datetime) -> bool:
    local = now.astimezone(TASHKENT).time().replace(tzinfo=None)
    s, e = prefs.quiet_start, prefs.quiet_end
    if s == e:
        return False
    return s <= local < e if s < e else (local >= s or local < e)


@dataclass(frozen=True, slots=True)
class Decision:
    allowed: bool
    reason: str = "ok"


def decide(
    prefs: Preferences,
    kind: Kind,
    channel: Channel,
    now: datetime,
    *,
    sent_today: int,
    kind_sent_today: bool,
) -> Decision:
    """Whether to deliver `kind` over `channel` now. `sent_today`/`kind_sent_today` are
    counted over the Asia/Tashkent day."""
    if not prefs.enabled:
        return Decision(False, "opted_out")
    if channel not in prefs.channels:
        return Decision(False, "channel_off")
    if kind not in prefs.kinds:
        return Decision(False, "kind_off")
    if in_quiet_hours(prefs, now):
        return Decision(False, "quiet_hours")
    if kind_sent_today:
        return Decision(False, "already_sent")
    if sent_today >= prefs.max_per_day:
        return Decision(False, "cap_reached")
    return Decision(True)


def streak_at_risk(last_active_day: date | None, streak: int, now: datetime) -> bool:
    """True when the learner has a streak but has not practised today (Tashkent)."""
    return streak > 0 and last_active_day is not None and last_active_day < tashkent_day(now)


def utcnow() -> datetime:
    return datetime.now(UTC)
