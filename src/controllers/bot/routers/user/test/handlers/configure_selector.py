from src.controllers.bot.container import Container
from src.controllers.bot.routers.user.test.callback import (
    ToggleSubject, SetCount, SetLevel, ToggleExcludeAnswered,
)
from src.controllers.bot.routers.user.test.router import router
from src.controllers.bot.routers.user.test.states import TestStates
from src.controllers.bot.routers.user.test.utils.selector import build_selector_content
from src.controllers.bot.utilities import reply_edit

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery


@router.callback_query(TestStates.configuring, ToggleSubject.filter())
async def toggle_subject(
    callback: CallbackQuery,
    callback_data: ToggleSubject,
    container: Container,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    locked = data.get("locked_subjects", [])

    if callback_data.subject in locked:
        await callback.answer("Этот предмет задан программой.", show_alert=False)
        return

    selected = data["selected_subjects"]
    if callback_data.subject in selected:
        selected = [s for s in selected if s != callback_data.subject]
    else:
        selected = selected + [callback_data.subject]

    await state.update_data(selected_subjects=selected)
    text, keyboard = await build_selector_content(state, container, callback.from_user.id)
    await reply_edit.answer(callback, text=text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(TestStates.configuring, SetCount.filter())
async def set_count(
    callback: CallbackQuery,
    callback_data: SetCount,
    container: Container,
    state: FSMContext,
) -> None:
    await state.update_data(count=callback_data.count)
    text, keyboard = await build_selector_content(state, container, callback.from_user.id)
    await reply_edit.answer(callback, text=text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(TestStates.configuring, SetLevel.filter())
async def set_level(
    callback: CallbackQuery,
    callback_data: SetLevel,
    container: Container,
    state: FSMContext,
) -> None:
    await state.update_data(level=callback_data.level)
    text, keyboard = await build_selector_content(state, container, callback.from_user.id)
    await reply_edit.answer(callback, text=text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(TestStates.configuring, ToggleExcludeAnswered.filter())
async def toggle_exclude(
    callback: CallbackQuery, container: Container, state: FSMContext,
) -> None:
    data = await state.get_data()
    await state.update_data(exclude_answered=not data["exclude_answered"])
    text, keyboard = await build_selector_content(state, container, callback.from_user.id)
    await reply_edit.answer(callback, text=text, reply_markup=keyboard, parse_mode="HTML")