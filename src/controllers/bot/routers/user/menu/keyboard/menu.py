from src.controllers.bot.routers.user.bank.callback import OpenBank
from src.controllers.bot.routers.user.menu.callback import ProgramsList
from src.controllers.bot.routers.user.stats.callback import Stats
from src.controllers.bot.routers.user.test.callback import OpenSelector

from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup


def get() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🧩 Сгенерировать тест", callback_data=OpenSelector().pack()
    ))
    builder.row(InlineKeyboardButton(
        text="📋 По направлениям", callback_data=ProgramsList().pack()
    ))
    builder.row(InlineKeyboardButton(
        text="📚 Банк вопросов", callback_data=OpenBank().pack()
    ))
    builder.row(InlineKeyboardButton(
        text="📊 Статистика", callback_data=Stats().pack()
    ))
    return builder.as_markup()