from src.controllers.bot.container import Container

from aiogram.filters import Filter
from aiogram.types import TelegramObject


class UserExists(Filter):
    """Passes only if the user is (or is not) registered in the database."""

    def __init__(self, exists: bool) -> None:
        self.exists = exists

    async def __call__(self, event: TelegramObject, container: Container) -> bool:
        user = await container.users.get_by_telegram_id(event.from_user.id)
        return (user is not None) is self.exists