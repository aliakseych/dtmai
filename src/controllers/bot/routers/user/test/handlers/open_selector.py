from src.controllers.bot.container import Container
from src.controllers.bot.routers.user.test.callback import OpenSelector
from src.controllers.bot.routers.user.test.router import router
from src.controllers.bot.routers.user.test.utils.selector import init_selector_state, build_selector_content
from src.controllers.bot.utilities import reply_edit

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery


@router.callback_query(OpenSelector.filter())
async def open_selector(
    callback: CallbackQuery, container: Container, state: FSMContext,
) -> None:
    available = await init_selector_state(state, container)
    text, keyboard = await build_selector_content(state, container, callback.from_user.id, available)
    await reply_edit.answer(callback, text=text, reply_markup=keyboard, parse_mode="HTML")