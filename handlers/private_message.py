# =========================================================
# IMPORTS
# =========================================================

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config.settings import ADMIN_ID
from states.private_message import PrivateMessageState

router = Router()
# =========================================================
# PRIVATE MESSAGE
# =========================================================

@router.message(F.text == "📨 Shaxsiy Xabar")
async def private_message_start(
    message: Message,
    state: FSMContext,
):

    if message.from_user.id not in ADMIN_ID:
        return

    await state.set_state(
        PrivateMessageState.waiting_user_id
    )

    await message.answer(
        "👤 Foydalanuvchi Telegram ID sini yuboring."
    )
# =========================================================
# USER ID
# =========================================================

@router.message(
    PrivateMessageState.waiting_user_id
)
async def private_message_user(
    message: Message,
    state: FSMContext,
):

    if not message.text.isdigit():

        await message.answer(
            "❌ ID faqat raqamdan iborat bo'lishi kerak."
        )
        return

    await state.update_data(
        user_id=int(message.text)
    )

    await state.set_state(
        PrivateMessageState.waiting_message
    )

    await message.answer(
        "✍️ Yubormoqchi bo'lgan xabarni yuboring."
    )
# =========================================================
# SEND PRIVATE MESSAGE
# =========================================================

@router.message(
    PrivateMessageState.waiting_message
)
async def send_private_message(
    message: Message,
    state: FSMContext,
):

    data = await state.get_data()

    try:

        await message.copy_to(
            chat_id=data["user_id"]
        )

        await message.answer(
            "✅ Xabar yuborildi."
        )

    except Exception:

        await message.answer(
            "❌ Xabar yuborib bo'lmadi."
        )

    await state.clear()
