from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.settings import get_settings
from app.shared.errors import Unauthorized

ALGORITHM = "HS256"


@dataclass(frozen=True, slots=True)
class Principal:
    user_id: UUID
    roles: frozenset[str]


def encode_access_token(
    user_id: UUID,
    roles: list[str] | frozenset[str],
    *,
    secret: str | None = None,
    ttl_seconds: int | None = None,
    now: datetime | None = None,
) -> str:
    s = get_settings()
    issued = now or datetime.now(UTC)
    ttl = s.access_ttl_seconds if ttl_seconds is None else ttl_seconds
    payload = {
        "sub": str(user_id),
        "roles": sorted(roles),
        "typ": "access",
        "iat": issued,
        "exp": issued + timedelta(seconds=ttl),
    }
    return jwt.encode(payload, secret or s.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str, *, secret: str | None = None) -> Principal:
    try:
        data = jwt.decode(
            token,
            secret or get_settings().jwt_secret,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
        if data.get("typ") != "access":
            raise Unauthorized("wrong token type", code="invalid_token")
        return Principal(UUID(data["sub"]), frozenset(data.get("roles", [])))
    except jwt.ExpiredSignatureError as e:
        raise Unauthorized("token expired", code="token_expired") from e
    except (jwt.InvalidTokenError, ValueError) as e:
        raise Unauthorized("invalid token", code="invalid_token") from e
