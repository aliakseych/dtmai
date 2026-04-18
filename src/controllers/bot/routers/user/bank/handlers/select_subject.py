from src.controllers.bot.routers.user.bank.callback import SelectBankSubject
from src.controllers.bot.routers.user.bank.router import router
from src.controllers.bot.routers.user.bank.states import BankStates
from src.controllers.bot.routers.user.bank.utils.filter import build_filter_content
from src.controllers.bot.utilities import reply_edit

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery


@router.callback_query(SelectBankSubject.filter())
async def select_subject(
    callback: CallbackQuery,
    callback_data: SelectBankSubject,
    state: FSMContext,
) -> None:
    await state.set_state(BankStates.filtering)
    await state.set_data({
        "subject": callback_data.subject,
        "level_filter": None,
        "solved_filter": "all",
    })
    text, keyboard = build_filter_content(callback_data.subject, level_filter=None, solved_filter="all")
    await reply_edit.answer(callback, text=text, reply_markup=keyboard, parse_mode="HTML")