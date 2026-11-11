from uuid import UUID

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from app.interfaces.bot.i18n import LOCALE_LABELS, t

# Telegram limits callback_data to 64 bytes: "dq:" + 32 hex + ":" + idx fits easily.
PREFIX_QUESTION = "dq"
PREFIX_LANG = "lang"
MENU_DAILY, MENU_LANG, MENU_HELP, MENU_REMINDERS = "menu:daily", "menu:lang", "menu:help", "menu:rem"


def question_data(question_id: UUID, option_index: int) -> str:
    return f"{PREFIX_QUESTION}:{question_id.hex}:{option_index}"


def parse_question_data(data: str) -> tuple[UUID, int] | None:
    parts = data.split(":")
    if len(parts) != 3 or parts[0] != PREFIX_QUESTION:
        return None
    try:
        return UUID(hex=parts[1]), int(parts[2])
    except ValueError:
        return None


def main_menu(locale: str, app_url: str, *, reminders_on: bool) -> InlineKeyboardMarkup:
    rem_label = t(locale, "reminders_on" if reminders_on else "reminders_off")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(locale, "open_app"), web_app=WebAppInfo(url=app_url))],
            [InlineKeyboardButton(text=t(locale, "daily"), callback_data=MENU_DAILY)],
            [InlineKeyboardButton(text=rem_label, callback_data=MENU_REMINDERS)],
            [
                InlineKeyboardButton(text=t(locale, "language"), callback_data=MENU_LANG),
                InlineKeyboardButton(text=t(locale, "help"), callback_data=MENU_HELP),
            ],
        ]
    )


def language_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"{PREFIX_LANG}:{code}")]
            for code, label in LOCALE_LABELS.items()
        ]
    )


def question_keyboard(question_id: UUID, labels: list[str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label[:60], callback_data=question_data(question_id, i))]
            for i, label in enumerate(labels)
        ]
    )
