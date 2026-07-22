from aiogram.fsm.state import State, StatesGroup


class SprechenState(StatesGroup):
    waiting_voice = State()


class VizuSprechenState(StatesGroup):
    teil1 = State()
    teil21 = State()
    teil22 = State()
    teil31 = State()
    teil32 = State()