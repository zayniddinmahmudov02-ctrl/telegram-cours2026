import logging

logging.warning("RECEIPT HANDLER ISHLADI")
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
    ContentType,
)
from aiogram.fsm.context import FSMContext

from loader import bot

from config.settings import (
    ADMIN_ID,
    COURSE_INFO,
)

from states.payment import PaymentState

from keyboards.payment import (
    phone_keyboard,
    confirm_keyboard,
    admin_payment_keyboard,
)

from database.payments import (
    create_payment,
    get_payment,
    approve_payment,
    reject_payment,
)

router = Router()
# =========================================================
# START PAYMENT
# =========================================================

@router.callback_query(
    F.data.startswith("payment:")
)
async def start_payment(
    callback: CallbackQuery,
    state: FSMContext,
):
    course = callback.data.split(":")[1]

    await state.clear()

    await state.update_data(
        course=course,
    )

    await state.set_state(
        PaymentState.waiting_receipt
    )

    await callback.message.answer(
        f"""
🎉 <b>{course}</b>

📷 Endi to'lov chekini yuboring.

Qabul qilinadi:

• JPG
• PNG
• PDF
""",
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# RECEIPT (PHOTO)
# =========================================================

@router.message(
    PaymentState.waiting_receipt,
    F.photo,
)
async def receipt_photo(
    message: Message,
    state: FSMContext,
):
    await state.update_data(
        receipt_file_id=message.photo[-1].file_id,
        file_type="photo",
    )

    await state.set_state(
        PaymentState.waiting_full_name
    )

    await message.answer(
        "👤 Ism va familiyangizni kiriting."
    )


# =========================================================
# RECEIPT (PDF)
# =========================================================

@router.message(
    PaymentState.waiting_receipt,
    F.document,
)
async def receipt_pdf(
    message: Message,
    state: FSMContext,
):
    if message.document.mime_type != "application/pdf":

        await message.answer(
            "❌ Faqat PDF yuborishingiz mumkin."
        )
        return

    await state.update_data(
        receipt_file_id=message.document.file_id,
        file_type="pdf",
    )

    await state.set_state(
        PaymentState.waiting_full_name
    )

    await message.answer(
        "👤 Ism va familiyangizni kiriting."
    )


# =========================================================
# INVALID RECEIPT
# =========================================================

@router.message(
    PaymentState.waiting_receipt,
)
async def invalid_receipt(
    message: Message,
):
    await message.answer(
        """
❌ To'lov chekini yuboring.

Qabul qilinadi:

📷 JPG

📷 PNG

📄 PDF
"""
    )
# =========================================================
# FULL NAME
# =========================================================

import re

@router.message(
    PaymentState.waiting_full_name,
)
async def payment_full_name(
    message: Message,
    state: FSMContext,
):
    full_name = message.text.strip()

    if len(full_name.split()) < 2:
        await message.answer(
            "❌ Ism va familiyangizni to'liq kiriting.\n\n"
            "Masalan:\n"
            "Ali Valiyev"
        )
        return

    if len(full_name) < 5:
        await message.answer(
            "❌ Ism juda qisqa."
        )
        return

    if not re.fullmatch(r"[A-Za-zÀ-ÿʻ'`\- ]+", full_name):
        await message.answer(
            "❌ Ismda faqat harflardan foydalaning."
        )
        return

    await state.update_data(
        full_name=full_name,
    )

    await state.set_state(
        PaymentState.waiting_phone
    )

    await message.answer(
        "📱 Telefon raqamingizni yuboring.",
        reply_markup=phone_keyboard,
    )


# =========================================================
# INVALID PHONE
# =========================================================

@router.message(
    PaymentState.waiting_phone,
)
async def invalid_phone(
    message: Message,
):
    await message.answer(
        "📱 Telefon raqamingizni pastdagi tugma orqali yuboring.",
        reply_markup=phone_keyboard,
    )


# =========================================================
# PHONE
# =========================================================

@router.message(
    PaymentState.waiting_phone,
    F.contact,
)
async def payment_phone(
    message: Message,
    state: FSMContext,
):
    phone = message.contact.phone_number

    await state.update_data(
        phone=phone,
    )

    data = await state.get_data()

    text = f"""
📝 <b>To'lov ma'lumotlari</b>

👤 <b>Ism:</b>
{data['full_name']}

📚 <b>Kurs:</b>
{data['course']}

📱 <b>Telefon:</b>
{phone}

────────────────

Ma'lumotlarni tekshiring.
"""

    await state.set_state(
        PaymentState.waiting_confirm
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=confirm_keyboard,
    )
# =========================================================
# CONFIRM PAYMENT
# =========================================================

@router.callback_query(
    PaymentState.waiting_confirm,
    F.data == "payment_confirm",
)
async def confirm_payment(
    callback: CallbackQuery,
    state: FSMContext,
):

    data = await state.get_data()

    payment_id = create_payment(
        user_id=callback.from_user.id,
        full_name=data["full_name"],
        phone=data["phone"],
        username=callback.from_user.username or "",
        course=data["course"],
        receipt_file_id=data["receipt_file_id"],
        file_type=data["file_type"],
    )

    admin_text = f"""
🆕 <b>Yangi to'lov</b>

🆔 <b>Payment ID:</b> {payment_id}

👤 <b>Ism:</b>
{data["full_name"]}

👤 <b>Username:</b>
@{callback.from_user.username or "-"}

🆔 <b>User ID:</b>
<code>{callback.from_user.id}</code>

📱 <b>Telefon:</b>
{data["phone"]}

📚 <b>Kurs:</b>
{data["course"]}
"""

    for admin_id in ADMIN_ID:

        if data["file_type"] == "photo":

            await bot.send_photo(
                chat_id=admin_id,
                photo=data["receipt_file_id"],
                caption=admin_text,
                parse_mode="HTML",
                reply_markup=admin_payment_keyboard(payment_id),
            )

        else:

            await bot.send_document(
                chat_id=admin_id,
                document=data["receipt_file_id"],
                caption=admin_text,
                parse_mode="HTML",
                reply_markup=admin_payment_keyboard(payment_id),
            )

    await callback.message.edit_text(
        """
✅ <b>To'lovingiz muvaffaqiyatli yuborildi.</b>

📨 Chekingiz administratorga yuborildi.

Tasdiqlangandan so'ng kurs avtomatik ochiladi.
""",
        parse_mode="HTML",
    )

    await state.clear()

    await callback.answer()
# =========================================================
# APPROVE PAYMENT
# =========================================================

@router.callback_query(
    F.data.startswith("approve_payment:")
)
async def approve_payment(
    callback: CallbackQuery,
):

    payment_id = int(
        callback.data.split(":")[1]
    )

    payment = get_payment(
        payment_id
    )

    if payment is None:

        await callback.answer(
            "❌ To'lov topilmadi.",
            show_alert=True,
        )

        return

    approve_payment(
    payment_id,
    callback.from_user.id,
)

    await bot.send_message(
        chat_id=payment["user_id"],
        text=f"""
🎉 <b>To'lovingiz tasdiqlandi.</b>

📚 Kurs:
{payment["course"]}

✅ Endi Video Kurslar bo'limidan foydalanishingiz mumkin.

Omad tilaymiz!
""",
        parse_mode="HTML",
    )

    await callback.message.edit_reply_markup()

    await callback.answer(
        "✅ To'lov tasdiqlandi."
    )
# =========================================================
# REJECT PAYMENT
# =========================================================

@router.callback_query(
    F.data.startswith("reject_payment:")
)
async def reject_payment(
    callback: CallbackQuery,
):

    payment_id = int(
        callback.data.split(":")[1]
    )

    payment = get_payment(
        payment_id
    )

    if payment is None:

        await callback.answer(
            "❌ To'lov topilmadi.",
            show_alert=True,
        )

        return

    reject_payment(
    payment_id,
    callback.from_user.id,
)

    await bot.send_message(
        chat_id=payment["user_id"],
        text="""
❌ <b>To'lov tasdiqlanmadi.</b>

Iltimos chekni qayta yuboring yoki administrator bilan bog'laning.
""",
        parse_mode="HTML",
    )

    await callback.message.edit_reply_markup()

    await callback.answer(
        "❌ To'lov rad etildi."
    )