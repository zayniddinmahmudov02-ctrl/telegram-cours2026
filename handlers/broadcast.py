# =========================================================
# IMPORTS
# =========================================================

from aiogram import Router, F
from aiogram.types import (
    Message,
)

from aiogram.fsm.context import FSMContext

from config.settings import ADMIN_ID

from states.broadcast import BroadcastState

from database.users import (
    get_all_users,
)

router = Router()
# =========================================================
# START BROADCAST
# =========================================================

@router.message(F.text == "📢 Reklama Yuborish")
async def start_broadcast(
    message: Message,
    state: FSMContext,
):

    if message.from_user.id not in ADMIN_ID:
        return

    await state.set_state(
        BroadcastState.waiting_message
    )

    await message.answer(
        """
📢 Reklama yuborish

Yubormoqchi bo'lgan xabaringizni yuboring.

Qo'llab-quvvatlanadi:

• Matn
• Rasm
• Video
• Hujjat
• Audio
"""
    )
# =========================================================
# SAVE BROADCAST
# =========================================================

@router.message(
    BroadcastState.waiting_message
)
async def save_broadcast(
    message: Message,
    state: FSMContext,
):

    await state.update_data(
        message_id=message.message_id,
        chat_id=message.chat.id,
    )

    await state.set_state(
        BroadcastState.waiting_confirm
    )

    await message.answer(
        """
✅ Reklama qabul qilindi.

Tasdiqlash uchun:

/send

Bekor qilish uchun:

/cancel
"""
    )
# =========================================================
# CANCEL
# =========================================================

@router.message(
    BroadcastState.waiting_confirm,
    F.text == "/cancel",
)
async def cancel_broadcast(
    message: Message,
    state: FSMContext,
):

    await state.clear()

    await message.answer(
        "❌ Reklama bekor qilindi."
    )
# =========================================================
# SEND BROADCAST
# =========================================================

@router.message(
    BroadcastState.waiting_confirm,
    F.text == "/send",
)
async def send_broadcast(
    message: Message,
    state: FSMContext,
):

    if message.from_user.id not in ADMIN_ID:
        return

    data = await state.get_data()

    users = get_all_users()

    success = 0
    failed = 0

    for user in users:

        try:

            await message.bot.copy_message(
                chat_id=user["user_id"],
                from_chat_id=data["chat_id"],
                message_id=data["message_id"],
            )

            success += 1

        except Exception:

            failed += 1

    await state.clear()

    await message.answer(
        f"""
✅ Reklama yuborildi.

👥 Yuborildi: {success}

❌ Xatolik: {failed}
"""
    )
