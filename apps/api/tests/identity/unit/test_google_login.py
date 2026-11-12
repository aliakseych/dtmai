import pytest

from app.modules.identity.domain.models import User
from app.modules.identity.ports import GoogleProfile
from app.shared.errors import Unauthorized, ValidationFailed
from app.shared.ids import new_id
from tests.identity.unit.test_password_reset import make


class FakeGoogle:
    def __init__(self, profile=None):
        self.profile = profile

    async def verify(self, id_token):
        if self.profile is None:
            raise Unauthorized("bad", code="invalid_google_token")
        return self.profile


class Store:
    """Users fake with `add`, on top of the shared one."""

    def __init__(self, user):
        self.u = user
        self.added: list[User] = []

    async def by_email(self, email):
        return self.u if self.u and self.u.email == email else None

    async def add(self, user):
        self.added.append(user)

    async def save(self, user):
        self.u = user

    async def touch(self, *a):
        return None


def build(profile, existing=None):
    svc, _, _, _ = make(existing)
    svc._users = Store(existing)
    svc._google = FakeGoogle(profile)
    return svc


def prof(**kw):
    base = dict(sub="1", email="New@B.uz", email_verified=True, name="Ann")
    return GoogleProfile(**{**base, **kw})


async def test_creates_verified_user():
    svc = build(prof())
    tokens = await svc.login_google("x" * 20)
    assert tokens.access_token
    (u,) = svc._users.added
    assert u.email == "new@b.uz" and u.email_verified and u.name == "Ann"


async def test_links_existing_user_by_email():
    existing = User(id=new_id(), name="A", email="a@b.uz", email_verified=True, password_hash="h:x")
    svc = build(prof(email="a@b.uz"), existing)
    await svc.login_google("x" * 20)
    assert not svc._users.added and existing.password_hash == "h:x"


async def test_unverified_signup_is_claimed():
    existing = User(id=new_id(), name="A", email="a@b.uz", password_hash="h:x")
    svc = build(prof(email="a@b.uz"), existing)
    await svc.login_google("x" * 20)
    assert existing.email_verified and existing.password_hash is None


async def test_invalid_token_and_unverified_email_rejected():
    with pytest.raises(Unauthorized):
        await build(None).login_google("x" * 20)
    with pytest.raises(Unauthorized):
        await build(prof(email_verified=False)).login_google("x" * 20)


async def test_disabled_without_verifier():
    svc = build(prof())
    svc._google = None
    with pytest.raises(ValidationFailed):
        await svc.login_google("x" * 20)
