import random
from datetime import datetime, timezone

from src.controllers.bot.container import Container
from src.controllers.bot.routers.user.test.callback import StartTest
from src.controllers.bot.routers.user.test.router import router
from src.controllers.bot.routers.user.test.states import TestStates
from src.controllers.bot.routers.user.test.utils.question import build_question_content, get_local_progress
from src.controllers.bot.utilities import reply_edit
from src.models.questions.subject import SUBJECT_DISPLAY

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery


@router.callback_query(TestStates.configuring, StartTest.filter())
async def start_test(
    callback: CallbackQuery, container: Container, state: FSMContext,
) -> None:
    data = await state.get_data()
    selected = data["selected_subjects"]

    if not selected:
        await callback.answer("Выбери хотя бы один предмет.", show_alert=True)
        return

    level = None if data["level"] == "MIXED" else data["level"]
    count = data["count"]
    exclude_ids: list[str] = []

    if data["exclude_answered"]:
        user = await container.users.get_by_telegram_id(callback.from_user.id)
        exclude_ids = await container.attempts.get_answered_question_ids(user["id"])

    # Fetch per subject, shuffle within each group, keep subjects consecutive
    questions: list[dict] = []
    subject_parts: list[dict] = []  # [{"subject": "MATH", "count": 10, "start": 0}, ...]
    skipped: list[str] = []

    for subj in selected:
        batch = await container.questions.get_random(
            subject=subj, count=count, level=level, exclude_ids=exclude_ids or None,
        )
        if not batch:
            skipped.append(SUBJECT_DISPLAY.get(subj, subj))
            continue
        random.shuffle(batch)
        subject_parts.append({"subject": subj, "start": len(questions), "count": len(batch)})
        questions.extend(batch)

    if not questions:
        await callback.answer("Нет доступных вопросов по выбранным параметрам.", show_alert=True)
        return

    await state.set_state(TestStates.in_progress)
    await state.update_data(
        questions=questions,
        subject_parts=subject_parts,
        current_index=0,
        answered={},
        started_at=datetime.now(timezone.utc).isoformat(),
    )

    notice = ("⚠️ Нет вопросов по: " + ", ".join(skipped) + "\n\n") if skipped else ""
    local_idx, local_total = get_local_progress(0, subject_parts)
    text, keyboard = build_question_content(questions[0], local_idx, local_total, notice=notice)
    await reply_edit.answer(callback, text=text, reply_markup=keyboard, parse_mode="HTML")