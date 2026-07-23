from aiogram.fsm.state import (
    State,
    StatesGroup,
)

# =========================================================
# ADMIN STATES
# =========================================================

class AdminStates(StatesGroup):
    broadcast = State()

    personal_user_id = State()
    personal_text = State()