from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
)

import asyncio

from loader import (
    dp,
    bot,
    logger,
)

from config import (
    ADMIN_ID,
    ADMIN_CHANNEL_ID,
)

from database import db_execute

from keyboards import (
    admin_menu,
    main_menu,
)

from states.admin import (
    BroadcastState,
    AdminStates,
)

from services.logger import (
    send_admin_log,
    send_admin_photo_log,
)
# =========================================================
# ADMIN PANEL
# =========================================================

@dp.message(Command("admin"))
async def admin_panel(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "⚙️ Admin Panel",
        reply_markup=admin_menu,
    )
# =========================================================
# STATISTICS
# =========================================================

@dp.message(F.text == "📊 Statistika")
async def admin_statistics(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    total_users = db_execute(
        "SELECT COUNT(*) FROM users",
        fetchone=True,
    )[0]

    approved_users = db_execute(
        "SELECT COUNT(*) FROM users WHERE approved = 1",
        fetchone=True,
    )[0]

    pending_users = db_execute(
        "SELECT COUNT(*) FROM users WHERE approved = 0",
        fetchone=True,
    )[0]

    courses = db_execute(
        """
        SELECT
            course,
            COUNT(*)
        FROM users
        WHERE approved = 1
        GROUP BY course
        ORDER BY course
        """,
        fetchall=True,
    )

    course_text = ""

    if courses:

        for course, count in courses:

            course_text += (
                f"📚 {course}: {count}\n"
            )

    text = (

        "📊 <b>BOT STATISTIKASI</b>\n\n"

        f"👥 Foydalanuvchilar: <b>{total_users}</b>\n"

        f"💳 Xaridorlar: <b>{approved_users}</b>\n"

        f"⏳ Kutilmoqda: <b>{pending_users}</b>\n\n"

        "<b>Kurslar</b>\n"

        f"{course_text}"

    )

    await message.answer(
        text,
        parse_mode="HTML",
    )

# =========================================================
# USERS
# =========================================================

@dp.message(F.text == "👥 Foydalanuvchilar")
async def admin_users(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    total_users = db_execute(
        """
        SELECT COUNT(*)
        FROM users
        """,
        fetchone=True,
    )[0]

    latest_users = db_execute(
        """
        SELECT
            full_name,
            user_id
        FROM users
        ORDER BY id DESC
        LIMIT 10
        """,
        fetchall=True,
    )

    text = (
        "👥 <b>FOYDALANUVCHILAR</b>\n\n"
        f"📊 Jami: <b>{total_users}</b>\n\n"
    )

    if latest_users:

        text += "<b>🆕 Oxirgi foydalanuvchilar</b>\n\n"

        for index, user in enumerate(latest_users, start=1):

            full_name = user[0] or "Ism kiritilmagan"

            text += (
                f"{index}. {full_name}\n"
            )

    await message.answer(
        text,
        parse_mode="HTML",
    )
# =========================================================
# BUYERS
# =========================================================

@dp.message(F.text == "💳 Xaridorlar")
async def buyers(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    rows = db_execute(
        """
        SELECT
            course,
            COUNT(*)
        FROM users
        WHERE approved = 1
        GROUP BY course
        ORDER BY course
        """,
        fetchall=True,
    )

    total = db_execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE approved = 1
        """,
        fetchone=True,
    )[0]

    text = (
        "💳 <b>XARIDORLAR</b>\n\n"
    )

    if rows:

        for course, count in rows:

            text += (
                f"📚 {course}: <b>{count}</b>\n"
            )

    text += (
        f"\n👥 Jami: <b>{total}</b>"
    )

    await message.answer(
        text,
        parse_mode="HTML",
    )
# =========================================================
# PENDING PAYMENTS
# =========================================================

@dp.message(F.text == "⏳ To'lov Kutilmoqda")
async def pending_payments(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    rows = db_execute(
        """
        SELECT
            full_name,
            course
        FROM users
        WHERE approved = 0
        ORDER BY id DESC
        """,
        fetchall=True,
    )

    if not rows:

        await message.answer(
            "✅ Tasdiqlanmagan to'lovlar mavjud emas."
        )

        return

    text = (
        "⏳ <b>TASDIQLANMAGAN TO'LOVLAR</b>\n\n"
    )

    for i, row in enumerate(rows, start=1):

        full_name = row[0] or "Ism yo'q"
        course = row[1] or "-"

        text += (
            f"{i}. {full_name}\n"
            f"📚 {course}\n\n"
        )

    await message.answer(
        text,
        parse_mode="HTML",
    )
# =========================================================
# START BROADCAST
# =========================================================

@dp.message(F.text == "📢 Reklama Yuborish")
async def broadcast_start(
    message: Message,
    state: FSMContext,
):

    if message.from_user.id != ADMIN_ID:
        return

    await state.set_state(
        BroadcastState.waiting_for_message
    )

    await message.answer(
        "📢 <b>Broadcast rejimi yoqildi.</b>\n\n"
        "Yubormoqchi bo'lgan xabarni yuboring.\n\n"
        "✅ Matn\n"
        "✅ Rasm\n"
        "✅ Video\n"
        "✅ Audio\n"
        "✅ Forward\n\n"
        "Bekor qilish uchun:\n"
        "<b>❌ Bekor qilish</b>",
        parse_mode="HTML",
    )
# =========================================================
# CANCEL BROADCAST
# =========================================================

@dp.message(
    BroadcastState.waiting_for_message,
    F.text == "❌ Bekor qilish",
)
async def cancel_broadcast(
    message: Message,
    state: FSMContext,
):

    if message.from_user.id != ADMIN_ID:
        return

    await state.clear()

    await message.answer(
        "❌ Broadcast bekor qilindi.",
        reply_markup=admin_menu,
    )
# =========================================================
# PROCESS BROADCAST
# =========================================================

@dp.message(BroadcastState.waiting_for_message)
async def process_broadcast(
    message: Message,
    state: FSMContext,
):

    if message.from_user.id != ADMIN_ID:
        return

    users = db_execute(
        """
        SELECT user_id
        FROM users
        """,
        fetchall=True,
    )

    if not users:

        await message.answer(
            "❌ Foydalanuvchilar topilmadi."
        )

        await state.clear()

        return

    status = await message.answer(
        "📤 Reklama yuborilmoqda..."
    )

    success = 0
    failed = 0

    for (user_id,) in users:

        try:

            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
            )

            success += 1

        except Exception as e:

            logger.error(
                f"Broadcast {user_id}: {e}"
            )

            failed += 1

        await asyncio.sleep(0.05)

    await status.edit_text(

        "✅ <b>Broadcast yakunlandi</b>\n\n"

        f"👥 Jami: <b>{len(users)}</b>\n"

        f"✅ Yuborildi: <b>{success}</b>\n"

        f"❌ Xatolik: <b>{failed}</b>",

        parse_mode="HTML",
    )

    await state.clear()
# =========================================================
# PERSONAL MESSAGE START
# =========================================================

@dp.message(F.text == "📨 Shaxsiy Xabar")
async def personal_message_start(
    message: Message,
    state: FSMContext,
):

    if message.from_user.id != ADMIN_ID:
        return

    await state.set_state(
        AdminStates.personal_user_id
    )

    await message.answer(
        "🆔 Foydalanuvchi ID sini yuboring."
    )
# =========================================================
# PERSONAL USER ID
# =========================================================

@dp.message(AdminStates.personal_user_id)
async def personal_message_user(
    message: Message,
    state: FSMContext,
):

    if message.from_user.id != ADMIN_ID:
        return

    if not message.text.isdigit():

        await message.answer(
            "❌ Faqat raqam kiriting."
        )

        return

    await state.update_data(
        target_user=int(message.text)
    )

    await state.set_state(
        AdminStates.personal_text
    )

    await message.answer(
        "✉️ Endi yuboriladigan xabarni yuboring."
    )
# =========================================================
# PERSONAL MESSAGE SEND
# =========================================================

@dp.message(AdminStates.personal_text)
async def personal_message_send(
    message: Message,
    state: FSMContext,
):

    if message.from_user.id != ADMIN_ID:
        return

    data = await state.get_data()

    target_user = data.get("target_user")

    try:

        await bot.copy_message(
            chat_id=target_user,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )

        await message.answer(
            "✅ Xabar muvaffaqiyatli yuborildi.",
            reply_markup=admin_menu,
        )

        logger.info(
            f"Admin personal message -> {target_user}"
        )

    except Exception as e:

        logger.exception(e)

        await message.answer(
            "❌ Xabar yuborilmadi."
        )

    await state.clear()
# =========================================================
# ADMIN EXIT
# =========================================================

@dp.message(F.text == "⬅️ Admin Chiqish")
async def admin_exit(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "🏠 Asosiy menyuga qaytildi.",
        reply_markup=main_menu,
    )
