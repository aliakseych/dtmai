from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.shared.errors import Forbidden, Unauthorized
from app.shared.security import decode_access_token, encode_access_token

SECRET = "unit-test-secret-unit-test-secret"


def test_roundtrip() -> None:
    uid = uuid4()
    p = decode_access_token(
        encode_access_token(uid, ["admin", "student"], secret=SECRET), secret=SECRET
    )
    assert p.user_id == uid
    assert p.roles == {"admin", "student"}


def test_expired() -> None:
    old = datetime.now(UTC) - timedelta(hours=1)
    token = encode_access_token(uuid4(), ["student"], secret=SECRET, ttl_seconds=60, now=old)
    with pytest.raises(Unauthorized) as e:
        decode_access_token(token, secret=SECRET)
    assert e.value.code == "token_expired"


def test_wrong_secret() -> None:
    token = encode_access_token(uuid4(), ["student"], secret=SECRET)
    with pytest.raises(Unauthorized):
        decode_access_token(token, secret="another-secret-another-secret-xx")


def test_garbage() -> None:
    with pytest.raises(Unauthorized):
        decode_access_token("not.a.jwt", secret=SECRET)


async def test_require_role() -> None:
    from app.shared.deps import require_role
    from app.shared.security import Principal

    dep = require_role("admin")
    with pytest.raises(Forbidden):
        await dep(Principal(uuid4(), frozenset({"student"})))
    assert (await dep(Principal(uuid4(), frozenset({"admin"})))).roles == {"admin"}
