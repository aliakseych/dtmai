from uuid import UUID

import structlog

import app.modules.notify.application.handlers  # noqa: F401  (registers event subscribers)
from app.bootstrap.tasks import broker
from app.modules.notify.application.service import NotifyService
from app.modules.notify.domain.messages import Message
from app.modules.notify.domain.policy import Channel, Kind, reminder_due, tashkent_day, utcnow
from app.modules.notify.infrastructure.repositories import SqlNotifyRepo
from app.modules.notify.wiring import build_notify_service, iter_recipients
from app.modules.study_plan.facade import study_schedules
from app.shared.db import get_sessionmaker

log = structlog.get_logger()
BATCH = 200
REMINDER_LABEL = [{"cron": "*/30 * * * *", "cron_offset": "Asia/Tashkent"}]
WEEKLY_LABEL = [{"cron": "0 18 * * 0", "cron_offset": "Asia/Tashkent"}]


async def _fan_out(kind: Kind) -> int:
    sent = 0
    now = utcnow()
    today = tashkent_day(now)
    after: UUID | None = None
    while True:
        async with get_sessionmaker()() as session:
            repo = SqlNotifyRepo(session)
            if kind is Kind.STREAK_REMINDER:
                batch = [(u, s) for u, s, _ in await repo.at_risk(today, BATCH, after)]
            else:
                batch = [(u, 0) for u in await repo.opted_in_users(BATCH, after)]
            if not batch:
                return sent
            service: NotifyService = build_notify_service(session)
            schedules = (
                await study_schedules(session, [u for u, _ in batch])
                if kind is Kind.STREAK_REMINDER
                else {}
            )
            for user_id, streak in batch:
                if kind is Kind.STREAK_REMINDER and not reminder_due(
                    now, *(schedules.get(user_id) or (None, ()))
                ):
                    continue
                params = {"streak": streak} if kind is Kind.STREAK_REMINDER else {}
                if await service.notify(user_id, kind, now, **params):
                    sent += 1
            await session.commit()
            after = batch[-1][0]


@broker.task(task_name="notify.streak_reminders", schedule=REMINDER_LABEL)
async def streak_reminders() -> int:
    """Runs every 30 minutes; each learner is reminded in their own study_time slot (default 19:00)."""
    sent = await _fan_out(Kind.STREAK_REMINDER)
    log.info("notify.streak_reminders", sent=sent)
    return sent


@broker.task(task_name="notify.league_ending", schedule=WEEKLY_LABEL)
async def league_ending() -> int:
    sent = await _fan_out(Kind.LEAGUE_ENDING)
    log.info("notify.league_ending", sent=sent)
    return sent


@broker.task(task_name="notify.broadcast")
async def broadcast(channel: str, locale: str | None, title: str, body: str) -> int:
    """Admin broadcast: delivers to every reachable user on one channel."""
    ch, message, sent = Channel(channel), Message(title, body), 0
    async with get_sessionmaker()() as session:
        service: NotifyService = build_notify_service(session)
        async for user_id, who in iter_recipients(session, ch, locale):
            if await service.deliver(user_id, ch, who, message):
                sent += 1
        await session.commit()
    log.info("notify.broadcast", channel=channel, locale=locale, sent=sent)
    return sent
