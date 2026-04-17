from src.controllers.bot.routers.user.test.callback import (
    ToggleSubject, SetCount, SetLevel, ToggleExcludeAnswered, StartTest,
)
from src.controllers.bot.routers.user.menu.callback import Menu
from src.models.questions.subject import SUBJECT_DISPLAY

from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup

COUNTS = [5, 10, 15, 20]
LEVELS = [
    ("MIXED", "Смешанный"),
    ("EASY", "Лёгкий"),
    ("MEDIUM", "Средний"),
    ("HARD", "Сложный"),
    ("ORIGINAL", "Официальные"),
]


def get(
    selected_subjects: list[str],
    count: int,
    level: str,
    exclude_answered: bool,
    available_subjects: list[str],  # subjects that have questions in DB
    locked_subjects: list[str] | None = None,  # pre-set by program, can't untoggle
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    locked_subjects = locked_subjects or []

    # Subject toggles
    for subj, display in SUBJECT_DISPLAY.items():
        if subj not in available_subjects:
            continue
        is_on = subj in selected_subjects
        is_locked = subj in locked_subjects
        label = f"{'✅' if is_on else '☐'} {display}{'🔒' if is_locked else ''}"
        builder.row(
            InlineKeyboardButton(
                text=label,
                callback_data=ToggleSubject(subject=subj).pack(),
            )
        )

    builder.row(InlineKeyboardButton(
            text="- - - - -",
            callback_data="none"))

    # Question count
    count_row = [
        InlineKeyboardButton(
            text=f"{'►' if c == count else ''}{c}",
            callback_data=SetCount(count=c).pack(),
        )
        for c in COUNTS
    ]
    builder.row(*count_row)

    # Level
    level_row = [
        InlineKeyboardButton(
            text=f"{'►' if lv == level else ''}{label}",
            callback_data=SetLevel(level=lv).pack(),
        )
        for lv, label in LEVELS
    ]
    builder.row(*level_row, width=2)


    builder.row(InlineKeyboardButton(
            text="- - - - -",
            callback_data="none"))

    # Exclude answered toggle
    excl_label = f"{'✅' if exclude_answered else '☐'} Только новые вопросы"
    builder.row(InlineKeyboardButton(
        text=excl_label,
        callback_data=ToggleExcludeAnswered().pack(),
    ))

    # Start / back
    builder.row(
        InlineKeyboardButton(text="← Назад", callback_data=Menu().pack()),
        InlineKeyboardButton(text="🚀 Начать", callback_data=StartTest().pack()),
    )

    return builder.as_markup()