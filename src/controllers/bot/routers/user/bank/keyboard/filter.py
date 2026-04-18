from src.controllers.bot.routers.user.bank.callback import (
    ApplyBankFilter, OpenBank, ShowBankAll, ToggleBankLevel, ToggleBankSolved,
)

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

_LEVELS = [
    ("ORIGINAL", "⭐ Оригинальный"),
    ("HARD",     "🔴 Сложный"),
    ("MEDIUM",   "🟡 Средний"),
    ("EASY",     "🟢 Лёгкий"),
]

_SOLVED = [
    ("all",       "Все"),
    ("solved",    "Решённые"),
    ("unsolved",  "Нерешённые"),
]

_SEP = InlineKeyboardButton(text="- - - - -", callback_data="none")


def get(subject: str, level_filter: str | None, solved_filter: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Quick action at top
    builder.row(InlineKeyboardButton(text="Показать всё", callback_data=ShowBankAll().pack()))

    builder.row(_SEP)

    # Level row — single-select toggle
    level_buttons = [
        InlineKeyboardButton(
            text=f"{label}{' ✓' if level_filter == value else ''}",
            callback_data=ToggleBankLevel(level=value).pack(),
        )
        for value, label in _LEVELS
    ]
    builder.row(*level_buttons, width=1)

    builder.row(_SEP)

    # Solved row
    solved_buttons = [
        InlineKeyboardButton(
            text=f"{label}{' ✓' if solved_filter == value else ''}",
            callback_data=ToggleBankSolved(value=value).pack(),
        )
        for value, label in _SOLVED
    ]
    builder.row(*solved_buttons, width=1)

    builder.row(_SEP)

    builder.row(
        InlineKeyboardButton(text="🔍 Поиск", callback_data=ApplyBankFilter().pack()))
    builder.row(InlineKeyboardButton(text="← Назад", callback_data=OpenBank().pack()))

    return builder.as_markup()