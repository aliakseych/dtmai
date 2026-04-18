from src.controllers.bot.routers.user.bank.callback import BackToBankFilter, BankPage, ViewBankQuestion

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

PAGE_SIZE = 10


def get(questions_page: list[dict], total: int, page: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    start = page * PAGE_SIZE

    q_buttons = [
        InlineKeyboardButton(
            text=f"#{start + i + 1}",
            callback_data=ViewBankQuestion(question_id=q["id"]).pack(),
        )
        for i, q in enumerate(questions_page)
    ]
    # 5 per row
    for i in range(0, len(q_buttons), 5):
        builder.row(*q_buttons[i:i + 5])

    # Pagination
    if total_pages > 1:
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton(
                text="← Пред.", callback_data=BankPage(page=page - 1).pack(),
            ))
        nav.append(InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}", callback_data=BankPage(page=page).pack(),
        ))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton(
                text="След. →", callback_data=BankPage(page=page + 1).pack(),
            ))
        builder.row(*nav)

    builder.row(InlineKeyboardButton(
        text="← К фильтрам", callback_data=BackToBankFilter().pack(),
    ))
    return builder.as_markup()