import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from app.modules.identity.application.service import IdentityConfig, IdentityService, _sha
from app.modules.identity.domain.models import EmailCode, User
from app.shared.errors import ValidationFailed
from app.shared.ids import new_id

NOW = datetime(2026, 1, 1, tzinfo=UTC)


class Users:
    def __init__(self, user):
        self.u = user

    async def by_email(self, email):
        return self.u if self.u and self.u.email == email else None

    async def save(self, user):
        self.u = user

    async def touch(self, user_id, at=None):
        return None

    async def get(self, user_id):
        return self.u if self.u and self.u.id == user_id else None


class Codes:
    def __init__(self):
        self.items: list[EmailCode] = []

    async def add(self, c):
        self.items.append(c)

    async def latest_for(self, user_id):
        return self.items[-1] if self.items else None

    async def record_attempt(self, cid):
        self.items[-1] = replace(self.items[-1], attempts=self.items[-1].attempts + 1)

    async def consume(self, cid):
        self.items[-1] = replace(self.items[-1], consumed=True)


class Refresh:
    def __init__(self):
        self.revoked_for: list = []

    async def add(self, t):
        pass

    async def revoke_all(self, user_id):
        self.revoked_for.append(user_id)


class Hasher:
    def hash(self, p):
        return "h:" + p

    def verify(self, p, h):
        return h == "h:" + p


class Mailer:
    def __init__(self):
        self.sent: list[tuple[str, str, str]] = []

    async def send(self, to, subject, body):
        self.sent.append((to, subject, body))


class Clock:
    def now(self):
        return NOW


class Cities:
    async def exists(self, code):
        return code == "tashkent"


def make(user):
    cfg = IdentityConfig(
        access_ttl=60,
        refresh_ttl=600,
        code_ttl=600,
        code_max_attempts=3,
        bot_token="t",
        init_data_max_age=60,
        jwt_secret="s" * 32,
    )
    users, codes, mail = Users(user), Codes(), Mailer()
    return (
        IdentityService(users, codes, Refresh(), Hasher(), mail, Clock(), cfg, Cities(), None),
        users,
        codes,
        mail,
    )


def _user():
    return User(
        id=new_id(), name="A", email="a@b.uz", email_verified=False, password_hash="h:oldpassword"
    )


def test_forgot_sends_code_and_unknown_is_silent():
    svc, _, codes, mail = make(_user())
    asyncio.run(svc.forgot_password("A@B.uz"))
    assert len(codes.items) == 1 and mail.sent[0][0] == "a@b.uz"
    asyncio.run(svc.forgot_password("nobody@b.uz"))
    assert len(mail.sent) == 1


def test_reset_with_valid_code_sets_password_and_consumes():
    svc, users, codes, mail = make(_user())
    asyncio.run(svc.forgot_password("a@b.uz"))
    code = mail.sent[0][1].removeprefix("DTM AI: ")
    tokens = asyncio.run(svc.reset_password("a@b.uz", code, "newpassword"))
    assert (
        tokens.access_token and users.u.password_hash == "h:newpassword" and users.u.email_verified
    )
    assert codes.items[-1].consumed
    with pytest.raises(ValidationFailed):  # single use
        asyncio.run(svc.reset_password("a@b.uz", code, "another-pass"))


def test_reset_rejects_wrong_expired_unknown_and_weak():
    user = _user()
    svc, users, codes, mail = make(user)
    asyncio.run(svc.forgot_password("a@b.uz"))
    with pytest.raises(ValidationFailed):
        asyncio.run(svc.reset_password("a@b.uz", "000000x", "newpassword"))
    assert codes.items[-1].attempts == 1
    with pytest.raises(ValidationFailed):
        asyncio.run(svc.reset_password("nobody@b.uz", "123456", "newpassword"))
    with pytest.raises(ValidationFailed):
        asyncio.run(svc.reset_password("a@b.uz", "123456", "short"))
    codes.items[-1] = replace(
        codes.items[-1], expires_at=NOW - timedelta(seconds=1), code_hash=_sha(f"{user.id}:123456")
    )
    with pytest.raises(ValidationFailed):
        asyncio.run(svc.reset_password("a@b.uz", "123456", "newpassword"))
    assert users.u.password_hash == "h:oldpassword"


def test_admin_reset_password_revokes_refresh_tokens():
    user = _user()
    svc, users, _, _ = make(user)
    refresh = svc._refresh
    asyncio.run(svc.reset_user_password(user.id, "brand-new-pass"))
    assert users.u.password_hash == "h:brand-new-pass" and refresh.revoked_for == [user.id]


def test_invalid_code_is_not_401():
    svc, _, _, _ = make(_user())
    asyncio.run(svc.forgot_password("a@b.uz"))
    with pytest.raises(ValidationFailed) as e:
        asyncio.run(svc.reset_password("a@b.uz", "000000x", "newpassword"))
    assert e.value.status == 422 and e.value.code == "invalid_code"
