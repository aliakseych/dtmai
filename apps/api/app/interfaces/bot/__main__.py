"""CLI: `uv run python -m app.interfaces.bot set-webhook|delete-webhook|info`."""

import argparse
import asyncio

from aiogram import Bot
from aiogram.types import BotCommand, MenuButtonWebApp, WebAppInfo

from app.interfaces.bot.i18n import LOCALES, t
from app.modules.notify.settings import get_notify_settings
from app.settings import get_settings


async def _run(action: str) -> None:
    s, cfg = get_settings(), get_notify_settings()
    if not s.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set")
    bot = Bot(token=s.telegram_bot_token)
    try:
        if action == "set-webhook":
            if not s.telegram_webhook_secret:
                raise SystemExit("TELEGRAM_WEBHOOK_SECRET is not set")
            await bot.set_webhook(
                cfg.telegram_webhook_url, secret_token=s.telegram_webhook_secret,
                allowed_updates=["message", "callback_query"], drop_pending_updates=False,
            )
            await bot.set_my_commands(
                [BotCommand(command="start", description="Menu"),
                 BotCommand(command="daily", description="Daily question")]
            )
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text=t("en", "open_app").lstrip("📱 "),
                    web_app=WebAppInfo(url=cfg.telegram_mini_app_url),
                )
            )
            print(f"webhook set: {cfg.telegram_webhook_url} (locales: {', '.join(LOCALES)})")
        elif action == "delete-webhook":
            await bot.delete_webhook()
            print("webhook deleted")
        else:
            print(await bot.get_webhook_info())
    finally:
        await bot.session.close()


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.interfaces.bot")
    parser.add_argument("action", choices=["set-webhook", "delete-webhook", "info"])
    asyncio.run(_run(parser.parse_args().action))


if __name__ == "__main__":
    main()
