from src.controllers.bot.routers.user.bank.callback import (
    BackToBankList, BankNextQuestion, BankPrevQuestion, ShowBankAnswer,
)
from src.controllers.bot.routers.user.menu.callback import Menu
from src.controllers.bot.routers.user.test.callback import AnswerQuestion, ShowExplanation
from src.controllers.bot.routers.user.test.keyboard.question import LETTERS

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def _nav_buttons(viewing_idx: int, total: int) -> list[InlineKeyboardButton]:
    prev = InlineKeyboardButton(
        text="← Назад",
        callback_data=BankPrevQuestion().pack() if viewing_idx > 0 else "none",
    )
    nxt = InlineKeyboardButton(
        text="Вперёд →",
        callback_data=BankNextQuestion().pack() if viewing_idx < total - 1 else "none",
    )
    show = InlineKeyboardButton(text="👁 Ответ", callback_data=ShowBankAnswer().pack())
    return [prev, show, nxt]


def get_unanswered(
    answers: list[str],
    viewing_idx: int,
    total: int,
    page: int,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for i, answer in enumerate(answers):
        builder.row(InlineKeyboardButton(
            text=f"{LETTERS[i]}) {answer}",
            callback_data=AnswerQuestion(index=i).pack(),
        ))
    builder.adjust(2)

    builder.row(*_nav_buttons(viewing_idx, total))
    builder.row(InlineKeyboardButton(text="← Меню", callback_data=Menu().pack()))
    return builder.as_markup()


def get_after_answer(
    viewing_idx: int,
    total: int,
    has_steps: bool,
    page: int,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if has_steps:
        builder.row(InlineKeyboardButton(
            text="🔍 Объяснение", callback_data=ShowExplanation().pack(),
        ))

    prev_cb = BankPrevQuestion().pack() if viewing_idx > 0 else "none"
    nxt_cb = BankNextQuestion().pack() if viewing_idx < total - 1 else "none"
    builder.row(
        InlineKeyboardButton(text="← Пред.", callback_data=prev_cb),
        InlineKeyboardButton(text="Вперёд →", callback_data=nxt_cb),
    )
    builder.row(
        InlineKeyboardButton(text="← К списку", callback_data=BackToBankList(page=page).pack()),
        InlineKeyboardButton(text="← Меню", callback_data=Menu().pack()),
    )
    return builder.as_markup()