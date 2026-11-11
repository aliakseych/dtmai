import logging

from app.bootstrap.tasks import broker
from app.modules.study_plan.wiring import build_plan_service
from app.shared.db import get_sessionmaker

log = logging.getLogger(__name__)


@broker.task(
    task_name="study_plan.replan_all",
    schedule=[{"cron": "0 3 * * *", "cron_offset": "Asia/Tashkent"}],
)
async def replan_all() -> int:
    """Nightly: refresh every running plan from today, one transaction per plan."""
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        user_ids = await build_plan_service(session).stale_plan_users()
    done = 0
    for user_id in user_ids:
        try:
            async with sessionmaker() as session:
                if await build_plan_service(session).replan_user(user_id):
                    done += 1
                await session.commit()
        except Exception:  # one broken plan must not stop the rest of the run
            log.exception("study plan replan failed", extra={"user_id": str(user_id)})
    return done
