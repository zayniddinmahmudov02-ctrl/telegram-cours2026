import logging

logging.warning("RECEIPT HANDLER ISHLADI")
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
    ContentType,
)
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CopyTextButton,
)
from loader import bot

from config.settings import (
    ADMIN_ID,
    COURSE_INFO,
)
from aiogram.types import ReplyKeyboardRemove
from states.payment import PaymentState

from keyboards.payment import (
    admin_payment_keyboard,
)
from database.payments import (
    create_payment,
    get_payment,
    approve_payment as approve_payment_db,
    reject_payment as reject_payment_db,
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
):
    course = callback.data.split(":", 1)[1]

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 UzCard nusxalash",
                    copy_text=CopyTextButton(
                        text="9860350144907192",
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Visa Card nusxalash",
                    copy_text=CopyTextButton(
                        text="4448844427532174",
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="📷 Chekni yuborish",
                    callback_data=f"payment_receipt:{course}",
                )
            ],
        ]
    )

    await callback.message.answer(
        f"""
🎓 <b>{course}</b>

💳 <b>To'lov ma'lumotlari</b>

To'lovni <b>Click</b>, <b>Payme</b>, <b>Uzum Bank</b>, <b>Anorbank</b> yoki boshqa bank ilovalari hamda to'lov terminallari orqali amalga oshirishingiz mumkin.

━━━━━━━━━━━━━━━━━━━━

💳 <b>UzCard</b>

<code>9860 3501 4490 7192</code>

💳 <b>Visa Card</b>

<code>4448 8444 2753 2174</code>

👤 <b>Karta egasi</b>

<b>Zayniddinkhuja Makhmudov</b>

━━━━━━━━━━━━━━━━━━━━

📌 To'lovni amalga oshirgach
<b>📷 Chekni yuborish</b> tugmasini bosing.
""",
        parse_mode="HTML",
        reply_markup=keyboard,
    )

    await callback.answer()
# =========================================================
# RECEIPT STEP
# =========================================================

