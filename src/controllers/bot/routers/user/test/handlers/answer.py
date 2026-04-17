from datetime import datetime, timezone

from src.controllers.bot.container import Container
from src.controllers.bot.routers.user.test.callback import AnswerQuestion
from src.controllers.bot.routers.user.test.router import router
from src.controllers.bot.routers.user.test.states import TestStates
from src.controllers.bot.routers.user.test.utils.question import build_verdict_content, get_local_progress
from src.controllers.bot.utilities import reply_edit

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from uuid6 import uuid7


@router.callback_query(TestStates.in_progress, AnswerQuestion.filter())
async def handle_answer(
    callback: CallbackQuery,
    callback_data: AnswerQuestion,
    container: Container,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    questions = data["questions"]
    idx = data["current_index"]
    q = questions[idx]

    if q["id"] in data["answered"]:
        await callback.answer()
        return

    selected = q["answers"][callback_data.index]
    is_correct = selected == q["correct_answer"]

    # DB write first — survives /cancel or FSM loss
    user = await container.users.get_by_telegram_id(callback.from_user.id)
    await container.attempts.create({
        "_id": str(uuid7()),
        "user_id": user["id"],
        "question_id": q["id"],
        "subject": q.get("subject", ""),
        "set_id": None,
        "selected_answer": selected,
        "is_correct": is_correct,
        "answered_at": datetime.now(timezone.utc),
        "time_taken_ms": None,
    })

    answered = dict(data["answered"])
    answered[q["id"]] = {
        "selected": selected,
        "correct": q["correct_answer"],
        "is_correct": is_correct,
        "subject": q.get("subject", ""),
        "category_id": q.get("category_id", ""),
    }
    await state.update_data(answered=answered)

    local_idx, local_total = get_local_progress(idx, data["subject_parts"])
    is_last = idx == len(questions) - 1
    text, keyboard = build_verdict_content(q, local_idx, local_total, is_correct, is_last)
    await reply_edit.answer(callback, text=text, reply_markup=keyboard, parse_mode="HTML")