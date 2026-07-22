from aiogram.fsm.state import State, StatesGroup


class VizuCertificateState(StatesGroup):
    waiting_for_payment_check = State()
    waiting_for_ticket_photo = State()