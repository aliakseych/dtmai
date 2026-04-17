from aiogram.filters.callback_data import CallbackData


class OpenSelector(CallbackData, prefix="test_open"):
    """Open test configurator (from menu or programs)."""
    pass


class ToggleSubject(CallbackData, prefix="test_subj"):
    subject: str


class SetCount(CallbackData, prefix="test_cnt"):
    count: int


class SetLevel(CallbackData, prefix="test_lvl"):
    level: str  # Level.value or "MIXED"


class ToggleExcludeAnswered(CallbackData, prefix="test_excl"):
    pass


class StartTest(CallbackData, prefix="test_start"):
    pass


class AnswerQuestion(CallbackData, prefix="test_ans"):
    index: int  # index into the current question's answers list


class ShowExplanation(CallbackData, prefix="test_expl"):
    pass


class NextQuestion(CallbackData, prefix="test_next"):
    pass


class NextPart(CallbackData, prefix="test_next_part"):
    """Continue to the next subject part after seeing intermediate results."""
    pass