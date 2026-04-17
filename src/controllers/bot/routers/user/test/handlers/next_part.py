from src.controllers.bot.routers.user.test.callback import NextPart
from src.controllers.bot.routers.user.test.router import router
from src.controllers.bot.routers.user.test.states import TestStates
from src.controllers.bot.routers.user.test.utils.question import build_question_content, get_local_progress
from src.controllers.bot.utilities import reply_edit

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery


@router.callback_query(TestStates.in_progress, NextPart.filter())
async def next_part(
    callback: CallbackQuery, state: FSMContext,
) -> None:
    data = await state.get_data()
    idx = data["current_index"]  # already advanced by navigate.py before showing part result
    questions = data["questions"]
    local_idx, local_total = get_local_progress(idx, data["subject_parts"])
    text, keyboard = build_question_content(questions[idx], local_idx, local_total)
    await reply_edit.answer(callback, text=text, reply_markup=keyboard, parse_mode="HTML")