import logging

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CopyTextButton,
)

from database import db_execute
from keyboards import video_menu
from services.runtime import artikel_users
from config import COURSE_INFO

router = Router()

logging.basicConfig(level=logging.INFO)

# =========================================================
# VIDEO COURSES
# =========================================================

@router.message(F.text == "🎥 Video Kurslar")
async def video_courses(message: Message):
    artikel_users.pop(message.from_user.id, None)

    await message.answer(
        "🎥 Kerakli kursni tanlang:",
        reply_markup=video_menu,
    )


# =========================================================
# SAMPLE LESSON
# =========================================================

@router.message(F.text == "🎬 Bepul Namuna Darslar")
async def sample_lesson(message: Message):

    await message.answer(
        "🎬 Bepul Namuna Dars:\n"
        "https://t.me/+yUxu7EOWyd82ODhi"
    )


# =========================================================
# PAYMENT KEYBOARD
# =========================================================

def payment_keyboard(course: str):

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 To'lov qilish",
                    callback_data=f"payment:{course}",
                )
            ],
        ]
    )


# =========================================================
# COURSE INFO
# =========================================================

async def send_course_info(
    message: Message,
    course: str,
):

    info = COURSE_INFO.get(course)

    if not info:
        await message.answer("❌ Kurs topilmadi.")
        return

    try:
        await db_execute(
            "UPDATE users SET course=%s WHERE user_id=%s",
            (
                course,
                message.from_user.id,
            ),
        )
    except Exception as e:
        logging.error(e)

    text = (
        f"🎉 <b>Hozirda barcha kurslar katta CHEGIRMADA!</b>\n\n"
        f"📚 <b>{course}</b>\n\n"
        f"🎥 Darslar soni: {info['lessons']}\n\n"
        f"❌ Eski narx: {info['old_price']}\n"
        f"🔥 Chegirma narxi: {info['price']}\n\n"
        f"💳 Quyidagi tugma orqali to'lov ma'lumotlarini oching."
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=payment_keyboard(course),
    )


# =========================================================
# COURSES
# =========================================================

@router.message(F.text == "🇩🇪 A1")
async def course_a1(message: Message):
    await send_course_info(message, "🇩🇪 A1")


@router.message(F.text == "🇩🇪 A2")
async def course_a2(message: Message):
    await send_course_info(message, "🇩🇪 A2")


@router.message(F.text == "🇩🇪 B1")
async def course_b1(message: Message):
    await send_course_info(message, "🇩🇪 B1")


@router.message(F.text == "🔥 A1-B1")
async def course_a1b1(message: Message):
    await send_course_info(message, "🔥 A1-B1")


@router.message(F.text == "🔥 A1-C1")
async def course_a1c1(message: Message):
    await send_course_info(message, "🔥 A1-C1")


# =========================================================
# PAYMENT INFO
# =========================================================

@router.callback_query(F.data.startswith("payment:"))
async def payment_info(callback: CallbackQuery):

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

📌 To'lovni amalga oshirgandan so'ng
<b>📷 Chekni yuborish</b> tugmasini bosing.
""",
        parse_mode="HTML",
        reply_markup=keyboard,
    )

    await callback.answer()