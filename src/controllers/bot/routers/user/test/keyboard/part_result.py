from src.controllers.bot.routers.user.test.callback import NextPart
from src.models.questions.subject import SUBJECT_DISPLAY

from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup


def get(next_subject: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    next_display = SUBJECT_DISPLAY.get(next_subject, next_subject)
    builder.row(InlineKeyboardButton(
        text=f"Продолжить: {next_display} →",
        callback_data=NextPart().pack(),
    ))
    return builder.as_markup()