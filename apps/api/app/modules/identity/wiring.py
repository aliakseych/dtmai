from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.application.service import IdentityConfig, IdentityService
from app.modules.lyceums.city_wiring import build_city_catalog
from app.modules.identity.infrastructure.clock import SystemClock
from app.modules.identity.infrastructure.mail import build_mailer
from app.modules.identity.infrastructure.passwords import Argon2Hasher
from app.modules.identity.infrastructure.repositories import (
    SqlEmailCodeRepository,
    SqlRefreshTokenRepository,
    SqlUserRepository,
)
from app.settings import get_settings
from app.shared.db import get_session


def build_identity_service(session: AsyncSession) -> IdentityService:
    s = get_settings()
    return IdentityService(
        SqlUserRepository(session),
        SqlEmailCodeRepository(session),
        SqlRefreshTokenRepository(session),
        Argon2Hasher(),
        build_mailer(s),
        SystemClock(),
        IdentityConfig(
            access_ttl=s.access_ttl_seconds,
            refresh_ttl=s.refresh_ttl_seconds,
            code_ttl=s.email_code_ttl_seconds,
            code_max_attempts=s.email_code_max_attempts,
            bot_token=s.telegram_bot_token,
            init_data_max_age=s.telegram_init_data_max_age_seconds,
            jwt_secret=s.jwt_secret,
        ),
        build_city_catalog(session),
    )


async def get_identity_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> IdentityService:
    return build_identity_service(session)


IdentityServiceDep = Annotated[IdentityService, Depends(get_identity_service)]
