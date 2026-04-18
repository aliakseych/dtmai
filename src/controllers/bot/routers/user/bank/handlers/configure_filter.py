from src.controllers.bot.routers.user.bank.callback import ToggleBankLevel, ToggleBankSolved
from src.controllers.bot.routers.user.bank.router import router
from src.controllers.bot.routers.user.bank.states import BankStates
from src.controllers.bot.routers.user.bank.utils.filter import build_filter_content
from src.controllers.bot.utilities import reply_edit

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery


@router.callback_query(BankStates.filtering, ToggleBankLevel.filter())
async def toggle_level(
    callback: CallbackQuery,
    callback_data: ToggleBankLevel,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    current = data.get("level_filter")
    # clicking the active level deselects it
    new_level = None if current == callback_data.level else callback_data.level
    await state.update_data(level_filter=new_level)
    text, keyboard = build_filter_content(data["subject"], new_level, data["solved_filter"])
    await reply_edit.answer(callback, text=text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(BankStates.filtering, ToggleBankSolved.filter())
async def toggle_solved(
    callback: CallbackQuery,
    callback_data: ToggleBankSolved,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    new_solved = callback_data.value
    new_level = None if new_solved == "all" else data.get("level_filter")
    await state.update_data(solved_filter=new_solved, level_filter=new_level)
    text, keyboard = build_filter_content(data["subject"], new_level, new_solved)
    await reply_edit.answer(callback, text=text, reply_markup=keyboard, parse_mode="HTML")