from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

TASHKENT = ZoneInfo("Asia/Tashkent")


def tashkent_today(now: datetime | None = None) -> date:
    return (now or datetime.now(UTC)).astimezone(TASHKENT).date()
