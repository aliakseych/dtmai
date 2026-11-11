import secrets
from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notify.domain.policy import Channel, Kind, Preferences
from app.modules.notify.infrastructure.orm import (
    ActivityRow,
    DeliveryRow,
    DeviceRow,
    LinkCodeRow,
    PreferencesRow,
    TelegramChatRow,
)
from app.shared.ids import new_id


class SqlNotifyRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # preferences
    async def get_preferences(self, user_id: UUID) -> Preferences:
        row = await self._s.get(PreferencesRow, user_id)
        if row is None:
            return Preferences(user_id=user_id)
        return Preferences(
            user_id=user_id, enabled=row.enabled,
            channels={Channel(c) for c in row.channels}, kinds={Kind(k) for k in row.kinds},
            quiet_start=row.quiet_start, quiet_end=row.quiet_end, max_per_day=row.max_per_day,
        )

    async def save_preferences(self, p: Preferences) -> None:
        assert isinstance(p.user_id, UUID)
        row = await self._s.get(PreferencesRow, p.user_id)
        if row is None:
            row = PreferencesRow(user_id=p.user_id)
            self._s.add(row)
        row.enabled = p.enabled
        row.channels = sorted(c.value for c in p.channels)
        row.kinds = sorted(k.value for k in p.kinds)
        row.quiet_start, row.quiet_end, row.max_per_day = p.quiet_start, p.quiet_end, p.max_per_day
        await self._s.flush()

    # devices
    async def register_device(self, user_id: UUID, token: str, platform: str) -> None:
        stmt = insert(DeviceRow).values(token=token, user_id=user_id, platform=platform)
        await self._s.execute(
            stmt.on_conflict_do_update(
                index_elements=[DeviceRow.token], set_={"user_id": user_id, "platform": platform}
            )
        )

    async def remove_device(self, user_id: UUID, token: str) -> None:
        await self._s.execute(
            delete(DeviceRow).where(DeviceRow.token == token, DeviceRow.user_id == user_id)
        )

    async def drop_token(self, token: str) -> None:
        await self._s.execute(delete(DeviceRow).where(DeviceRow.token == token))

    async def device_tokens(self, user_id: UUID) -> list[str]:
        return list(await self._s.scalars(select(DeviceRow.token).where(DeviceRow.user_id == user_id)))

    # telegram chats + linking
    async def upsert_chat(self, chat_id: int, locale: str) -> None:
        stmt = insert(TelegramChatRow).values(chat_id=chat_id, locale=locale)
        await self._s.execute(
            stmt.on_conflict_do_update(index_elements=[TelegramChatRow.chat_id],
                                       set_={"locale": locale})
        )

    async def chat(self, chat_id: int) -> TelegramChatRow | None:
        return await self._s.get(TelegramChatRow, chat_id)

    async def linked_chat_ids(self, user_id: UUID) -> list[int]:
        return list(await self._s.scalars(
            select(TelegramChatRow.chat_id).where(TelegramChatRow.user_id == user_id)
        ))

    async def user_for_chat(self, chat_id: int) -> UUID | None:
        row = await self._s.get(TelegramChatRow, chat_id)
        return row.user_id if row else None

    async def create_link_code(self, user_id: UUID, ttl_seconds: int, now: datetime) -> str:
        code = secrets.token_urlsafe(12)
        self._s.add(LinkCodeRow(code=code, user_id=user_id,
                                expires_at=now + timedelta(seconds=ttl_seconds)))
        await self._s.flush()
        return code

    async def consume_link_code(self, code: str, chat_id: int, now: datetime) -> UUID | None:
        row = await self._s.get(LinkCodeRow, code)
        if row is None:
            return None
        user_id, expires = row.user_id, row.expires_at
        await self._s.delete(row)
        if expires < now:
            return None
        await self._s.execute(
            update(TelegramChatRow).where(TelegramChatRow.chat_id == chat_id).values(user_id=user_id)
        )
        return user_id

    # activity (streak tracking for reminders)
    async def record_activity(self, user_id: UUID, today: date) -> None:
        row = await self._s.get(ActivityRow, user_id)
        if row is None:
            self._s.add(ActivityRow(user_id=user_id, last_day=today, streak=1))
        elif row.last_day == today:
            return
        else:
            row.streak = row.streak + 1 if row.last_day == today - timedelta(days=1) else 1
            row.last_day = today
        await self._s.flush()

    async def at_risk(self, today: date, limit: int, after: UUID | None) -> list[tuple[UUID, int, date]]:
        """Users with a streak who have not practised on `today` (keyset-paged by user_id)."""
        stmt = (
            select(ActivityRow.user_id, ActivityRow.streak, ActivityRow.last_day)
            .where(ActivityRow.last_day < today, ActivityRow.streak > 0)
            .order_by(ActivityRow.user_id).limit(limit)
        )
        if after is not None:
            stmt = stmt.where(ActivityRow.user_id > after)
        return [(r[0], r[1], r[2]) for r in await self._s.execute(stmt)]

    async def opted_in_users(self, limit: int, after: UUID | None) -> list[UUID]:
        stmt = (
            select(PreferencesRow.user_id).where(PreferencesRow.enabled.is_(True))
            .order_by(PreferencesRow.user_id).limit(limit)
        )
        if after is not None:
            stmt = stmt.where(PreferencesRow.user_id > after)
        return list(await self._s.scalars(stmt))

    # deliveries
    async def counts_today(self, user_id: UUID, day: date, kind: Kind) -> tuple[int, bool]:
        rows = await self._s.execute(
            select(DeliveryRow.kind, func.count()).where(
                DeliveryRow.user_id == user_id, DeliveryRow.day == day
            ).group_by(DeliveryRow.kind)
        )
        by_kind = {k: n for k, n in rows}
        return sum(by_kind.values()), by_kind.get(kind.value, 0) > 0

    async def record_delivery(self, user_id: UUID, kind: Kind, channel: Channel, day: date) -> None:
        self._s.add(DeliveryRow(id=new_id(), user_id=user_id, kind=kind.value,
                                channel=channel.value, day=day))
        await self._s.flush()

