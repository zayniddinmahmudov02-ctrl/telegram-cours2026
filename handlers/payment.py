from aiogram import Router, F
from aiogram.types import CallbackQuery
from loader import bot
from config.settings import (
    COURSE_LINKS,
    GROUP_LINKS,
)

from database.payments import (
    get_payment,
    approve_payment as approve_payment_db,
    reject_payment as reject_payment_db,
)
router = Router()
# =========================================================
# LEGACY PAYMENTS
# =========================================================
# Video course sales are discontinued (see handlers.video), so no
# new payments are created anymore. The approve/reject buttons stay
# so receipts already posted to the admin channel before the
# shutdown can still be processed and their buyers still get access.

# =========================================================
# APPROVE PAYMENT
# =========================================================

@router.callback_query(
    F.data.startswith("approve_payment:")
)
async def approve_payment_callback(
    callback: CallbackQuery,
):
    payment_id = int(callback.data.split(":")[1])

    payment = await get_payment(payment_id)

    if payment is None:
        await callback.answer(
            "❌ To'lov topilmadi.",
            show_alert=True,
        )
        return

    # -------------------------------------------------
    # DATABASE
    # -------------------------------------------------

    await approve_payment_db(
        payment_id,
        callback.from_user.id,
    )

    # -------------------------------------------------
    # COURSE LINKS
    # -------------------------------------------------

    course_link = COURSE_LINKS.get(
        payment["course"],
        "-"
    )

    group_link = GROUP_LINKS.get(
        payment["course"],
        "-"
    )

    # -------------------------------------------------
    # USER MESSAGE
    # -------------------------------------------------

    await bot.send_message(
        chat_id=payment["user_id"],
        text=f"""
🎉 <b>To'lovingiz muvaffaqiyatli tasdiqlandi!</b>

━━━━━━━━━━━━━━━━━━

📚 <b>Kurs:</b>
{payment["course"]}

🎥 <b>Video kurs:</b>

{course_link}

👥 <b>Guruh:</b>

{group_link}

━━━━━━━━━━━━━━━━━━

📌 Endi Video Kurslar bo'limidan foydalanishingiz mumkin.

VIZU Academy'ni tanlaganingiz uchun rahmat! ❤️
""",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    # -------------------------------------------------
    # UPDATE CHANNEL POST
    # -------------------------------------------------

    await callback.message.edit_caption(
        caption=f"""
🟢 <b>TASDIQLANDI</b>

🆔 <b>Payment ID:</b>
{payment["id"]}

👤 <b>Ism:</b>
{payment["full_name"]}

👤 <b>Username:</b>
@{payment["username"] or "-"}

🆔 <b>User ID:</b>
<code>{payment["user_id"]}</code>

📱 <b>Telefon:</b>
{payment["phone"]}

📚 <b>Kurs:</b>
{payment["course"]}

💰 <b>Summa:</b>
{payment["amount"]:,} so'm

✅ <b>Holati:</b> TASDIQLANDI
""",
        parse_mode="HTML",
        reply_markup=None,
    )

    await callback.answer(
        "✅ To'lov tasdiqlandi."
    )
# =========================================================
# REJECT PAYMENT
# =========================================================

@router.callback_query(
    F.data.startswith("reject_payment:")
)
async def reject_payment_callback(
    callback: CallbackQuery,
):
    payment_id = int(callback.data.split(":")[1])

    payment = await get_payment(payment_id)

    if payment is None:
        await callback.answer(
            "❌ To'lov topilmadi.",
            show_alert=True,
        )
        return

    # Database
    await reject_payment_db(
        payment_id,
        callback.from_user.id,
    )

    # Userga xabar
    await bot.send_message(
        chat_id=payment["user_id"],
        text=f"""
❌ <b>To'lovingiz rad etildi.</b>

📚 <b>Kurs:</b>
{payment["course"]}

━━━━━━━━━━━━━━━

Administrator to'lovni tasdiqlamadi.

Iltimos:

• yangi chek yuboring;
yoki
• administrator bilan bog'laning.
""",
        parse_mode="HTML",
    )

    # Kanal postini yangilash
    await callback.message.edit_caption(
        caption=f"""
🔴 <b>RAD ETILDI</b>

🆔 <b>Payment ID:</b>
{payment["id"]}

👤 <b>Ism:</b>
{payment["full_name"]}

👤 <b>Username:</b>
@{payment["username"] or "-"}

🆔 <b>User ID:</b>
<code>{payment["user_id"]}</code>

📱 <b>Telefon:</b>
{payment["phone"]}

📚 <b>Kurs:</b>
{payment["course"]}

💰 <b>Summa:</b>
{payment["amount"]:,} so'm

❌ <b>Holati:</b> RAD ETILDI
""",
        parse_mode="HTML",
        reply_markup=None,
    )

    await callback.answer(
        "❌ To'lov rad etildi."
    )