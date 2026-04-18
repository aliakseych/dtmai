import uuid
from typing import Any

from src.settings import settings

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject


class ErrorMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler,
        event: TelegramObject,
        data: dict[str, Any],
    ):
        try:
            return await handler(event, data)

        except Exception as e:
            # Ignore stale callback query errors — Telegram fires these when
            # a response timeout expires on an old inline button press.
            if "query is too old" in str(e):
                return None
            if "message is not modified" in str(e):
                return None

            error_uuid = str(uuid.uuid4())
            bot: Bot = data["bot"]

            try:
                await bot.send_message(
                    settings.ADMINS_IDS[0],
                    f"⚠️ Error [{error_uuid}]\n{type(e).__name__}: {e}\n\nEvent: "
                    f"{event[:3900]}",
                )
            except Exception:
                print(error_uuid, e, event)

            user = data.get("event_from_user")
            if user:
                try:
                    await bot.send_message(
                        user.id,
                        f"⚠️ Произошла ошибка. Попробуйте ещё раз или вернитесь в меню: /menu\n\n"
                        f"ID ошибки: {error_uuid}",
                    )
                except Exception:
                    pass

            return None