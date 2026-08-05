# =========================================================
# IMPORTS
# =========================================================

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from services.auth import is_admin
from database.users import get_user
from keyboards.admin import admin_menu
from states.private_message import PrivateMessageState

router = Router()
# =========================================================
# START (from the Users submenu)
# =========================================================

@router.message(F.text == "✉️ Xabar Yuborish")
async def private_message_start(
    message: Message,
    state: FSMContext,
):

    if not is_admin(message.from_user.id):
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

    if not is_admin(message.from_user.id):
        return

    text = (message.text or "").strip()

    if not text.isdigit():
        await message.answer("❌ User not found.")
        return

    user_id = int(text)

    if not await get_user(user_id):
        await message.answer("❌ User not found.")
        return

    await state.update_data(
        user_id=user_id
    )

    await state.set_state(
        PrivateMessageState.waiting_message
    )

    await message.answer(
        "✍️ Yubormoqchi bo'lgan xabarni yuboring.\n\n"
        "Matn, rasm, video yoki hujjat yuborishingiz mumkin."
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

    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()

    try:

        await message.copy_to(
            chat_id=data["user_id"]
        )

        await message.answer(
            "✅ Message sent successfully.",
            reply_markup=admin_menu,
        )

    except Exception as e:

        await message.answer(
            f"❌ {e}",
            reply_markup=admin_menu,
        )

    await state.clear()
