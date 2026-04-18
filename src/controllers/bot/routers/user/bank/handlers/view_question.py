from datetime import datetime, timezone

from src.controllers.bot.container import Container
from src.controllers.bot.routers.user.bank.callback import (
    BackToBankList, BankNextQuestion, BankPrevQuestion, ShowBankAnswer, ViewBankQuestion,
)
from src.controllers.bot.routers.user.bank.keyboard import question_view as qv_kb
from src.controllers.bot.routers.user.bank.router import router
from src.controllers.bot.routers.user.bank.states import BankStates
from src.controllers.bot.routers.user.bank.utils.list import build_list_content
from src.controllers.bot.routers.user.test.callback import AnswerQuestion, ShowExplanation
from src.controllers.bot.routers.user.test.utils.question import build_question_content, build_verdict_content
from src.controllers.bot.utilities import reply_edit
from src.controllers.bot.utilities.latex import render_for_telegram
from src.models.questions.subject import SUBJECT_DISPLAY

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

import uuid6


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _show_question(callback: CallbackQuery, doc: dict, viewing_idx: int, state: FSMContext) -> None:
    data = await state.get_data()
    total = len(data["questions"])
    page = data.get("page", 0)
    answers = [render_for_telegram(a) for a in doc["answers"]]
    keyboard = qv_kb.get_unanswered(answers, viewing_idx, total, page)
    text, _ = build_question_content(doc, 0, 1, show_progress=False, keyboard=keyboard)
    await reply_edit.answer(callback, text=text, reply_markup=keyboard, parse_mode="HTML")


# ── Open question ──────────────────────────────────────────────────────────────

@router.callback_query(BankStates.listing, ViewBankQuestion.filter())
async def view_question(
    callback: CallbackQuery,
    callback_data: ViewBankQuestion,
    container: Container,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    questions = data["questions"]
    viewing_idx = next((i for i, q in enumerate(questions) if q["id"] == callback_data.question_id), 0)

    doc = await container.questions.get_by_id(callback_data.question_id)
    if not doc:
        await callback.answer("Вопрос не найден.", show_alert=True)
        return

    await state.set_state(BankStates.viewing)
    await state.update_data(viewing_question=doc, viewing_idx=viewing_idx)
    await _show_question(callback, doc, viewing_idx, state)


# ── Navigate prev / next ───────────────────────────────────────────────────────

@router.callback_query(BankStates.viewing, BankPrevQuestion.filter())
@router.callback_query(BankStates.viewing, BankNextQuestion.filter())
async def navigate_question(
    callback: CallbackQuery,
    container: Container,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    questions = data["questions"]
    viewing_idx = data.get("viewing_idx", 0)

    is_next = callback.data and callback.data.startswith("bank_next")
    new_idx = viewing_idx + (1 if is_next else -1)
    new_idx = max(0, min(new_idx, len(questions) - 1))

    doc = await container.questions.get_by_id(questions[new_idx]["id"])
    if not doc:
        await callback.answer("Вопрос не найден.", show_alert=True)
        return

    await state.update_data(viewing_question=doc, viewing_idx=new_idx)
    await _show_question(callback, doc, new_idx, state)


# ── Answer ─────────────────────────────────────────────────────────────────────

@router.callback_query(BankStates.viewing, AnswerQuestion.filter())
async def answer_question(
    callback: CallbackQuery,
    callback_data: AnswerQuestion,
    container: Container,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    q = data.get("viewing_question")
    viewing_idx = data.get("viewing_idx", 0)
    page = data.get("page", 0)

    if not q:
        await callback.answer()
        return

    selected = q["answers"][callback_data.index]
    is_correct = selected == q["correct_answer"]

    user = await container.users.get_by_telegram_id(callback.from_user.id)
    await container.attempts.create({
        "_id": str(uuid6.uuid7()),
        "user_id": user["id"],
        "question_id": q["id"],
        "subject": q.get("subject", ""),
        "set_id": None,
        "selected_answer": selected,
        "is_correct": is_correct,
        "answered_at": datetime.now(timezone.utc),
        "time_taken_ms": None,
    })

    # Mark question as solved in the in-memory list so the list reflects it immediately
    questions = data["questions"]
    questions = [
        {**item, "solved": True} if item["id"] == q["id"] else item
        for item in questions
    ]
    await state.update_data(last_answer_correct=is_correct, questions=questions)

    total = len(questions)
    keyboard = qv_kb.get_after_answer(
        viewing_idx=viewing_idx,
        total=total,
        has_steps=bool(q.get("solution_steps")),
        page=page,
    )
    text, _ = build_verdict_content(q, 0, 1, is_correct, is_last=True, show_progress=False)
    await reply_edit.answer(callback, text=text, reply_markup=keyboard, parse_mode="HTML")


# ── Show answer (no attempt saved) ────────────────────────────────────────────

@router.callback_query(BankStates.viewing, ShowBankAnswer.filter())
async def show_answer(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    q = data.get("viewing_question")
    viewing_idx = data.get("viewing_idx", 0)
    page = data.get("page", 0)

    if not q:
        await callback.answer()
        return

    total = len(data["questions"])
    correct = render_for_telegram(q["correct_answer"])
    subject_label = SUBJECT_DISPLAY.get(q.get("subject", ""), "")
    question_text = render_for_telegram(q["question"])
    image_line = f'\n<a href="{q["image_url"]}">🖼 Изображение</a>' if q.get("image_url") else ""

    text = (
        f"<b>{subject_label}</b>\n\n"
        f"{question_text}"
        f"{image_line}\n\n"
        f"👁 Правильный ответ: <b>{correct}</b>"
    )
    keyboard = qv_kb.get_after_answer(
        viewing_idx=viewing_idx,
        total=total,
        has_steps=bool(q.get("solution_steps")),
        page=page,
    )
    await reply_edit.answer(callback, text=text, reply_markup=keyboard, parse_mode="HTML")


# ── Explanation ────────────────────────────────────────────────────────────────

@router.callback_query(BankStates.viewing, ShowExplanation.filter())
async def show_explanation(
    callback: CallbackQuery,
    container: Container,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    q = data.get("viewing_question")
    viewing_idx = data.get("viewing_idx", 0)
    page = data.get("page", 0)

    if not q:
        await callback.answer()
        return

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

    is_correct = data.get("last_answer_correct", False)
    verdict = "✅ Правильно!" if is_correct else f"❌ Правильный ответ: <b>{render_for_telegram(q['correct_answer'])}</b>"
    lines.append(verdict)

    total = len(data["questions"])
    keyboard = qv_kb.get_after_answer(
        viewing_idx=viewing_idx,
        total=total,
        has_steps=False,  # already on explanation screen
        page=page,
    )
    await reply_edit.answer(
        callback, text="\n".join(lines),
        reply_markup=keyboard, parse_mode="HTML",
    )


# ── Back to list ───────────────────────────────────────────────────────────────

@router.callback_query(BankStates.viewing, BackToBankList.filter())
async def back_to_list(
    callback: CallbackQuery,
    callback_data: BackToBankList,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    await state.set_state(BankStates.listing)
    await state.update_data(page=callback_data.page)
    text, keyboard = build_list_content(data["questions"], page=callback_data.page, subject=data["subject"])
    await reply_edit.answer(callback, text=text, reply_markup=keyboard, parse_mode="HTML")