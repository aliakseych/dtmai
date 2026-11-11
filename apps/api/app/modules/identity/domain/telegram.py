"""Pure Telegram credential verification (no I/O)."""

import hashlib
import hmac
import json
import time
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import parse_qsl

from app.shared.errors import Unauthorized


@dataclass(frozen=True, slots=True)
class TelegramProfile:
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None

    @property
    def display_name(self) -> str:
        return " ".join(p for p in (self.first_name, self.last_name) if p) or self.username or str(
            self.id
        )


def _check_string(fields: Mapping[str, str]) -> str:
    return "\n".join(f"{k}={fields[k]}" for k in sorted(fields))


def _fresh(auth_date: str | None, max_age: int, now: float | None) -> None:
    try:
        issued = int(auth_date or "")
    except ValueError as e:
        raise Unauthorized("bad auth_date", code="telegram_invalid") from e
    if (now if now is not None else time.time()) - issued > max_age:
        raise Unauthorized("telegram data expired", code="telegram_expired")


def verify_init_data(
    init_data: str, bot_token: str, *, max_age: int = 86400, now: float | None = None
) -> TelegramProfile:
    """Verify Mini App ``initData``: secret = HMAC_SHA256(key="WebAppData", msg=bot_token)."""
    fields = dict(parse_qsl(init_data, keep_blank_values=True))
    received = fields.pop("hash", None)
    if not received or not bot_token:
        raise Unauthorized("telegram hash missing", code="telegram_invalid")
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, _check_string(fields).encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received):
        raise Unauthorized("telegram signature mismatch", code="telegram_invalid")
    _fresh(fields.get("auth_date"), max_age, now)
    try:
        user = json.loads(fields["user"])
        return TelegramProfile(
            id=int(user["id"]),
            first_name=user.get("first_name", ""),
            last_name=user.get("last_name"),
            username=user.get("username"),
            language_code=user.get("language_code"),
        )
    except (KeyError, ValueError, TypeError) as e:
        raise Unauthorized("telegram user missing", code="telegram_invalid") from e


def verify_login_widget(
    data: Mapping[str, str], bot_token: str, *, max_age: int = 86400, now: float | None = None
) -> TelegramProfile:
    """Verify Login Widget payload: secret = SHA256(bot_token)."""
    fields = {k: str(v) for k, v in data.items() if v is not None}
    received = fields.pop("hash", None)
    if not received or not bot_token:
        raise Unauthorized("telegram hash missing", code="telegram_invalid")
    secret = hashlib.sha256(bot_token.encode()).digest()
    expected = hmac.new(secret, _check_string(fields).encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received):
        raise Unauthorized("telegram signature mismatch", code="telegram_invalid")
    _fresh(fields.get("auth_date"), max_age, now)
    try:
        return TelegramProfile(
            id=int(fields["id"]),
            first_name=fields.get("first_name", ""),
            last_name=fields.get("last_name"),
            username=fields.get("username"),
            language_code=None,
        )
    except (KeyError, ValueError) as e:
        raise Unauthorized("telegram id missing", code="telegram_invalid") from e
