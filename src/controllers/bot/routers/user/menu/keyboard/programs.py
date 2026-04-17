from src.controllers.bot.routers.user.menu.callback import Menu, SelectProgram

from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup


def get(programs: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for prog in programs:
        builder.row(InlineKeyboardButton(
            text=prog["name"],
            callback_data=SelectProgram(program_id=prog["id"]).pack()
        ))
    builder.row(InlineKeyboardButton(text="← Назад", callback_data=Menu().pack()))
    return builder.as_markup()