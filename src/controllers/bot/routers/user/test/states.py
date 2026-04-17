from aiogram.fsm.state import StatesGroup, State


class TestStates(StatesGroup):
    configuring = State()   # user is on the selector screen
    in_progress = State()   # user is answering questions