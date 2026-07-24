# =========================================================
# BROADCAST STATES
# =========================================================

from aiogram.fsm.state import (
    State,
    StatesGroup,
)


class BroadcastState(StatesGroup):

    waiting_message = State()

    waiting_confirm = State()