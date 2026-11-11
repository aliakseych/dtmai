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
    if n:
        await dispatch_pending()
    return n
