from src.controllers.bot.routers.user.test.callback import (
    AnswerQuestion, ShowExplanation, NextQuestion,
)

from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup

LETTERS = ["A", "B", "C", "D", "E"]


def get_answers(answers: list[str]) -> InlineKeyboardMarkup:
    """Answer option buttons — labelled A/B/C/D."""
    builder = InlineKeyboardBuilder()
    for i, answer in enumerate(answers):
        builder.row(
            InlineKeyboardButton(
                text=f"{LETTERS[i]}) {answer}",
                callback_data=AnswerQuestion(index=i).pack(),
            )
        )
    builder.adjust(2)
    return builder.as_markup()


def get_after_answer(has_steps: bool, is_last: bool) -> InlineKeyboardMarkup:
    """Buttons shown after the user answers: optionally explanation, then next/finish."""
    builder = InlineKeyboardBuilder()
    if has_steps:
        builder.row(InlineKeyboardButton(
            text="🔍 Объяснение",
            callback_data=ShowExplanation().pack(),
        ))
    next_label = "📊 Результат" if is_last else "Следующий →"
    builder.row(InlineKeyboardButton(
        text=next_label,
        callback_data=NextQuestion().pack(),
    ))
    return builder.as_markup()