import uuid
from datetime import date, datetime, time

from sqlalchemy import JSON, BigInteger, Boolean, Date, DateTime, Integer, String, Text, Time, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base

SCHEMA = "notify"


class PreferencesRow(Base):
    __tablename__ = "preferences"
    __table_args__ = {"schema": SCHEMA}

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    channels: Mapped[list[str]] = mapped_column(JSON, default=list)
    kinds: Mapped[list[str]] = mapped_column(JSON, default=list)
    quiet_start: Mapped[time] = mapped_column(Time, default=time(22, 0))
    quiet_end: Mapped[time] = mapped_column(Time, default=time(8, 0))
    max_per_day: Mapped[int] = mapped_column(Integer, default=2)


class DeviceRow(Base):
    __tablename__ = "devices"
    __table_args__ = {"schema": SCHEMA}

    token: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    platform: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TelegramChatRow(Base):
    __tablename__ = "telegram_chats"
    __table_args__ = {"schema": SCHEMA}

    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    locale: Mapped[str] = mapped_column(String(10), default="uz-Latn")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LinkCodeRow(Base):
    __tablename__ = "link_codes"
    __table_args__ = {"schema": SCHEMA}

    code: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ActivityRow(Base):
    __tablename__ = "activity"
    __table_args__ = {"schema": SCHEMA}

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    last_day: Mapped[date] = mapped_column(Date)
    streak: Mapped[int] = mapped_column(Integer, default=0)


class DeliveryRow(Base):
    __tablename__ = "deliveries"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    kind: Mapped[str] = mapped_column(String(32))
    channel: Mapped[str] = mapped_column(String(10))
    day: Mapped[date] = mapped_column(Date, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
