from datetime import datetime, timezone

from src.controllers.bot.container import Container
from src.controllers.bot.filters.user_exists import UserExists
from src.controllers.bot.routers.user.registration.router import router
from src.controllers.bot.routers.user.menu.keyboard import menu as menu_kb
from src.controllers.bot.utilities import reply_edit

from aiogram import F
from aiogram.filters import CommandStart
from aiogram.types import Message

import uuid6

from src.settings import settings


@router.message(CommandStart(), UserExists(exists=False), F.chat.type == "private")
async def start(message: Message, container: Container) -> None:
    user_id = str(uuid6.uuid7())
    now = datetime.now(timezone.utc)

    await container.users.create({
        "_id": user_id,
        "telegram_id": message.from_user.id,
        "created_at": now,
    })

    name = (message.from_user.first_name or "друг").split()[0]
    text = (
        f"👋 Привет, {name}!\n"
        "Добро пожаловать в <b>DTM AI</b> — бесплатный тренажёр для подготовки к вступительным экзаменам в лицей.\n\n"
        "Здесь ты найдёшь:\n"
        "• 📚 Банк вопросов по математике и английскому\n"
        "• 🧩 Конструктор собственных тестов\n"
        "• 📋 Готовые программы по направлениям\n"
        "• 📊 Статистику с прогнозом баллов\n\n"
        "Нажми кнопку ниже, чтобы начать 👇\n\n"
        "<i>Сделано с ❤️ командой Alternative лицея \"International House - Tashkent\" "
        "(<a href=\"https://t.me/altiht\">@altiht</a>)</i>"
    )

    await message.bot.send_message(
        chat_id=settings.ADMINS_IDS[0],
        text=f"Зарегистрирован новый пользователь!\n"
             f"{"@" + message.from_user.username if 
             message.from_user.username else message.from_user.full_name}"
    )

    await reply_edit.answer(message, text=text, reply_markup=menu_kb.get(), parse_mode="HTML")
