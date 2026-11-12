from uuid import uuid4

import pytest

from app.modules.identity.domain.models import Role, User, ensure_admin_change_allowed
from app.shared.errors import Conflict, ValidationFailed


def _admin() -> User:
    return User(id=uuid4(), name="A", email="a@b.uz", roles={Role.ADMIN})


def test_admin_cannot_disable_self():
    me = _admin()
    with pytest.raises(ValidationFailed) as e:
        ensure_admin_change_allowed(
            actor_id=me.id, target=me, new_roles={Role.ADMIN}, disabled=True, active_admins=3
        )
    assert e.value.code == "self_disable"


def test_last_admin_cannot_be_demoted_or_disabled():
    target = _admin()
    for roles, disabled in (({Role.STUDENT}, False), ({Role.ADMIN}, True)):
        with pytest.raises(Conflict) as e:
            ensure_admin_change_allowed(
                actor_id=uuid4(), target=target, new_roles=roles, disabled=disabled, active_admins=1
            )
        assert e.value.code == "last_admin"


def test_demoting_one_of_many_admins_is_allowed():
    ensure_admin_change_allowed(
        actor_id=uuid4(), target=_admin(), new_roles={Role.STUDENT}, disabled=False, active_admins=2
    )
