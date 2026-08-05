# =========================================================
# IMPORTS
# =========================================================

from aiogram import Router, F
from aiogram.types import (
    Message,
)

from aiogram.fsm.context import FSMContext

from services.auth import is_admin
from services.broadcast import format_elapsed, run_broadcast

from states.broadcast import BroadcastState

router = Router()
# =========================================================
# START BROADCAST
# =========================================================

@router.message(F.text == "📢 Reklama Yuborish")
async def start_broadcast(
    message: Message,
    state: FSMContext,
):

    if not is_admin(message.from_user.id):
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

    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()

    await state.clear()

    status_message = await message.answer(
        "⏳ Yuborilmoqda...\n\n0 / 0"
    )

    async def report_progress(sent: int, total: int):
        try:
            await status_message.edit_text(
                f"⏳ Yuborilmoqda...\n\n{sent} / {total}"
            )
        except Exception:
            pass

    stats = await run_broadcast(
        bot=message.bot,
        from_chat_id=data["chat_id"],
        message_id=data["message_id"],
        progress_callback=report_progress,
    )

    await status_message.edit_text(
        f"""
✅ Reklama yakunlandi.

👥 Jami: {stats['total']}
✅ Yuborildi: {stats['success']}
🚫 Bloklangan: {stats['blocked']}
🗑 O'chirilgan: {stats['deleted']}
❌ Xatolik: {stats['failed']}
⏱ Vaqt: {format_elapsed(stats['elapsed_seconds'])}
"""
    )
