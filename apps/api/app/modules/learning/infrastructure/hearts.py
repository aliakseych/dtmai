from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.gamification import facade as gamification


class FacadeHearts:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def state(self, user_id: UUID) -> tuple[int, bool]:
        v = await gamification.hearts_state(self._s, user_id)
        return v.count, v.unlimited

    async def lose(self, user_id: UUID) -> int:
        return (await gamification.lose_heart(self._s, user_id)).count
