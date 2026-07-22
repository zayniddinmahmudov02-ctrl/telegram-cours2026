from aiogram.fsm.state import State, StatesGroup


class BroadcastState(StatesGroup):
    waiting_for_message = State()


class PersonalMessageState(StatesGroup):
    waiting_for_id = State()
    waiting_for_text = State()