@router.callback_query(
    F.data.startswith("payment_receipt:")
)
async def payment_receipt(
    callback: CallbackQuery,
    state: FSMContext,
):
    course = callback.data.split(":", 1)[1]

    info = COURSE_INFO.get(course)

    if info is None:
        await callback.answer(
            "❌ Kurs topilmadi.",
            show_alert=True,
        )
        return

    await state.clear()

    await state.update_data(
        course=course,
        amount=info["price"],
    )

    await state.set_state(
        PaymentState.waiting_receipt
    )

    await callback.message.answer(
        """
📷 <b>To'lov chekini yuboring.</b>

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
        "📱 Telefon raqamingizni kiriting.",
    )
# =========================================================
# PHONE
# =========================================================

import re
import logging

logger = logging.getLogger(__name__)


@router.message(PaymentState.waiting_phone)
async def payment_phone(
    message: Message,
    state: FSMContext,
):
    try:
        # -------------------------------------------------
        # TEXT
        # -------------------------------------------------

        if not message.text:
            await message.answer(
                "❌ Telefon raqamingizni matn ko'rinishida kiriting."
            )
            return

        phone = message.text.strip()

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if re.search(r"[A-Za-zА-Яа-я]", phone):
            await message.answer(
                "❌ Telefon raqamda harflar bo'lmasligi kerak."
            )
            return

        if not re.fullmatch(r"[\d+\-\s()]+", phone):
            await message.answer(
                "❌ Telefon raqam noto'g'ri."
            )
            return

        digits = re.sub(r"\D", "", phone)

        if len(digits) < 7:
            await message.answer(
                "❌ Telefon raqam juda qisqa."
            )
            return

        # -------------------------------------------------
        # STATE
        # -------------------------------------------------

        await state.update_data(phone=phone)

        data = await state.get_data()

        required = (
            "full_name",
            "course",
            "amount",
            "receipt_file_id",
            "file_type",
        )

        for key in required:
            if key not in data:
                await state.clear()

                await message.answer(
                    "❌ To'lov jarayoni bekor qilindi.\n\n"
                    "Iltimos boshidan qayta urinib ko'ring."
                )
                return

        # -------------------------------------------------
        # CREATE PAYMENT
        # -------------------------------------------------

        payment_id = create_payment(
            user_id=message.from_user.id,
            full_name=data["full_name"],
            phone=phone,
            username=message.from_user.username or "",
            course=data["course"],
            amount=data["amount"],
            receipt_file_id=data["receipt_file_id"],
            file_type=data["file_type"],
        )

        if payment_id is None:
            await message.answer(
                "❌ To'lovni saqlab bo'lmadi."
            )
            return

        # -------------------------------------------------
        # ADMIN TEXT
        # -------------------------------------------------

        admin_text = f"""
🆕 <b>Yangi to'lov</b>

🆔 <b>Payment ID:</b> {payment_id}

👤 <b>Ism:</b>
{data["full_name"]}

👤 <b>Username:</b>
@{message.from_user.username or "-"}

🆔 <b>User ID:</b>
<code>{message.from_user.id}</code>

📱 <b>Telefon:</b>
{phone}

📚 <b>Kurs:</b>
{data["course"]}
"""

        # -------------------------------------------------
        # SEND TO ADMIN
        # -------------------------------------------------

        try:

            if data["file_type"] == "photo":

                await bot.send_photo(
                    chat_id=ADMIN_ID,
                    photo=data["receipt_file_id"],
                    caption=admin_text,
                    parse_mode="HTML",
                    reply_markup=admin_payment_keyboard(payment_id),
                )

            else:

                await bot.send_document(
                    chat_id=ADMIN_ID,
                    document=data["receipt_file_id"],
                    caption=admin_text,
                    parse_mode="HTML",
                    reply_markup=admin_payment_keyboard(payment_id),
                )

        except Exception:
            logger.exception("Adminga yuborishda xato")

            await message.answer(
                "❌ Administratorga yuborishda xatolik yuz berdi."
            )
            return

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        await message.answer(
            """
✅ <b>To'lovingiz muvaffaqiyatli yuborildi.</b>

📨 Chekingiz administratorga yuborildi.

⏳ Administrator tasdiqlagach kurs avtomatik ochiladi.
""",
            parse_mode="HTML",
        )

        await state.clear()

    except Exception:
        logger.exception("payment_phone umumiy xato")

        await state.clear()

        await message.answer(
            "❌ Kutilmagan xatolik yuz berdi.\n"
            "Iltimos qayta urinib ko'ring."
        )
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

    payment = get_payment(payment_id)

    if payment is None:
        await callback.answer(
            "❌ To'lov topilmadi.",
            show_alert=True,
        )
        return

    approve_payment_db(
        payment_id,
        callback.from_user.id,
    )

    await bot.send_message(
        chat_id=payment["user_id"],
        text=f"""
🎉 <b>To'lovingiz tasdiqlandi.</b>

📚 <b>Kurs:</b>
{payment["course"]}

✅ Endi Video Kurslar bo'limidan foydalanishingiz mumkin.
""",
        parse_mode="HTML",
    )

    await callback.message.edit_reply_markup(
        reply_markup=None
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

    payment = get_payment(payment_id)

    if payment is None:
        await callback.answer(
            "❌ To'lov topilmadi.",
            show_alert=True,
        )
        return

    reject_payment_db(
        payment_id,
        callback.from_user.id,
    )

    await bot.send_message(
        chat_id=payment["user_id"],
        text="""
❌ <b>To'lovingiz rad etildi.</b>

Iltimos yangi chek yuboring yoki administrator bilan bog'laning.
""",
        parse_mode="HTML",
    )

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await callback.answer(
        "❌ To'lov rad etildi."
    )