from src.controllers.bot.routers.user.bank.callback import SelectBankSubject
from src.controllers.bot.routers.user.menu.callback import Menu
from src.models.questions.subject import SUBJECT_DISPLAY, Subject

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get(subject_counts: dict[str, int]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for subj in Subject:
        count = subject_counts.get(subj.value, 0)
        display = SUBJECT_DISPLAY.get(subj.value, subj.value)
        builder.row(InlineKeyboardButton(
            text=f"{display} ({count})",
            callback_data=SelectBankSubject(subject=subj.value).pack(),
        ))
    builder.row(InlineKeyboardButton(text="← Меню", callback_data=Menu().pack()))
    return builder.as_markup()