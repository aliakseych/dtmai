from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.shared.errors import Forbidden, Unauthorized
from app.shared.security import Principal, decode_access_token

_bearer = HTTPBearer(auto_error=False)


async def current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Principal:
    if creds is None:
        raise Unauthorized("missing bearer token", code="missing_token")
    return decode_access_token(creds.credentials)


CurrentUser = Annotated[Principal, Depends(current_user)]


async def optional_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Principal | None:
    return None if creds is None else decode_access_token(creds.credentials)


OptionalUser = Annotated[Principal | None, Depends(optional_user)]


def has_any_role(held: set[str] | frozenset[str], required: tuple[str, ...]) -> bool:
    """Pure role check used by `require_role`."""
    return bool(set(held).intersection(required))


def require_role(*roles: str) -> Callable[..., Coroutine[Any, Any, Principal]]:
    async def dep(user: CurrentUser) -> Principal:
        if not has_any_role(user.roles, roles):
            raise Forbidden("insufficient role", code="role_required")
        return user

    return dep
