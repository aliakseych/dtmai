import asyncio
from uuid import uuid4

import pytest

from app.modules.identity.application.service import IdentityConfig, IdentityService
from app.modules.identity.domain.models import User, dream_field_mismatch, validate_field_code
from app.shared.errors import ValidationFailed
from app.shared.ids import new_id

MATH, PHYS, ENG = uuid4(), uuid4(), uuid4()


class Users:
    def __init__(self, user: User) -> None:
        self.u = user

    async def get(self, user_id):
        return self.u

    async def save(self, user):
        self.u = user


class Cities:
    async def exists(self, code):
        return True


class Fields:
    def __init__(self, mapping, offered) -> None:
        self.mapping, self.offered = mapping, offered

    async def subjects_for(self, code):
        return self.mapping.get(code)

    async def offered_fields(self, lyceum_ids):
        return {i: self.offered[i] for i in lyceum_ids if i in self.offered}


def make(mapping=None, offered=None):
    user = User(id=new_id(), name="A", email="a@b.uz", email_verified=True, password_hash="h")
    cfg = IdentityConfig(60, 600, 600, 3, "t", 60, "s" * 32)
    fields = Fields(mapping or {}, offered or {})
    svc = IdentityService(  # type: ignore[arg-type]
        Users(user), None, None, None, None, None, cfg, Cities(), fields
    )
    return svc, user


def test_field_code_normalised():
    assert validate_field_code(None) is None
    assert validate_field_code("  ") is None
    assert validate_field_code(" 601 ") == "601"
    with pytest.raises(ValidationFailed) as e:
        validate_field_code("x" * 21)
    assert e.value.code == "invalid_field_code"


def test_mapped_field_derives_subjects_overriding_explicit():
    svc, user = make({"601": [MATH, PHYS]})
    updated = asyncio.run(svc.update_me(user.id, field_code="601", subject_ids=[ENG]))
    assert updated.field_code == "601"
    assert updated.subject_ids == [MATH, PHYS]


def test_unmapped_field_keeps_explicit_subjects():
    svc, user = make()
    updated = asyncio.run(svc.update_me(user.id, field_code="999", subject_ids=[ENG]))
    assert updated.subject_ids == [ENG]


def test_mapped_field_wins_on_later_subject_edit():
    svc, user = make({"601": [MATH, PHYS]})
    asyncio.run(svc.update_me(user.id, field_code="601"))
    updated = asyncio.run(svc.update_me(user.id, subject_ids=[ENG]))
    assert updated.subject_ids == [MATH, PHYS]


def test_clearing_field_keeps_subjects_editable():
    svc, user = make({"601": [MATH]})
    asyncio.run(svc.update_me(user.id, field_code="601"))
    updated = asyncio.run(svc.update_me(user.id, field_code=None, subject_ids=[ENG]))
    assert updated.field_code is None
    assert updated.subject_ids == [ENG]


def test_mismatch_lists_lyceums_lacking_the_field_in_priority_order():
    a, b, c = uuid4(), uuid4(), uuid4()
    offered = {a: {"601"}, b: {"602"}}
    assert dream_field_mismatch("601", [a, b, c], offered) == [b, c]
    assert dream_field_mismatch(None, [a, b], offered) == []
    assert dream_field_mismatch("601", [], offered) == []


def test_service_mismatch_does_not_reject():
    a, b = uuid4(), uuid4()
    svc, user = make(offered={a: {"601"}, b: {"602"}})
    asyncio.run(svc.update_me(user.id, dream_lyceum_ids=[a, b], field_code="601"))
    assert asyncio.run(svc.dream_field_mismatch(user)) == [b]
    user.field_code = None
    assert asyncio.run(svc.dream_field_mismatch(user)) == []
