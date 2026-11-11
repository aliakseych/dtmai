from datetime import time
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

import app.modules.notify.application.handlers  # noqa: F401  (registers event subscribers)
from app.modules.notify.domain.policy import Channel, Kind, Preferences, utcnow
from app.modules.notify.settings import get_notify_settings
from app.modules.notify.wiring import NotifyRepoDep, iter_recipients
from app.shared.audit import audit_admin
from app.shared.db import get_session
from app.shared.deps import CurrentUser, require_role
from app.shared.security import Principal
from app.shared.errors import ProblemDetails

router = APIRouter(tags=["notify"])
admin_router = APIRouter(tags=["notify-admin"])
Admin = Annotated[Principal, Depends(require_role("admin"))]

ERR: dict[int | str, dict[str, Any]] = {
    401: {"model": ProblemDetails, "description": "Unauthorized"},
    403: {"model": ProblemDetails, "description": "Forbidden"},
    422: {"model": ProblemDetails, "description": "Validation failed"},
}


class PreferencesOut(BaseModel):
    enabled: bool
    channels: list[Channel]
    kinds: list[Kind]
    quiet_start: time
    quiet_end: time
    max_per_day: int


class PreferencesIn(BaseModel):
    enabled: bool
    channels: list[Channel] = Field(default_factory=list)
    kinds: list[Kind] = Field(default_factory=lambda: list(Kind))
    quiet_start: time = time(22, 0)
    quiet_end: time = time(8, 0)
    max_per_day: int = Field(default=2, ge=0, le=10)


class DeviceIn(BaseModel):
    token: str = Field(min_length=10, max_length=4096)
    platform: Literal["android", "ios", "web"]


class LinkCodeOut(BaseModel):
    code: str
    deep_link: str
    expires_in: int


def _out(p: Preferences) -> PreferencesOut:
    return PreferencesOut(
        enabled=p.enabled, channels=sorted(p.channels), kinds=sorted(p.kinds),
        quiet_start=p.quiet_start, quiet_end=p.quiet_end, max_per_day=p.max_per_day,
    )


@router.get("/preferences", response_model=PreferencesOut, responses=ERR)
async def get_preferences(user: CurrentUser, repo: NotifyRepoDep) -> PreferencesOut:
    return _out(await repo.get_preferences(user.user_id))


@router.put("/preferences", response_model=PreferencesOut, responses=ERR)
async def put_preferences(
    body: PreferencesIn, user: CurrentUser, repo: NotifyRepoDep
) -> PreferencesOut:
    prefs = Preferences(
        user_id=user.user_id, enabled=body.enabled, channels=set(body.channels),
        kinds=set(body.kinds), quiet_start=body.quiet_start, quiet_end=body.quiet_end,
        max_per_day=body.max_per_day,
    )
    prefs.validate()
    await repo.save_preferences(prefs)
    return _out(prefs)


@router.post("/devices", status_code=204, responses=ERR)
async def register_device(body: DeviceIn, user: CurrentUser, repo: NotifyRepoDep) -> Response:
    await repo.register_device(user.user_id, body.token, body.platform)
    return Response(status_code=204)


@router.delete("/devices", status_code=204, responses=ERR)
async def remove_device(
    user: CurrentUser, repo: NotifyRepoDep, token: Annotated[str, Query(min_length=10)]
) -> Response:
    await repo.remove_device(user.user_id, token)
    return Response(status_code=204)


@router.post("/telegram/link", response_model=LinkCodeOut, responses=ERR)
async def telegram_link(user: CurrentUser, repo: NotifyRepoDep) -> LinkCodeOut:
    cfg = get_notify_settings()
    code = await repo.create_link_code(user.user_id, cfg.link_code_ttl_seconds, utcnow())
    return LinkCodeOut(
        code=code,
        deep_link=f"https://t.me/{cfg.telegram_bot_username}?start=link_{code}",
        expires_in=cfg.link_code_ttl_seconds,
    )


class BroadcastIn(BaseModel):
    channel: Channel
    locale: str | None = None
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=4000)
    dry_run: bool = True


class BroadcastOut(BaseModel):
    recipients: int
    queued: int


@admin_router.post("/broadcast", operation_id="notify_admin_broadcast", responses=ERR)
async def broadcast(
    body: BroadcastIn, who: Admin, session: Annotated[AsyncSession, Depends(get_session)]
) -> BroadcastOut:
    from app.interfaces.jobs.notify import broadcast as broadcast_job
    from app.modules.identity.domain.models import validate_locale

    if body.locale is not None:
        validate_locale(body.locale)
    recipients = 0
    async for _ in iter_recipients(session, body.channel, body.locale):
        recipients += 1
    queued = 0
    if not body.dry_run and recipients:
        await broadcast_job.kiq(body.channel.value, body.locale, body.title, body.body)
        queued = recipients
    audit_admin(
        who, "notify.broadcast", channel=body.channel.value, locale=body.locale,
        dry_run=body.dry_run, recipients=recipients, queued=queued,
    )
    return BroadcastOut(recipients=recipients, queued=queued)
