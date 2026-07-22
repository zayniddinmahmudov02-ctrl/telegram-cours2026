from aiogram.fsm.state import State, StatesGroup


class VizuHorenState(StatesGroup):
    solving = State()