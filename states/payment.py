from aiogram.fsm.state import State, StatesGroup


# =========================================================
# PAYMENT FSM
# =========================================================

class PaymentState(StatesGroup):

    # Kurs tanlash
    waiting_course = State()

    # Chek (rasm yoki PDF)
    waiting_receipt = State()

    # Ism-familiya
    waiting_full_name = State()

    # Telefon raqami
    waiting_phone = State()

    # Yakuniy tasdiqlash
    waiting_confirm = State()