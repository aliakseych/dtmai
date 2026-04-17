from src.controllers.bot.routers.default.router import router

from aiogram import Bot
from aiogram.filters import StateFilter, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.methods import DeclineChatJoinRequest


@router.message(StateFilter(None), Command(commands=["cancel"]))
async def cancel_nothing(message: Message) -> None:
    """Handle requests, that should cancel state info, but there is none."""

    text = "Нечего отменять, но.. хорошо?\n\nУспешно отменено!"

    await message.reply(text)

@router.message(StateFilter("*"), Command(commands=["cancel"]))
async def cancel(message: Message, state: FSMContext, bot: Bot) -> None:
    """Handle requests, that should cancel state info."""

    text = "Успешно отменено!"

    # Clearing FSM data
    await state.clear()

    await message.reply(text)
