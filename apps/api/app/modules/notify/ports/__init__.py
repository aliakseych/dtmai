from typing import Protocol

from app.modules.notify.domain.messages import Message


class TelegramSender(Protocol):
    async def send_telegram(self, chat_id: int, message: Message) -> bool: ...


class PushSender(Protocol):
    async def send_push(self, token: str, message: Message) -> bool:
        """False when the token is dead and should be dropped."""
        ...


class EmailSender(Protocol):
    async def send_email(self, to: str, message: Message) -> None: ...
