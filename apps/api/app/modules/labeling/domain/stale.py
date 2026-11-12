from datetime import datetime, timedelta

STALE_AFTER = timedelta(hours=2)
ACTIVE_STATUSES = ("pending", "running")


def is_abandoned(status: str, queued_at: datetime, now: datetime) -> bool:
    """A pending/running batch nobody finished within STALE_AFTER lost its worker."""
    return status in ACTIVE_STATUSES and now - queued_at > STALE_AFTER
