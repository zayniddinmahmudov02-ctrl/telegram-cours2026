# =========================================================
# IMPORTS
# =========================================================

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

from services.certificate_generator import (
    generate_certificate,
    get_certificate_file_path,
)
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

    total_users = get_total_users()
    total_buyers = get_distinct_buyers_count()
    course_sales = get_payment_statistics()["approved"]
    wordgame_certificates = wordgame_certificates_count()

    text = f"""
📊 <b>VIZU Academy Statistikasi</b>

━━━━━━━━━━━━━━━━━━

👥 Jami foydalanuvchilar: <b>{total_users}</b>
💳 Jami kurs xaridorlari: <b>{total_buyers}</b>
🛒 Kurs sotuvlari: <b>{course_sales}</b>
🏆 So'z O'yini sertifikatlari: <b>{wordgame_certificates}</b>

━━━━━━━━━━━━━━━━━━
📈 <b>Ro'yxatdan o'tish</b>

🆕 Bugun: <b>{today_users_count()}</b>
📅 Kecha: <b>{yesterday_users_count()}</b>
🗓 Shu hafta: <b>{weekly_users_count()}</b>
📆 Shu oy: <b>{monthly_users_count()}</b>

━━━━━━━━━━━━━━━━━━
🟢 <b>Faollik</b>

🟢 Bugun faol: <b>{today_active_users_count()}</b>
🟢 Shu hafta faol: <b>{weekly_active_users_count()}</b>

━━━━━━━━━━━━━━━━━━
⭐ Premium: <b>{premium_count()}</b>
🚫 Bloklangan: <b>{blocked_count()}</b>
🗑 O'chirilgan: <b>{deleted_count()}</b>
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

    total = get_total_users()

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
# =========================================================
# PAYMENTS
# =========================================================

@router.message(F.text == "💰 To'lovlar")
async def payments(message: Message):

    if not is_admin(message.from_user.id):
        return

    payments = get_recent_payments(limit=30)

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

    total = wordgame_certificates_count()

    text = (
        "🏅 <b>Certificates</b>\n\n"
        f"• Jami: <b>{total}</b>\n"
    )

    for level in LEVEL_ORDER:
        text += (
            f"• {level}: <b>{level_certificates(level)}</b>\n"
        )

    text += (
        "\n🧪 Test rejimi - istalgan darajani tanlab, "
        "progress 0% bo'lsa ham namuna sertifikat oling."
    )

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

    total = wordgame_certificates_count()

    text = (
        "🏅 <b>Certificates</b>\n\n"
        f"• Jami: <b>{total}</b>\n"
    )

    for level in LEVEL_ORDER:
        text += (
            f"• {level}: <b>{level_certificates(level)}</b>\n"
        )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=admin_certificates_keyboard(),
    )

    await callback.answer()


@router.callback_query(F.data.startswith("admin_cert:generate:"))
async def certificates_generate_test(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    level = callback.data.split(":")[2]

    await callback.answer(
        "⏳ Test sertifikat tayyorlanmoqda..."
    )

    try:
        pdf_path = generate_certificate(
            user_id=callback.from_user.id,
            level=level,
            admin_override=True,
        )

    except Exception as e:

        logger.error(
            f"Admin test certificate generation failed "
            f"(admin={callback.from_user.id}, level={level}): {e}"
        )

        await callback.message.answer(
            "❌ Sertifikatni tayyorlashda xatolik yuz berdi."
        )
        return

    await callback.message.answer_document(
        FSInputFile(pdf_path),
        caption=(
            f"🧪 <b>{level} W-Zertifikat (TEST)</b>\n\n"
            "Faqat admin uchun namuna - progress talab qilinmadi."
        ),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin_cert:browse")
async def certificates_browse(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    certificates = get_recent_certificates(limit=20)

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

    certificate = get_certificate(certificate_id)

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