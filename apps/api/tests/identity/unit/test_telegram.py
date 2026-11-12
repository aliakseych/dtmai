import hashlib
import hmac
import json
from urllib.parse import urlencode

import pytest

from app.modules.identity.domain.telegram import verify_init_data, verify_login_widget
from app.shared.errors import Unauthorized

TOKEN = "123456:TEST-TOKEN"
NOW = 1_700_000_000.0


def _sign_init(fields: dict[str, str]) -> str:
    check = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    return urlencode(
        {**fields, "hash": hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()}
    )


def _sign_widget(fields: dict[str, str]) -> dict[str, str]:
    check = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    secret = hashlib.sha256(TOKEN.encode()).digest()
    return {**fields, "hash": hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()}


def _init_fields(auth_date: float = NOW) -> dict[str, str]:
    user = {"id": 42, "first_name": "Ali", "last_name": "V", "language_code": "ru"}
    return {"auth_date": str(int(auth_date)), "query_id": "AAH", "user": json.dumps(user)}


def test_init_data_valid() -> None:
    p = verify_init_data(_sign_init(_init_fields()), TOKEN, now=NOW + 10)
    assert (p.id, p.first_name, p.language_code) == (42, "Ali", "ru")
    assert p.display_name == "Ali V"


def test_init_data_tampered() -> None:
    raw = _sign_init(_init_fields()).replace("Ali", "Eve")
    with pytest.raises(Unauthorized):
        verify_init_data(raw, TOKEN, now=NOW)


def test_init_data_wrong_token() -> None:
    with pytest.raises(Unauthorized):
        verify_init_data(_sign_init(_init_fields()), "999:OTHER", now=NOW)


def test_init_data_expired() -> None:
    with pytest.raises(Unauthorized) as e:
        verify_init_data(_sign_init(_init_fields()), TOKEN, max_age=60, now=NOW + 3600)
    assert e.value.code == "telegram_expired"


def test_init_data_missing_hash() -> None:
    with pytest.raises(Unauthorized):
        verify_init_data("auth_date=1", TOKEN)


def test_widget_valid() -> None:
    data = _sign_widget({"id": "7", "first_name": "Bek", "auth_date": str(int(NOW))})
    assert verify_login_widget(data, TOKEN, now=NOW).id == 7


def test_widget_bad_hash() -> None:
    data = _sign_widget({"id": "7", "first_name": "Bek", "auth_date": str(int(NOW))})
    data["first_name"] = "Evil"
    with pytest.raises(Unauthorized):
        verify_login_widget(data, TOKEN, now=NOW)


def test_widget_uses_sha256_not_webappdata_key() -> None:
    fields = {"id": "7", "first_name": "Bek", "auth_date": str(int(NOW))}
    forged = dict(fields, hash=_sign_init(fields).split("hash=")[1])
    with pytest.raises(Unauthorized):
        verify_login_widget(forged, TOKEN, now=NOW)
