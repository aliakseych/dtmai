from app.bootstrap.tasks import broker
from app.modules.assessment.wiring import build_assessment_service
from app.shared.db import get_sessionmaker
from app.shared.events import dispatch_pending


@broker.task(task_name="assessment.auto_submit_expired", schedule=[{"cron": "* * * * *"}])
async def auto_submit_expired() -> int:
    """Server-side deadline enforcement: submit attempts whose time ran out."""
    async with get_sessionmaker()() as session:
        n = await build_assessment_service(session).auto_submit_expired()
        await session.commit()
    await dispatch_pending()
    return n


@broker.task(task_name="events.dispatch_pending", schedule=[{"cron": "* * * * *"}])
async def dispatch_outbox() -> int:
    """Deliver outbox events from every module (the one dispatcher; handlers are idempotent)."""
    return await dispatch_pending()
