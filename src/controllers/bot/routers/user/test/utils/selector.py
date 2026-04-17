from src.controllers.bot.container import Container
from src.controllers.bot.routers.user.test.states import TestStates
from src.controllers.bot.routers.user.test.keyboard import selector as selector_kb
from src.models.questions.subject import SUBJECT_DISPLAY

from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup

_DEFAULT_COUNT = 10
_DEFAULT_LEVEL = "MIXED"

_LEVEL_DISPLAY = {
    "MIXED": "Смешанный (Случайно)", "EASY": "Лёгкий", "MEDIUM": "Средний",
    "HARD": "Сложный", "ORIGINAL": "Задания прошлых лет",
}


async def get_available_subjects(container: Container) -> list[str]:
    return [
        s for s in SUBJECT_DISPLAY
        if await container.questions.count_available(s) > 0
    ]


async def init_selector_state(
    state: FSMContext,
    container: Container,
    preset_subjects: list[str] | None = None,
    program_id: str | None = None,
) -> list[str]:
    """Set up FSM state with default config. Returns available subjects."""
    available = await get_available_subjects(container)
    selected = preset_subjects or ([available[0]] if available else [])
    await state.set_state(TestStates.configuring)
    await state.update_data(
        selected_subjects=selected,
        count=_DEFAULT_COUNT,
        level=_DEFAULT_LEVEL,
        exclude_answered=False,
        program_id=program_id,
        locked_subjects=preset_subjects or [],
    )
    return available


async def build_selector_content(
    state: FSMContext,
    container: Container,
    tg_user_id: int,
    available: list[str] | None = None,
) -> tuple[str, InlineKeyboardMarkup]:
    """Build selector screen text and keyboard from current FSM state."""
    data = await state.get_data()
    selected = data["selected_subjects"]
    count = data["count"]
    level = data["level"]
    exclude = data["exclude_answered"]
    locked = data.get("locked_subjects", [])

    if available is None:
        available = await get_available_subjects(container)

    warnings = []
    if exclude:
        user = await container.users.get_by_telegram_id(tg_user_id)
        answered_ids = await container.attempts.get_answered_question_ids(user["id"])
        for subj in selected:
            avail = await container.questions.count_available(subj, exclude_ids=answered_ids)
            if avail < count:
                display = SUBJECT_DISPLAY.get(subj, subj)
                warnings.append(f"⚠️ {display}: доступно только {avail} новых вопросов")

    text = (
        "🧩 <b>Создать тест</b>\n\n"
        f"Вопросов на предмет: <b>{count}</b>\n"
        f"Уровень: <b>{_LEVEL_DISPLAY.get(level, level)}</b>\n"
        + ("\n".join(warnings) + "\n" if warnings else "")
        + "\nВыбери предметы и параметры:"
    )
    keyboard = selector_kb.get(
        selected_subjects=selected,
        count=count,
        level=level,
        exclude_answered=exclude,
        available_subjects=available,
        locked_subjects=locked,
    )
    return text, keyboard