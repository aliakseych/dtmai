from uuid import uuid4

import pytest

from app.modules.identity.domain.models import Role, parse_roles
from app.shared.deps import has_any_role
from app.shared.errors import ValidationFailed


def test_has_any_role():
    assert has_any_role(frozenset({"admin"}), ("admin",))
    assert has_any_role({"editor"}, ("editor", "admin"))
    assert not has_any_role({"student"}, ("admin",))
    assert not has_any_role(set(), ("admin",))


def test_parse_roles_ok():
    assert parse_roles(["student", "editor"], actor_id=uuid4(), target_id=uuid4()) == {Role.STUDENT, Role.EDITOR}


@pytest.mark.parametrize("raw", [[], ["root"], ["guest", "student"]])
def test_parse_roles_rejects(raw):
    with pytest.raises(ValidationFailed):
        parse_roles(raw, actor_id=uuid4(), target_id=uuid4())


def test_admin_cannot_self_demote():
    me = uuid4()
    with pytest.raises(ValidationFailed):
        parse_roles(["student"], actor_id=me, target_id=me)
    assert parse_roles(["admin"], actor_id=me, target_id=me) == {Role.ADMIN}
