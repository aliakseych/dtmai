from datetime import UTC, datetime, timedelta

from app.modules.labeling.domain.stale import STALE_AFTER, is_abandoned

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def test_old_running_is_abandoned():
    assert is_abandoned("running", NOW - STALE_AFTER - timedelta(minutes=1), NOW)
    assert is_abandoned("pending", NOW - STALE_AFTER - timedelta(minutes=1), NOW)


def test_recent_or_finished_is_not_abandoned():
    assert not is_abandoned("running", NOW - timedelta(minutes=5), NOW)
    assert not is_abandoned("done", NOW - timedelta(days=3), NOW)
    assert not is_abandoned("failed", NOW - timedelta(days=3), NOW)
