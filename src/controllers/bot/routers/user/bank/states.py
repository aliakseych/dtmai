from aiogram.fsm.state import State, StatesGroup


class BankStates(StatesGroup):
    filtering = State()
    listing = State()
    viewing = State()