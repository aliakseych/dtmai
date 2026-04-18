from src.controllers.bot.routers.user.bank.callback import BackToBankFilter, BankPage
from src.controllers.bot.routers.user.bank.router import router
from src.controllers.bot.routers.user.bank.states import BankStates
from src.controllers.bot.routers.user.bank.utils.filter import build_filter_content
from src.controllers.bot.routers.user.bank.utils.list import build_list_content
from src.controllers.bot.utilities import reply_edit

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery


@router.callback_query(BankStates.listing, BankPage.filter())
async def navigate_page(
    callback: CallbackQuery,
    callback_data: BankPage,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    await state.update_data(page=callback_data.page)
    text, keyboard = build_list_content(data["questions"], page=callback_data.page, subject=data["subject"])
    await reply_edit.answer(callback, text=text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(BankStates.listing, BackToBankFilter.filter())
async def back_to_filter(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(BankStates.filtering)
    text, keyboard = build_filter_content(
        data["subject"],
        data.get("level_filter"),
        data.get("solved_filter", "all"),
    )
    await reply_edit.answer(callback, text=text, reply_markup=keyboard, parse_mode="HTML")