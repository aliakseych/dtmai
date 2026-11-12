from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol
from uuid import UUID

import structlog

from app.modules.notify.domain.messages import Message, render
from app.modules.notify.domain.policy import (
    Channel,
    Kind,
    Preferences,
    decide,
    tashkent_day,
    utcnow,
)
from app.modules.notify.ports import EmailSender, PushSender, TelegramSender

log = structlog.get_logger()


@dataclass(frozen=True, slots=True)
class Recipient:
    locale: str
    email: str | None
    telegram_id: int | None


class RecipientLookup(Protocol):
    async def __call__(self, user_id: UUID) -> Recipient | None: ...


class NotifyRepo(Protocol):
    async def get_preferences(self, user_id: UUID) -> Preferences: ...
    async def counts_today(self, user_id: UUID, day: date, kind: Kind) -> tuple[int, bool]: ...
    async def record_delivery(
        self, user_id: UUID, kind: Kind, channel: Channel, day: date
    ) -> None: ...
    async def linked_chat_ids(self, user_id: UUID) -> list[int]: ...
    async def device_tokens(self, user_id: UUID) -> list[str]: ...
    async def drop_token(self, token: str) -> None: ...


class NotifyService:
    def __init__(
        self,
        repo: NotifyRepo,
        lookup: RecipientLookup,
        telegram: TelegramSender,
        push: PushSender,
        email: EmailSender,
    ) -> None:
        self._repo, self._lookup = repo, lookup
        self._tg, self._push, self._email = telegram, push, email

    async def notify(
        self, user_id: UUID, kind: Kind, now: datetime | None = None, **params: object
    ) -> list[Channel]:
        """Fan out over every enabled channel. A notification counts once toward the
        daily cap however many channels it used. Returns the channels delivered."""
        now = now or utcnow()
        prefs = await self._repo.get_preferences(user_id)
        if not prefs.enabled:
            return []
        who = await self._lookup(user_id)
        if who is None:
            return []
        day = tashkent_day(now)
        sent_today, kind_sent = await self._repo.counts_today(user_id, day, kind)
        message = render(kind, who.locale, **params)
        used: list[Channel] = []
        for channel in sorted(prefs.channels):
            verdict = decide(
                prefs, kind, channel, now, sent_today=sent_today, kind_sent_today=kind_sent
            )
            if verdict.allowed and await self._deliver(user_id, channel, who, message):
                used.append(channel)
        if used:
            await self._repo.record_delivery(user_id, kind, used[0], day)
        return used

    async def deliver(
        self, user_id: UUID, channel: Channel, who: Recipient, message: Message
    ) -> bool:
        """Direct delivery for admin broadcasts (bypasses preferences and caps)."""
        return await self._deliver(user_id, channel, who, message)

    async def _deliver(
        self, user_id: UUID, channel: Channel, who: Recipient, message: Message
    ) -> bool:
        try:
            if channel is Channel.TELEGRAM:
                chats = await self._repo.linked_chat_ids(user_id)
                if not chats and who.telegram_id is not None:
                    chats = [who.telegram_id]
                return any([await self._tg.send_telegram(c, message) for c in chats])
            if channel is Channel.PUSH:
                ok = False
                for token in await self._repo.device_tokens(user_id):
                    if await self._push.send_push(token, message):
                        ok = True
                    else:
                        await self._repo.drop_token(token)
                return ok
            if who.email:
                await self._email.send_email(who.email, message)
                return True
        except Exception:  # noqa: BLE001 - one broken channel must not stop the others
            log.exception("notify.channel_failed", channel=channel.value, user_id=str(user_id))
        return False
