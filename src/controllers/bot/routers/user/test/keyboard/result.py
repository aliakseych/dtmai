from src.controllers.bot.routers.user.menu.callback import Menu
from src.controllers.bot.routers.user.test.callback import OpenSelector

from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup


def get() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Ещё тест", callback_data=OpenSelector().pack()),
        InlineKeyboardButton(text="← Меню", callback_data=Menu().pack()),
    )
    return builder.as_markup()