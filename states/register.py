from aiogram.fsm.state import State, StatesGroup


class RegisterStates(StatesGroup):
    waiting_full_name = State()