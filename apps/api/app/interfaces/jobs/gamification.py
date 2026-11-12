from app.bootstrap.tasks import broker
from app.modules.gamification.wiring import build_gamification_service
from app.shared.db import get_sessionmaker


@broker.task(
    task_name="gamification.weekly_rollover",
    schedule=[{"cron": "5 0 * * 1", "cron_offset": "Asia/Tashkent"}],
)
async def weekly_rollover() -> int:
    """Monday 00:05 Tashkent: settle last week's league cohorts (idempotent)."""
    async with get_sessionmaker()() as session:
        svc = build_gamification_service(session)
        settled = 0
        while await svc.settle_next_cohort():  # one short transaction per cohort
            await session.commit()
            settled += 1
        await session.commit()
        return settled
