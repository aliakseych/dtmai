from src.controllers.bot.container import Container
from src.controllers.bot.routers.user.bank.callback import ApplyBankFilter, ShowBankAll
from src.controllers.bot.routers.user.bank.router import router
from src.controllers.bot.routers.user.bank.states import BankStates
from src.controllers.bot.routers.user.bank.utils.list import build_list_content
from src.controllers.bot.utilities import reply_edit

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery


async def _load_questions(
    container: Container,
    user_tg_id: int,
    subject: str,
    level_filter: str | None,
    solved_filter: str,
) -> list[dict]:
    user = await container.users.get_by_telegram_id(user_tg_id)
    answered_ids: set[str] = set()
    if user:
        answered_ids = set(await container.attempts.get_answered_question_ids(user["id"]))

    docs = await container.questions.get_for_bank(subject, level=level_filter)

    if solved_filter == "solved":
        docs = [d for d in docs if d["id"] in answered_ids]
    elif solved_filter == "unsolved":
        docs = [d for d in docs if d["id"] not in answered_ids]

    for doc in docs:
        doc["solved"] = doc["id"] in answered_ids

    return docs


@router.callback_query(BankStates.filtering, ApplyBankFilter.filter())
async def apply_filter(
    callback: CallbackQuery,
    container: Container,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    questions = await _load_questions(
        container, callback.from_user.id,
        data["subject"], data.get("level_filter"), data.get("solved_filter", "all"),
    )
    await state.set_state(BankStates.listing)
    await state.update_data(questions=questions, page=0)
    text, keyboard = build_list_content(questions, page=0, subject=data["subject"])
    await reply_edit.answer(callback, text=text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(BankStates.filtering, ShowBankAll.filter())
async def show_all(
    callback: CallbackQuery,
    container: Container,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    questions = await _load_questions(
        container, callback.from_user.id,
        data["subject"], None, "all",
    )
    await state.set_state(BankStates.listing)
    await state.update_data(questions=questions, level_filter=None, solved_filter="all", page=0)
    text, keyboard = build_list_content(questions, page=0, subject=data["subject"])
    await reply_edit.answer(callback, text=text, reply_markup=keyboard, parse_mode="HTML")