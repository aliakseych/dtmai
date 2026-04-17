from src.controllers.bot.container import Container
from src.controllers.bot.routers.user.test.callback import ShowExplanation
from src.controllers.bot.routers.user.test.router import router
from src.controllers.bot.routers.user.test.states import TestStates
from src.controllers.bot.routers.user.test.keyboard import question as question_kb
from src.controllers.bot.utilities import reply_edit
from src.controllers.bot.utilities.latex import render_for_telegram
from src.models.questions.subject import SUBJECT_DISPLAY

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery


@router.callback_query(TestStates.in_progress, ShowExplanation.filter())
async def show_explanation(
    callback: CallbackQuery, container: Container, state: FSMContext,
) -> None:
    data = await state.get_data()
    questions = data["questions"]
    idx = data["current_index"]
    q = questions[idx]
    is_last = idx == len(questions) - 1

    full = await container.questions.get_by_id(q["id"])
    steps = full.get("solution_steps") if full else None

    if not steps:
        await callback.answer("Объяснение отсутствует.", show_alert=True)
        return

    subject_label = SUBJECT_DISPLAY.get(q.get("subject", ""), "")
    lines = [f"<b>{subject_label}</b> — объяснение\n"]
    for i, step in enumerate(steps, 1):
        lines.append(f"<b>Шаг {i}.</b> {render_for_telegram(step['action'])}")
        if step.get("formula"):
            lines.append(f"<code>{render_for_telegram(step['formula'])}</code>")
        if step.get("explanation"):
            lines.append(f"<i>{render_for_telegram(step['explanation'])}</i>")
        lines.append("")

    is_correct = data["answered"].get(q["id"], {}).get("is_correct", False)
    verdict = "✅ Правильно!" if is_correct else f"❌ Правильный ответ: <b>{render_for_telegram(q['correct_answer'])}</b>"
    lines.append(verdict)

    keyboard = question_kb.get_after_answer(has_steps=False, is_last=is_last)
    await reply_edit.answer(callback, text="\n".join(lines), reply_markup=keyboard, parse_mode="HTML")