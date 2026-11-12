"""In-process domain events with a transactional outbox.

Contract (frozen for all modules):
- Producers call `await publish(session, Event(...))` inside their unit of work; the row is
  written to `shared.outbox` in the same transaction.
- Consumers register with `@subscribe("AttemptGraded")`; `dispatch_pending()` (taskiq job / after
  commit) delivers each event at-least-once, so handlers MUST be idempotent (key on event.id).
- Modules never import each other's ORM models; cross-module data travels in event payloads or
  through ports.
"""

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, String, Uuid, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base, get_sessionmaker


@dataclass(frozen=True, slots=True)
class Event:
    name: str  # e.g. "AttemptGraded", "SessionCompleted", "EntitlementGranted"
    payload: dict[str, Any]
    id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class OutboxRow(Base):
    __tablename__ = "outbox"
    __table_args__ = {"schema": "shared"}

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


Handler = Callable[[AsyncSession, Event], Awaitable[None]]
_handlers: dict[str, list[Handler]] = {}


def subscribe(name: str) -> Callable[[Handler], Handler]:
    def deco(fn: Handler) -> Handler:
        _handlers.setdefault(name, []).append(fn)
        return fn

    return deco


async def publish(session: AsyncSession, event: Event) -> None:
    session.add(
        OutboxRow(
            id=event.id, name=event.name, payload=event.payload, occurred_at=event.occurred_at
        )
    )


async def dispatch_pending(limit: int = 200) -> int:
    """Deliver undispatched events; each event's handlers run in one transaction."""
    done = 0
    async with get_sessionmaker()() as session:
        rows = (
            await session.scalars(
                select(OutboxRow)
                .where(OutboxRow.dispatched_at.is_(None))
                .order_by(OutboxRow.occurred_at)
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
        ).all()
        for row in rows:
            ev = Event(name=row.name, payload=row.payload, id=row.id, occurred_at=row.occurred_at)
            for h in _handlers.get(row.name, []):
                await h(session, ev)
            row.dispatched_at = datetime.now(UTC)
            done += 1
        await session.commit()
    return done


async def commit_and_dispatch(session: AsyncSession) -> None:
    """Commit the request's unit of work, then deliver the outbox in-process.

    Crediting (XP, streak, quests) must not wait for the scheduler. Dispatch is best-effort:
    a failure leaves rows undispatched and the scheduled job redelivers them (handlers are
    idempotent on event.id).
    """
    await session.commit()
    try:
        await dispatch_pending()
    except Exception:  # noqa: BLE001 - the committed request must still succeed
        logging.getLogger(__name__).exception("in-process outbox dispatch failed")
