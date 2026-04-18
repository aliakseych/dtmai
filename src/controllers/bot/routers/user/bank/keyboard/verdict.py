from src.controllers.bot.routers.user.bank.callback import BackToBankList
from src.controllers.bot.routers.user.test.callback import ShowExplanation

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get(has_steps: bool, page: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_steps:
        builder.row(InlineKeyboardButton(
            text="🔍 Объяснение", callback_data=ShowExplanation().pack(),
        ))
    builder.row(InlineKeyboardButton(
        text="← К списку", callback_data=BackToBankList(page=page).pack(),
    ))
    return builder.as_markup()