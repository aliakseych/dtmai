from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.modules.identity.domain.models import (
    GUEST_RETENTION_DAYS,
    Role,
    guest_cutoff,
    is_guest_expired,
    parse_roles,
    validate_city,
    validate_subject_ids,
)
from app.shared.errors import ValidationFailed

NOW = datetime(2026, 11, 14, tzinfo=UTC)


def test_guest_expires_after_retention():
    old = NOW - timedelta(days=GUEST_RETENTION_DAYS, seconds=1)
    assert is_guest_expired({Role.GUEST}, old, now=NOW)


def test_guest_within_retention_kept():
    assert not is_guest_expired({Role.GUEST}, NOW - timedelta(days=GUEST_RETENTION_DAYS), now=NOW)


def test_non_guest_never_expires():
    old = NOW - timedelta(days=400)
    assert not is_guest_expired({Role.STUDENT}, old, now=NOW)
    assert not is_guest_expired({Role.GUEST, Role.ADMIN}, old, now=NOW)


def test_unknown_last_seen_is_kept():
    assert not is_guest_expired({Role.GUEST}, None, now=NOW)


def test_cutoff():
    assert guest_cutoff(NOW) == NOW - timedelta(days=30)


def test_city_normalised():
    assert validate_city("  tashkent ") == "tashkent"
    assert validate_city("   ") is None
    assert validate_city(None) is None
    with pytest.raises(ValidationFailed):
        validate_city("x" * 51)


def test_subject_ids_dedupe_and_bound():
    a, b = uuid4(), uuid4()
    assert validate_subject_ids([a, b, a]) == [a, b]
    with pytest.raises(ValidationFailed):
        validate_subject_ids([uuid4() for _ in range(11)])


def test_lyceum_rep_role_assignable():
    assert parse_roles(["student", "lyceum_rep"], actor_id=uuid4(), target_id=uuid4()) == {
        Role.STUDENT, Role.LYCEUM_REP,
    }
