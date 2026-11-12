from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notify.domain.policy import tashkent_day
from app.modules.notify.infrastructure.repositories import SqlNotifyRepo
from app.shared.events import Event, subscribe


@subscribe("SessionCompleted")
async def on_session_completed(session: AsyncSession, event: Event) -> None:
    """Track the last practice day (Asia/Tashkent) to drive streak reminders. Idempotent per day."""
    await SqlNotifyRepo(session).record_activity(
        UUID(str(event.payload["user_id"])), tashkent_day(event.occurred_at)
    )
