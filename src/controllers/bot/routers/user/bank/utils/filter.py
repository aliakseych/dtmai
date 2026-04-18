from src.controllers.bot.routers.user.bank.keyboard import filter as filter_kb
from src.models.questions.subject import SUBJECT_DISPLAY

from aiogram.types import InlineKeyboardMarkup


def build_filter_content(
    subject: str,
    level_filter: str | None,
    solved_filter: str,
    total: int | None = None,
) -> tuple[str, InlineKeyboardMarkup]:
    subj_name = SUBJECT_DISPLAY.get(subject, subject)
    counter = f"Вопросов в базе: <b>{total}</b>\n\n" if total is not None else ""
    text = (
        f"📚 <b>Банк вопросов</b> — {subj_name}\n\n"
        f"{counter}"
        "Настрой фильтры и нажми <b>\"Поиск\"</b>.\n"
        "Или нажми <b>\"Показать всё\"</b> без фильтров."
    )
    keyboard = filter_kb.get(subject, level_filter, solved_filter)
    return text, keyboard
