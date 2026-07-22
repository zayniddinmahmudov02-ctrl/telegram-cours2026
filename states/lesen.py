from aiogram.fsm.state import State, StatesGroup


class VizuLesenState(StatesGroup):
    solving = State()