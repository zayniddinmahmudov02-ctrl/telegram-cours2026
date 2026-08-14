# =========================================================
# IMPORTS
# =========================================================

import asyncio

from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile, Message

from config import LEVEL_ORDER
from services.auth import is_admin

from keyboards.admin import admin_menu, users_menu
from keyboards.main import main_menu_for
from keyboards.inline.certificate import (
    admin_certificates_keyboard,
    admin_certificates_browse_keyboard,
)

from database.users import (
    get_total_users,
    blocked_count,
    deleted_count,
    premium_count,
    today_users_count,
    yesterday_users_count,
    weekly_users_count,
    monthly_users_count,
    today_active_users_count,
    weekly_active_users_count,
)

from database.payments import (
    get_approved_payments,
    get_recent_payments,
    get_payment_statistics,
    get_distinct_buyers_count,
)

from database.certificates import (
    wordgame_certificates_count,
    level_certificates,
    get_recent_certificates,
    get_certificate,
)

from services.certificate_generator import get_certificate_file_path
from services.logger import logger

router = Router()

# =========================================================
# ADMIN PANEL
# =========================================================

@router.message(F.text.in_({"/admin", "👨‍💼 Admin Panel"}))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
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

    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "🏠 Asosiy menyuga qaytildi.",
        reply_markup=main_menu_for(message.from_user.id),
    )
# =========================================================
# STATISTICS
# =========================================================

@router.message(F.text == "📊 Statistika")
async def statistics(message: Message):

    if not is_admin(message.from_user.id):
        return

    # All independent reads - fetched concurrently instead of
    # 12 sequential round trips.
    (
        total_users,
        total_buyers,
        payment_stats,
        wordgame_certificates,
        today_new,
        yesterday_new,
        weekly_new,
        monthly_new,
        today_active,
        weekly_active,
        premium,
        blocked,
        deleted,
    ) = await asyncio.gather(
        get_total_users(),
        get_distinct_buyers_count(),
        get_payment_statistics(),
        wordgame_certificates_count(),
        today_users_count(),
        yesterday_users_count(),
        weekly_users_count(),
        monthly_users_count(),
        today_active_users_count(),
        weekly_active_users_count(),
        premium_count(),
        blocked_count(),
        deleted_count(),
    )

    course_sales = payment_stats["approved"]

    text = f"""
📊 <b>VIZU Academy Statistikasi</b>

━━━━━━━━━━━━━━━━━━

👥 Jami foydalanuvchilar: <b>{total_users}</b>
💳 Jami kurs xaridorlari: <b>{total_buyers}</b>
🛒 Kurs sotuvlari: <b>{course_sales}</b>
🏆 So'z O'yini sertifikatlari: <b>{wordgame_certificates}</b>

━━━━━━━━━━━━━━━━━━
📈 <b>Ro'yxatdan o'tish</b>

🆕 Bugun: <b>{today_new}</b>
📅 Kecha: <b>{yesterday_new}</b>
🗓 Shu hafta: <b>{weekly_new}</b>
📆 Shu oy: <b>{monthly_new}</b>

━━━━━━━━━━━━━━━━━━
🟢 <b>Faollik</b>

🟢 Bugun faol: <b>{today_active}</b>
🟢 Shu hafta faol: <b>{weekly_active}</b>

━━━━━━━━━━━━━━━━━━
⭐ Premium: <b>{premium}</b>
🚫 Bloklangan: <b>{blocked}</b>
🗑 O'chirilgan: <b>{deleted}</b>
"""

    await message.answer(
        text,
        parse_mode="HTML",
    )
# =========================================================
# USERS
# =========================================================

@router.message(F.text == "👥 Foydalanuvchilar")
async def users(message: Message):

    if not is_admin(message.from_user.id):
        return

    total = await get_total_users()

    await message.answer(
        f"👥 <b>Foydalanuvchilar</b>\n\nJami: <b>{total}</b>",
        parse_mode="HTML",
        reply_markup=users_menu,
    )


