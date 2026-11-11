import hmac
from functools import lru_cache
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, Request

from app.interfaces.bot.handlers import router as handlers_router
from app.settings import get_settings
from app.shared.errors import Forbidden, NotFound, ProblemDetails

SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"

router = APIRouter(tags=["telegram"])


@lru_cache
def get_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(handlers_router)
    return dp


@lru_cache
def get_bot() -> Bot:
    return Bot(token=get_settings().telegram_bot_token)


def secret_matches(expected: str, provided: str | None) -> bool:
    """Constant-time check; an unconfigured secret never matches."""
    return bool(expected) and provided is not None and hmac.compare_digest(expected, provided)


@router.post(
    "/tg/webhook",
    include_in_schema=False,
    responses={403: {"model": ProblemDetails}, 404: {"model": ProblemDetails}},
)
async def telegram_webhook(request: Request) -> dict[str, Any]:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise NotFound("bot is not configured", code="bot_disabled")
    if not secret_matches(settings.telegram_webhook_secret, request.headers.get(SECRET_HEADER)):
        raise Forbidden("bad secret token", code="bad_webhook_secret")
    update = Update.model_validate(await request.json(), context={"bot": get_bot()})
    await get_dispatcher().feed_update(get_bot(), update)
    return {"ok": True}
