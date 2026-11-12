import asyncio
from functools import lru_cache

import jwt
from jwt import PyJWKClient

from app.modules.identity.ports import GoogleProfile, GoogleTokenVerifier
from app.shared.errors import Unauthorized

JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
ISSUERS = ("https://accounts.google.com", "accounts.google.com")


class JwksGoogleVerifier:
    """Verifies Google ID tokens (RS256) against Google's published signing keys."""

    def __init__(self, client_id: str) -> None:
        self._client_id = client_id
        self._jwks = PyJWKClient(JWKS_URL, cache_keys=True, lifespan=3600)

    async def verify(self, id_token: str) -> GoogleProfile:
        try:
            key = await asyncio.to_thread(self._jwks.get_signing_key_from_jwt, id_token)
            claims = jwt.decode(
                id_token,
                key.key,
                algorithms=["RS256"],
                audience=self._client_id,
                options={"require": ["exp", "iss", "sub", "aud"]},
            )
        except jwt.PyJWTError as e:
            raise Unauthorized("invalid google token", code="invalid_google_token") from e
        if claims["iss"] not in ISSUERS or not claims.get("email"):
            raise Unauthorized("invalid google token", code="invalid_google_token")
        return GoogleProfile(
            sub=str(claims["sub"]),
            email=claims["email"],
            email_verified=claims.get("email_verified") is True,
            name=str(claims.get("name") or ""),
        )


@lru_cache(maxsize=4)
def _verifier(client_id: str) -> JwksGoogleVerifier:
    return JwksGoogleVerifier(client_id)  # one PyJWKClient per client id keeps its key cache


def build_google_verifier(client_id: str) -> GoogleTokenVerifier | None:
    return _verifier(client_id) if client_id else None
