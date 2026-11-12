from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.domain.models import Role
from app.modules.identity.wiring import build_identity_service
from app.modules.lyceums.application.admission import AdmissionService
from app.modules.lyceums.application.profile import ProfileService
from app.modules.lyceums.application.rep import RepService
from app.modules.lyceums.infrastructure.admission import SqlAdmissionStore, load_seed_docs
from app.modules.lyceums.infrastructure.repositories import (
    SqlCities,
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

    async def revoke_lyceum_rep(self, user_id: UUID) -> None:
        await build_identity_service(self._session).revoke_role(user_id, Role.LYCEUM_REP)

    async def has_lyceum_rep(self, user_id: UUID) -> bool:
        user = await build_identity_service(self._session).get_me(user_id)
        return Role.LYCEUM_REP in user.roles


def build_profile_service(session: AsyncSession) -> ProfileService:
    return ProfileService(SqlLyceumProfiles(session), SqlCities(session))


def build_rep_service(session: AsyncSession) -> RepService:
    return RepService(
        SqlLyceumProfiles(session),
        SqlMemberships(session),
        SqlPosts(session),
        _IdentityRoleGranter(session),
        build_profile_service(session),
        _SystemClock(),
    )


def build_admission_service(session: AsyncSession) -> AdmissionService:
    return AdmissionService(SqlAdmissionStore(session), load_seed_docs)
