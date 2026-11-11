from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.gamification.ports import Profile
from app.shared.errors import NotFound


class IdentityProfile:
    """Reads display name and target lyceum through the identity application service."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: UUID) -> Profile | None:
        from app.modules.identity.wiring import build_identity_service

        try:
            user = await build_identity_service(self._session).get_me(user_id)
        except NotFound:
            return None
        return Profile(user.name, user.target_lyceum_id)
