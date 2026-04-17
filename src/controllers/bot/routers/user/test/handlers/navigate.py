from src.controllers.bot.container import Container
from src.controllers.bot.routers.user.test.callback import NextQuestion
from src.controllers.bot.routers.user.test.router import router
from src.controllers.bot.routers.user.test.states import TestStates
from src.controllers.bot.routers.user.test.utils.question import build_question_content, get_local_progress
from src.controllers.bot.routers.user.test.utils.result import aggregate_results, build_result_text, build_part_result_text
from src.controllers.bot.routers.user.test.keyboard import result as result_kb
from src.controllers.bot.routers.user.test.keyboard import part_result as part_result_kb
from src.controllers.bot.utilities import reply_edit

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery


@router.callback_query(TestStates.in_progress, NextQuestion.filter())
async def next_question(
    callback: CallbackQuery, container: Container, state: FSMContext,
) -> None:
    data = await state.get_data()
    idx = data["current_index"]
    questions = data["questions"]
    subject_parts = data["subject_parts"]
    new_idx = idx + 1

    await state.update_data(current_index=new_idx)

    # All questions done — final result
    if new_idx >= len(questions):
        cat_names = await _fetch_cat_names(questions, container)
        stats = aggregate_results(questions, data["answered"])
        text = build_result_text(stats, cat_names)
        await state.clear()
        await reply_edit.answer(callback, text=text, reply_markup=result_kb.get(), parse_mode="HTML")
        return

    # Check if we just crossed a subject boundary
    completed_part = _completed_part_at(new_idx, subject_parts)
    if completed_part:
        part_qs = questions[completed_part["start"]: completed_part["start"] + completed_part["count"]]
        cat_names = await _fetch_cat_names(part_qs, container)
        stats = aggregate_results(part_qs, data["answered"])
        text = build_part_result_text(completed_part["subject"], stats, cat_names)
        next_subject = questions[new_idx]["subject"]
        await reply_edit.answer(callback, text=text, reply_markup=part_result_kb.get(next_subject), parse_mode="HTML")
        return

    local_idx, local_total = get_local_progress(new_idx, subject_parts)
    text, keyboard = build_question_content(questions[new_idx], local_idx, local_total)
    await reply_edit.answer(callback, text=text, reply_markup=keyboard, parse_mode="HTML")


def _completed_part_at(new_idx: int, subject_parts: list[dict]) -> dict | None:
    """Return the part that just ended if new_idx is the first question of a new part."""
    for part in subject_parts[:-1]:  # last part boundary = end of test, handled above
        if new_idx == part["start"] + part["count"]:
            return part
    return None


async def _fetch_cat_names(questions: list[dict], container: Container) -> dict[str, str]:
    """Resolve category IDs present in questions to their names."""
    cat_ids = list({q["category_id"] for q in questions if q.get("category_id")})
    if not cat_ids:
        return {}
    cats = await container.categories.get_by_ids(cat_ids)
    return {c["id"]: c["name"] for c in cats}