from aiogram.fsm.state import (
    State,
    StatesGroup,
)

# =========================================================
# PAYMENT FSM
# =========================================================

class PaymentState(StatesGroup):

    # To'lov cheki
    waiting_receipt = State()

    # Ism va familiya
    waiting_full_name = State()

    # Telefon raqami
    waiting_phone = State()