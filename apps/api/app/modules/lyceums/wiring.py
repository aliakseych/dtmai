from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.domain.models import Role
from app.modules.identity.wiring import build_identity_service
from app.modules.lyceums.application.rep import RepService
from app.modules.lyceums.infrastructure.repositories import (
    SqlLyceumProfiles,
    SqlMemberships,
    SqlPosts,
)


class _SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class _IdentityRoleGranter:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def grant_lyceum_rep(self, user_id: UUID) -> None:
        await build_identity_service(self._session).grant_role(user_id, Role.LYCEUM_REP)


def build_rep_service(session: AsyncSession) -> RepService:
    return RepService(
        SqlLyceumProfiles(session), SqlMemberships(session), SqlPosts(session),
        _IdentityRoleGranter(session), _SystemClock(),
    )
