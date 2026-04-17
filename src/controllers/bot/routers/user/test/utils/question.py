from src.controllers.bot.routers.user.test.keyboard import question as question_kb
from src.controllers.bot.utilities.latex import render_for_telegram
from src.models.questions.subject import SUBJECT_DISPLAY

from aiogram.types import InlineKeyboardMarkup


def get_local_progress(idx: int, subject_parts: list[dict]) -> tuple[int, int]:
    """
    Returns (local_0based_idx, part_total) for the question at absolute index idx.
    Used to display '3/20' instead of '23/40' when test has multiple subject parts.
    """
    for part in subject_parts:
        end = part["start"] + part["count"]
        if idx < end:
            return idx - part["start"], part["count"]
    return idx, 1  # fallback


def build_question_content(
    q: dict,
    local_idx: int,
    local_total: int,
    notice: str = "",
) -> tuple[str, InlineKeyboardMarkup]:
    """Build question screen text and answer keyboard."""
    subject_label = SUBJECT_DISPLAY.get(q.get("subject", ""), "")
    question_text = render_for_telegram(q["question"])
    answers = [render_for_telegram(a) for a in q["answers"]]

    image_line = f'\n<a href="{q["image_url"]}">🖼 Изображение</a>' if q.get("image_url") else ""

    text = (
        f"{notice}"
        f"<b>{subject_label}</b> ({local_idx + 1}/{local_total})\n"
        f"\n"
        f"{question_text}"
        f"{image_line}"
    )
    return text, question_kb.get_answers(answers)


def build_verdict_content(
    q: dict,
    local_idx: int,
    local_total: int,
    is_correct: bool,
    is_last: bool,
) -> tuple[str, InlineKeyboardMarkup]:
    """Build post-answer text (question + verdict) and keyboard."""
    verdict = "✅ Правильно!" if is_correct else f"❌ Неверно. Правильный ответ: <b>{render_for_telegram(q['correct_answer'])}</b>"
    subject_label = SUBJECT_DISPLAY.get(q.get("subject", ""), "")
    question_text = render_for_telegram(q["question"])
    image_line = f'\n<a href="{q["image_url"]}">🖼 Изображение</a>' if q.get("image_url") else ""

    text = (
        f"<b>{subject_label}</b> ({local_idx + 1}/{local_total})\n"
        f"\n"
        f"{question_text}"
        f"{image_line}\n\n"
        f"{verdict}"
    )
    keyboard = question_kb.get_after_answer(
        has_steps=bool(q.get("solution_steps")),
        is_last=is_last,
    )
    return text, keyboard