@router.message(F.text == "⬅️ Admin Panel")
async def back_to_admin_panel(message: Message):

    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "👨‍💼 <b>VIZU Academy Admin Panel</b>",
        parse_mode="HTML",
        reply_markup=admin_menu,
    )
# =========================================================
# BUYERS
# =========================================================

@router.message(F.text == "💳 Xaridorlar")
async def buyers(message: Message):

    if not is_admin(message.from_user.id):
        return

    buyers = await get_approved_payments()

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
# =========================================================
# PAYMENTS
# =========================================================

@router.message(F.text == "💰 To'lovlar")
async def payments(message: Message):

    if not is_admin(message.from_user.id):
        return

    payments = await get_recent_payments(limit=30)

    if not payments:
        await message.answer(
            "📭 To'lovlar mavjud emas."
        )
        return

    text = "💰 <b>Oxirgi To'lovlar</b>\n\n"

    for payment in payments:

        status = {
            "pending": "🟡 Kutilmoqda",
            "approved": "🟢 Tasdiqlangan",
            "rejected": "🔴 Rad etilgan",
            "cancelled": "⚫ Bekor qilingan",
            "refunded": "🔵 Refund",
        }.get(payment["status"], payment["status"])

        block = (
            f"🆔 <b>#{payment['id']}</b>\n"
            f"👤 {payment['full_name']}\n"
            f"📚 {payment['course']}\n"
            f"💰 {payment['amount']:,} so'm\n"
            f"{status}\n"
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
# =========================================================
# CERTIFICATES
# =========================================================

@router.message(F.text == "🏅 Certificates")
async def certificates_menu(message: Message):

    if not is_admin(message.from_user.id):
        return

    total, per_level = await asyncio.gather(
        wordgame_certificates_count(),
        asyncio.gather(
            *(level_certificates(level) for level in LEVEL_ORDER)
        ),
    )

    text = (
        "🏅 <b>Certificates</b>\n\n"
        f"• Jami: <b>{total}</b>\n"
    )

    for level, count in zip(LEVEL_ORDER, per_level):
        text += f"• {level}: <b>{count}</b>\n"

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=admin_certificates_keyboard(),
    )


@router.callback_query(F.data == "admin_cert:home")
async def certificates_home_callback(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    total, per_level = await asyncio.gather(
        wordgame_certificates_count(),
        asyncio.gather(
            *(level_certificates(level) for level in LEVEL_ORDER)
        ),
    )

    text = (
        "🏅 <b>Certificates</b>\n\n"
        f"• Jami: <b>{total}</b>\n"
    )

    for level, count in zip(LEVEL_ORDER, per_level):
        text += f"• {level}: <b>{count}</b>\n"

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=admin_certificates_keyboard(),
    )

    await callback.answer()


@router.callback_query(F.data == "admin_cert:browse")
async def certificates_browse(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    certificates = await get_recent_certificates(limit=20)

    if not certificates:

        await callback.message.edit_text(
            "📭 Hozircha berilgan sertifikatlar mavjud emas.",
            reply_markup=admin_certificates_browse_keyboard([]),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "📂 <b>Oxirgi 20 ta sertifikat</b>",
        parse_mode="HTML",
        reply_markup=admin_certificates_browse_keyboard(
            certificates
        ),
    )

    await callback.answer()


@router.callback_query(F.data.startswith("admin_cert:open:"))
async def certificates_open(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    certificate_id = callback.data.split(":", 2)[2]

    certificate = await get_certificate(certificate_id)

    if not certificate:
        await callback.answer(
            "❌ Sertifikat topilmadi.",
            show_alert=True,
        )
        return

    pdf_path = get_certificate_file_path(certificate_id)

    if not pdf_path.exists():
        await callback.answer(
            "❌ PDF fayli topilmadi.",
            show_alert=True,
        )
        return

    await callback.message.answer_document(
        FSInputFile(pdf_path),
        caption=(
            f"🏅 <b>{certificate['level']} W-Zertifikat</b>\n"
            f"👤 User ID: <code>{certificate['user_id']}</code>"
        ),
        parse_mode="HTML",
    )

    await callback.answer()