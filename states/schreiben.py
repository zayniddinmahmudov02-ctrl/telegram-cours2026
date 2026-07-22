from aiogram.fsm.state import State, StatesGroup


class SchreibenState(StatesGroup):
    waiting_file = State()


class SchreibenRateState(StatesGroup):
    waiting_score = State()


class VizuSchreibenState(StatesGroup):
    teil1 = State()
    teil2 = State()