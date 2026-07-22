from aiogram.fsm.state import State, StatesGroup


class ProfileState(StatesGroup):
    change_name = State()