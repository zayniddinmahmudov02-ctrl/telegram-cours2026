# =========================================================
# IMPORTS
# =========================================================

from aiogram import Router, F
from aiogram.types import CallbackQuery

from loader import bot

from config.settings import (
    BUYERS_CHANNEL_ID,
    COURSE_LINKS,
    GROUP_LINKS,
)

from database.users import approve_user

from database.payments import (
    get_payment,
    approve_payment,
    reject_payment,
)

router = Router()

# =========================================================
# APPROVE PAYMENT
# =========================================================

@router.callback_query(F.data.startswith("approve_payment:"))
async def approve_payment_callback(
    callback: CallbackQuery,
):
    payment_id = int(callback.data.split(":")[1])

    payment = get_payment(payment_id)

    if payment is None:
        await callback.answer(
            "❌ To'lov topilmadi.",
            show_alert=True,
        )
        return

    if payment["status"] == "approved":
        await callback.answer(
            "Bu to'lov allaqachon tasdiqlangan.",
            show_alert=True,
        )
        return

    # Payment approve
    approve_payment(
        payment_id,
        callback.from_user.id,
    )

    # User approve
    approve_user(
        payment["user_id"]
    )

    course_link = COURSE_LINKS.get(
        payment["course"],
        "-"
    )

    group_link = GROUP_LINKS.get(
        payment["course"],
        "-"
    )

    text = f"""
🎉 <b>To'lovingiz muvaffaqiyatli tasdiqlandi!</b>

👤 <b>{payment['full_name']}</b>

📚 <b>Kurs:</b> {payment['course']}

━━━━━━━━━━━━━━━━━━

🎥 <b>Kurs kanali:</b>

{course_link}

👥 <b>Guruh havolasi:</b>

{group_link}

━━━━━━━━━━━━━━━━━━

✅ Avval kanalga,
so'ng guruhga qo'shiling.

VIZU Academy'ni tanlaganingiz uchun rahmat! 🇩🇪
"""

    await bot.send_message(
        chat_id=payment["user_id"],
        text=text,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    buyer_text = f"""
🎉 <b>Yangi o'quvchi qo'shildi</b>

👤 <b>{payment['full_name']}</b>

📚 {payment['course']}

🆔 <code>{payment['user_id']}</code>

Xush kelibsiz 🇩🇪
"""

    await bot.send_message(
        chat_id=BUYERS_CHANNEL_ID,
        text=buyer_text,
        parse_mode="HTML",
    )

    if callback.message.photo:

        caption = callback.message.caption or ""

        await callback.message.edit_caption(
            caption=caption + "\n\n✅ <b>TASDIQLANDI</b>",
            parse_mode="HTML",
            reply_markup=None,
        )

    else:

        text = callback.message.text or ""

        await callback.message.edit_text(
            text + "\n\n✅ <b>TASDIQLANDI</b>",
            parse_mode="HTML",
            reply_markup=None,
        )

    await callback.answer(
        "✅ To'lov tasdiqlandi."
    )


# =========================================================
# REJECT PAYMENT
# =========================================================

@router.callback_query(F.data.startswith("reject_payment:"))
async def reject_payment_callback(
    callback: CallbackQuery,
):
    payment_id = int(callback.data.split(":")[1])

    payment = get_payment(payment_id)

    if payment is None:
        await callback.answer(
            "❌ To'lov topilmadi.",
            show_alert=True,
        )
        return

    if payment["status"] == "rejected":
        await callback.answer(
            "Bu to'lov allaqachon rad etilgan.",
            show_alert=True,
        )
        return

    reject_payment(
        payment_id,
        callback.from_user.id,
    )

    reject_text = f"""
❌ <b>To'lovingiz rad etildi.</b>

📚 <b>Kurs:</b> {payment['course']}

Administrator to'lovni tasdiqlamadi.

Iltimos chekni qayta yuboring yoki administrator bilan bog'laning.
"""

    await bot.send_message(
        chat_id=payment["user_id"],
        text=reject_text,
        parse_mode="HTML",
    )

    if callback.message.photo:

        caption = callback.message.caption or ""

        await callback.message.edit_caption(
            caption=caption + "\n\n❌ <b>RAD ETILDI</b>",
            parse_mode="HTML",
            reply_markup=None,
        )

    else:

        text = callback.message.text or ""

        await callback.message.edit_text(
            text + "\n\n❌ <b>RAD ETILDI</b>",
            parse_mode="HTML",
            reply_markup=None,
        )

    await callback.answer(
        "❌ To'lov rad etildi."
    )