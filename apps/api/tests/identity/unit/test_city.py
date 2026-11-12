import asyncio

import pytest

from app.modules.identity.application.service import IdentityConfig, IdentityService
from app.modules.identity.domain.models import User
from app.shared.errors import ValidationFailed
from app.shared.ids import new_id


class Users:
    def __init__(self, user: User) -> None:
        self.u = user

    async def get(self, user_id):
        return self.u

    async def save(self, user):
        self.u = user


class Cities:
    async def exists(self, code):
        return code in ("tashkent", "samarkand")


def make() -> tuple[IdentityService, Users, User]:
    user = User(id=new_id(), name="A", email="a@b.uz", email_verified=True, password_hash="h")
    users = Users(user)
    cfg = IdentityConfig(60, 600, 600, 3, "t", 60, "s" * 32)
    svc = IdentityService(users, None, None, None, None, None, cfg, Cities(), None)  # type: ignore[arg-type]
    return svc, users, user


def test_known_city_code_is_stored():
    svc, _, user = make()
    updated = asyncio.run(svc.update_me(user.id, city=" samarkand "))
    assert updated.city == "samarkand"


def test_unknown_city_rejected_with_code():
    svc, users, user = make()
    with pytest.raises(ValidationFailed) as err:
        asyncio.run(svc.update_me(user.id, city="atlantis"))
    assert err.value.code == "unknown_city"
    assert users.u.city is None


def test_null_city_means_any_city():
    svc, _, user = make()
    asyncio.run(svc.update_me(user.id, city="tashkent"))
    assert asyncio.run(svc.update_me(user.id, city=None)).city is None
