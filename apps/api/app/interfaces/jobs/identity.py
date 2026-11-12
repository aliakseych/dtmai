from app.bootstrap.tasks import broker
from app.modules.identity.wiring import build_identity_service
from app.shared.db import get_sessionmaker


@broker.task(
    task_name="identity.cleanup_guests",
    schedule=[{"cron": "30 3 * * *", "cron_offset": "Asia/Tashkent"}],
)
async def cleanup_guests() -> int:
    """03:30 Tashkent daily: delete guest accounts unseen for more than 30 days."""
    async with get_sessionmaker()() as session:
        deleted = await build_identity_service(session).cleanup_guests()
        await session.commit()
        return deleted
