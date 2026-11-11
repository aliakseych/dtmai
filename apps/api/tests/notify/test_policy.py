from datetime import UTC, date, datetime, time
from uuid import uuid4

from app.modules.notify.domain.messages import catalog_locales, render
from app.modules.notify.domain.policy import (
    LOCALES,
    Channel,
    Kind,
    Preferences,
    decide,
    in_quiet_hours,
    streak_at_risk,
)


def _prefs(**kw: object) -> Preferences:
    base = {"enabled": True, "channels": {Channel.TELEGRAM}}
    return Preferences(user_id=uuid4(), **{**base, **kw})  # type: ignore[arg-type]


# 14:00 UTC = 19:00 Tashkent (UTC+5); 18:00 UTC = 23:00 Tashkent
DAY = datetime(2026, 3, 10, 14, 0, tzinfo=UTC)
NIGHT = datetime(2026, 3, 10, 18, 0, tzinfo=UTC)


def _decide(p: Preferences, now: datetime = DAY, sent: int = 0, kind_sent: bool = False):  # type: ignore[no-untyped-def]
    return decide(p, Kind.STREAK_REMINDER, Channel.TELEGRAM, now, sent_today=sent,
                  kind_sent_today=kind_sent)


def test_opt_in_required() -> None:
    assert _decide(_prefs(enabled=False)).reason == "opted_out"
    assert _decide(_prefs()).allowed


def test_channel_and_kind_filters() -> None:
    assert _decide(_prefs(channels={Channel.PUSH})).reason == "channel_off"
    assert _decide(_prefs(kinds={Kind.LEAGUE_ENDING})).reason == "kind_off"


def test_quiet_hours_wrap_midnight_in_tashkent() -> None:
    p = _prefs()
    assert in_quiet_hours(p, NIGHT)
    assert not in_quiet_hours(p, DAY)
    assert _decide(p, NIGHT).reason == "quiet_hours"


def test_caps() -> None:
    assert _decide(_prefs(max_per_day=2), sent=2).reason == "cap_reached"
    assert _decide(_prefs(), kind_sent=True).reason == "already_sent"


def test_equal_quiet_bounds_disable_quiet_hours() -> None:
    assert not in_quiet_hours(_prefs(quiet_start=time(0), quiet_end=time(0)), NIGHT)


def test_streak_at_risk_uses_tashkent_day() -> None:
    now = datetime(2026, 3, 10, 20, 0, tzinfo=UTC)  # 01:00 on 11th in Tashkent
    assert streak_at_risk(date(2026, 3, 10), 3, now)
    assert not streak_at_risk(date(2026, 3, 11), 3, now)
    assert not streak_at_risk(date(2026, 3, 9), 0, now)


def test_messages_cover_all_locales() -> None:
    for kind in Kind:
        assert catalog_locales(kind) == set(LOCALES)
    assert "5" in render(Kind.STREAK_REMINDER, "ru", streak=5).body
    assert render(Kind.DAILY_QUESTION, "xx").title == render(Kind.DAILY_QUESTION, "en").title
