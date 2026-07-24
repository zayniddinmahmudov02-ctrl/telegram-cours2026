# =========================================================
# IMPORTS
# =========================================================

from aiogram import Router, F
from aiogram.types import Message

from config.settings import ADMIN_IDS

from keyboards.admin import admin_menu
from keyboards.menu import main_menu
from database.payments import (
    get_approved_payments,
)

from database.users import (
    get_total_users,
    get_approved_users,
    get_blocked_users,
)

from database.payments import (
    get_payment_statistics,
)

router = Router()
# =========================================================
# ADMIN PANEL
# =========================================================

@router.message(F.text == "/admin")
async def admin_panel(message: Message):

    if message.from_user.id not in ADMIN_IDS:
        return

    await message.answer(
        "👨‍💼 <b>VIZU Academy Admin Panel</b>",
        parse_mode="HTML",
        reply_markup=admin_menu,
    )
# =========================================================
# ADMIN EXIT
# =========================================================

@router.message(F.text == "⬅️ Admin Chiqish")
async def admin_exit(message: Message):

    if message.from_user.id not in ADMIN_IDS:
        return

    await message.answer(
        "🏠 Asosiy menyuga qaytildi.",
        reply_markup=main_menu,
    )
# =========================================================
# STATISTICS
# =========================================================

@router.message(F.text == "📊 Statistika")
async def statistics(message: Message):

    if message.from_user.id not in ADMIN_IDS:
        return

    total_users = get_total_users()
    approved_users = get_approved_users()
    blocked_users = get_blocked_users()

    payment = get_payment_statistics()

    text = f"""
📊 <b>VIZU Academy Statistikasi</b>

━━━━━━━━━━━━━━━━━━

👥 <b>Foydalanuvchilar</b>

• Jami: {total_users}
• Tasdiqlangan: {approved_users}
• Bloklangan: {blocked_users}

━━━━━━━━━━━━━━━━━━

💳 <b>To'lovlar</b>

• Jami: {payment['total_payments']}
• Tasdiqlangan: {payment['approved']}
• Kutilmoqda: {payment['pending']}
• Rad etilgan: {payment['rejected']}
• Bekor qilingan: {payment['cancelled']}
• Refund: {payment['refunded']}

━━━━━━━━━━━━━━━━━━

💰 <b>Daromad</b>

• Bugun: {payment['today_income']:,} so'm
• Oy: {payment['monthly_income']:,} so'm
• Umumiy: {payment['total_income']:,} so'm
"""

    await message.answer(
        text,
        parse_mode="HTML",
    )
# =========================================================
# USERS
# =========================================================

from database.users import (
    get_total_users,
    get_approved_users,
    get_blocked_users,
    get_latest_users,
)


@router.message(F.text == "👥 Foydalanuvchilar")
async def users(message: Message):

    if message.from_user.id not in ADMIN_IDS:
        return

    total = get_total_users()
    approved = get_approved_users()
    blocked = get_blocked_users()

    latest_users = get_latest_users(limit=10)

    text = f"""
👥 <b>Foydalanuvchilar</b>

━━━━━━━━━━━━━━━━━━

📊 <b>Umumiy</b>

• Jami: {total}
• Tasdiqlangan: {approved}
• Bloklangan: {blocked}

━━━━━━━━━━━━━━━━━━

🆕 <b>Oxirgi 10 foydalanuvchi</b>

"""

    if latest_users:

        for user in latest_users:

            username = (
                f"@{user['username']}"
                if user.get("username")
                else "—"
            )

            full_name = (
                user["full_name"]
                if user.get("full_name")
                else "-"
            )

            text += (
                f"👤 {full_name}\n"
                f"🆔 <code>{user['user_id']}</code>\n"
                f"👨‍💻 {username}\n\n"
            )

    else:

        text += "Ma'lumot topilmadi."

    await message.answer(
        text,
        parse_mode="HTML",
    )
# =========================================================
# LATEST USERS
# =========================================================

def get_latest_users(limit=10):

    rows = db_execute(
        """
        SELECT
            user_id,
            full_name,
            username
        FROM users
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (limit,),
        fetchall=True,
    )

    return rows
# =========================================================
# BUYERS
# =========================================================

@router.message(F.text == "💳 Xaridorlar")
async def buyers(message: Message):

    if message.from_user.id not in ADMIN_IDS:
        return

    buyers = get_approved_payments()

    if not buyers:
        await message.answer(
            "📭 Hozircha tasdiqlangan xaridorlar mavjud emas."
        )
        return

    text = (
        "💳 <b>VIZU Academy Xaridorlari</b>\n\n"
    )

    for buyer in buyers:

        username = (
            f"@{buyer['username']}"
            if buyer.get("username")
            else "—"
        )

        block = (
            f"🆔 <b>#{buyer['id']}</b>\n"
            f"👤 {buyer['full_name']}\n"
            f"📱 {buyer['phone']}\n"
            f"👨‍💻 {username}\n"
            f"📚 {buyer['course']}\n"
            f"💰 {buyer['amount']:,} so'm\n"
            f"━━━━━━━━━━━━━━━━━━\n"
        )

        if len(text) + len(block) > 3800:
            await message.answer(
                text,
                parse_mode="HTML",
            )
            text = ""

        text += block

    if text:
        await message.answer(
            text,
            parse_mode="HTML",
        )
