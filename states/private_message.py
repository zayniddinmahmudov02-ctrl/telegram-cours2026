# =========================================================
# PRIVATE MESSAGE STATES
# =========================================================

from aiogram.fsm.state import (
    State,
    StatesGroup,
)


class PrivateMessageState(StatesGroup):

    waiting_user_id = State()

    waiting_message = State()