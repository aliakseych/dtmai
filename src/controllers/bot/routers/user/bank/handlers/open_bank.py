import asyncio

from src.controllers.bot.container import Container
from src.controllers.bot.routers.user.bank.callback import OpenBank
from src.controllers.bot.routers.user.bank.keyboard import subject as subject_kb
from src.controllers.bot.routers.user.bank.router import router
from src.controllers.bot.utilities import reply_edit
from src.models.questions.subject import Subject

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery


@router.callback_query(OpenBank.filter())
async def open_bank(callback: CallbackQuery, container: Container, state: FSMContext) -> None:
    await state.clear()

    subjects = [subj.value for subj in Subject]
    counts = await asyncio.gather(*[
        container.questions.count_available(subj) for subj in subjects
    ])
    subject_counts = dict(zip(subjects, counts))

    text = "📚 <b>Банк вопросов</b>\n\nВыбери предмет:"
    keyboard = subject_kb.get(subject_counts)
    await reply_edit.answer(callback, text=text, reply_markup=keyboard, parse_mode="HTML")