from src.controllers.bot.container import Container
from src.controllers.bot.routers.user.menu.callback import ProgramsList, SelectProgram
from src.controllers.bot.routers.user.menu.router import router
from src.controllers.bot.routers.user.menu.keyboard import programs as programs_kb
from src.controllers.bot.routers.user.test.utils.selector import init_selector_state, build_selector_content
from src.controllers.bot.utilities import reply_edit
from src.models.questions.subject import SUBJECT_DISPLAY

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery


@router.callback_query(ProgramsList.filter())
async def programs_list(callback: CallbackQuery, container: Container) -> None:
    programs = await container.programs.get_all()

    if not programs:
        await reply_edit.answer(
            callback,
            text="📋 Программы пока не добавлены. Загляни позже!",
            reply_markup=programs_kb.get([]),
        )
        return

    lines = ["📋 <b>Программы</b>\n\nВыбери направление подготовки:\n"]
    for prog in programs:
        subjects_str = " + ".join(SUBJECT_DISPLAY.get(s, s) for s in prog["subjects"])
        lines.append(f"• <b>{prog['name']}</b>: {subjects_str}")

    await reply_edit.answer(
        callback,
        text="\n".join(lines),
        reply_markup=programs_kb.get(programs),
        parse_mode="HTML",
    )


@router.callback_query(SelectProgram.filter())
async def select_program(
    callback: CallbackQuery,
    callback_data: SelectProgram,
    container: Container,
    state: FSMContext,
) -> None:
    program = await container.programs.get_by_id(callback_data.program_id)

    if not program:
        await callback.answer("Программа не найдена.", show_alert=True)
        return

    available = await init_selector_state(
        state, container,
        preset_subjects=program["subjects"],
        program_id=program["id"],
    )
    text, keyboard = await build_selector_content(state, container, callback.from_user.id, available)
    await reply_edit.answer(callback, text=text, reply_markup=keyboard, parse_mode="HTML")