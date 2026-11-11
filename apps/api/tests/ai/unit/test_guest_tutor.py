import pytest

from app.modules.ai.application.errors import GuestNotAllowed, ensure_registered


def test_guest_is_rejected_with_403_code() -> None:
    with pytest.raises(GuestNotAllowed) as e:
        ensure_registered(frozenset({"guest"}))
    assert e.value.status == 403
    assert e.value.code == "guest_not_allowed"


def test_registered_user_passes() -> None:
    ensure_registered(frozenset({"student"}))
