from src.controllers.bot.routers.user.menu.callback import Menu
from src.controllers.bot.routers.user.menu.router import router
from src.controllers.bot.routers.user.menu.keyboard import menu as menu_kb
from src.controllers.bot.utilities import reply_edit

from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery


@router.message(Command(commands=["menu", "start"]), F.chat.type == "private")
@router.callback_query(Menu.filter())
async def menu(request: Message | CallbackQuery) -> None:
    name = (request.from_user.first_name or "друг").split()[0]
    text = f"👋 Привет, {name}! Выбери действие:"
    await reply_edit.answer(request, text=text, reply_markup=menu_kb.get())
