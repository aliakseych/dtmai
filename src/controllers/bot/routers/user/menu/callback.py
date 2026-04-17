from aiogram.filters.callback_data import CallbackData


class Menu(CallbackData, prefix="menu"):
    """Return to main menu."""
    pass


class ProgramsList(CallbackData, prefix="menu_programs"):
    """Open programs list screen."""
    pass


class SelectProgram(CallbackData, prefix="menu_prog_select"):
    """User picked a program — open the test selector with its subjects pre-loaded."""
    program_id: str