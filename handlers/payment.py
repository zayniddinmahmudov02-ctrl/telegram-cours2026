from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
)
from keyboards.payment import course_keyboard
from aiogram.fsm.context import FSMContext

from states.payment import PaymentState

from keyboards.payment import (
    phone_keyboard,
    confirm_keyboard,
)
from loader import bot

from database.payments import create_payment

from keyboards.payment import (
    admin_payment_keyboard,
)

from config.settings import ADMIN_IDS

from config.settings import COURSE_INFO

router = Router()
# =========================================================
# START PAYMENT
# =========================================================
@router.message(F.text == "💳 To'lov qilish")
async def start_payment(
    message: Message,
    state: FSMContext,
):
    await state.clear()

    await state.set_state(
        PaymentState.waiting_course
    )

    await message.answer(
        "💳 <b>Xarid qilmoqchi bo'lgan kursni tanlang.</b>",
        parse_mode="HTML",
        reply_markup=course_keyboard(),
    )
# =========================================================
# SELECT COURSE
# =========================================================

@router.callback_query(
    PaymentState.waiting_course,
    F.data.startswith("course:")
)
async def select_course(
    callback: CallbackQuery,
    state: FSMContext,
):
    course = callback.data.split(":")[1]

    amount = COURSE_INFO[course]

    await state.update_data(
        course=course,
        amount=amount,
    )

    await state.set_state(
        PaymentState.waiting_receipt
    )

    await callback.message.edit_text(
        f"""
📚 <b>Kurs:</b> {course}

💰 <b>Narx:</b> {amount:,} so'm

────────────────

📷 To'lov chekini yuboring.

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
async def payment_receipt_photo(
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
async def payment_receipt_document(
    message: Message,
    state: FSMContext,
):
    document = message.document

    if document.mime_type != "application/pdf":
        await message.answer(
            "❌ Faqat PDF hujjat yuborishingiz mumkin."
        )
        return

    await state.update_data(
        receipt_file_id=document.file_id,
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

    # Kamida ism va familiya bo'lishi kerak
    if len(full_name.split()) < 2:
        await message.answer(
            "❌ Ism va familiyangizni to'liq kiriting.\n\n"
            "Masalan:\n"
            "Ali Valiyev"
        )
        return

    # Juda qisqa bo'lmasin
    if len(full_name) < 5:
        await message.answer(
            "❌ Ism juda qisqa."
        )
        return

    # Faqat harflar, probel, apostrof va tire
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

💰 <b>Narx:</b>
{data['amount']:,} so'm

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
# INVALID PHONE
# =========================================================

@router.message(
    PaymentState.waiting_phone,
)
async def invalid_phone(
    message: Message,
):
    await message.answer(
        "📱 Telefon raqamingizni tugma orqali yuboring.",
        reply_markup=phone_keyboard,
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
        amount=data["amount"],
        receipt_file_id=data["receipt_file_id"],
        file_type=data["file_type"],
    )

    admin_text = f"""
🆕 <b>Yangi to'lov</b>

🆔 <b>Payment ID:</b> {payment_id}

👤 <b>Ism:</b>
{data["full_name"]}

👤 <b>Telegram:</b>
@{callback.from_user.username or '-'}

🆔 <b>User ID:</b>
<code>{callback.from_user.id}</code>

📱 <b>Telefon:</b>
{data["phone"]}

📚 <b>Kurs:</b>
{data["course"]}

💰 <b>Summa:</b>
{data["amount"]:,} so'm
"""

    for admin_id in ADMIN_IDS:

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
✅ <b>To'lovingiz qabul qilindi.</b>

Chekingiz administratorga yuborildi.

Tekshiruvdan so'ng sizga avtomatik xabar yuboriladi.
""",
        parse_mode="HTML",
    )

    await state.clear()

    await callback.answer()
