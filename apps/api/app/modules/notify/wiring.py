from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notify.application.service import NotifyService, Recipient, RecipientLookup
from app.modules.notify.domain.policy import Channel
from app.modules.notify.infrastructure.channels import FcmPush, MailerEmail, TelegramBotApi
from app.modules.notify.infrastructure.repositories import SqlNotifyRepo
from app.modules.notify.settings import get_notify_settings
from app.settings import get_settings
from app.shared.db import get_session
from app.shared.errors import NotFound


def identity_lookup(session: AsyncSession) -> RecipientLookup:
    # Reads the user through identity's application service (no ORM access).
    from app.modules.identity.wiring import build_identity_service

    svc = build_identity_service(session)

    async def lookup(user_id: UUID) -> Recipient | None:
        try:
            user = await svc.get_me(user_id)
        except NotFound:
            return None
        return Recipient(user.locale, user.email, user.telegram_id)

    return lookup


async def iter_recipients(
    session: AsyncSession, channel: Channel, locale: str | None
) -> AsyncIterator[tuple[UUID, Recipient]]:
    """Users reachable on `channel` (optionally one locale), keyset-paged by user id."""
    from app.modules.identity.wiring import build_identity_service

    ident, repo = build_identity_service(session), SqlNotifyRepo(session)
    after: UUID | None = None
    while True:
        users = await ident.contacts(after, 500, locale, with_email=channel is Channel.EMAIL)
        if not users:
            return
        after = users[-1].id
        for u in users:
            if channel is Channel.TELEGRAM and u.telegram_id is None and not await repo.linked_chat_ids(u.id):
                continue
            if channel is Channel.PUSH and not await repo.device_tokens(u.id):
                continue
            yield u.id, Recipient(u.locale, u.email, u.telegram_id)


def build_notify_service(session: AsyncSession) -> NotifyService:
    cfg = get_notify_settings()
    return NotifyService(
        SqlNotifyRepo(session),
        identity_lookup(session),
        TelegramBotApi(get_settings().telegram_bot_token, cfg),
        FcmPush(cfg),
        MailerEmail(),
    )


def get_notify_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> SqlNotifyRepo:
    return SqlNotifyRepo(session)


NotifyRepoDep = Annotated[SqlNotifyRepo, Depends(get_notify_repo)]
