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

print("VIDEO ROUTER LOADED")
# =========================================================
# VIDEO COURSES
# =========================================================

@router.message(F.text == "🎥 Video Kurslar")
async def video_courses(message: Message):
    artikel_users.pop(message.from_user.id, None)

    await message.answer(
        "🎥 Kerakli kursni tanlang:",
        reply_markup=video_menu
    )

# =========================================================
# PAYMENT KEYBOARD
# =========================================================

CARD_NUMBER = "9860350144907192"


def payment_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 To'lov qilish",
                    copy_text=CopyTextButton(
                        text=CARD_NUMBER
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ To'lov qildim",
                    callback_data="payment_done"
                )
            ]
        ]
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
# COURSE INFO
# =========================================================
async def send_course_info(message: Message, course: str):
    info = COURSE_INFO.get(course)

    if info is None:
        await message.answer("❌ Kurs haqida ma'lumot topilmadi.")
        return

    text = (
        f"🎉 Hozirda barcha kurslar Katta CHEGIRMADA!\n\n"
        f"{course} Video Darslari\n\n"
        f"📚 {info['lessons']} ta dars\n\n"
        f"❌ Eski narx: {info['old_price']}\n"
        f"🔥 Chegirmadagi narx: {info['price']}\n\n"
    )

    try:
        db_execute(
            "UPDATE users SET course=%s WHERE user_id=%s",
            (course, message.from_user.id)
        )
    except Exception as e:
        print("DB ERROR:", e)
    await message.answer(
    text,
    reply_markup=payment_keyboard()
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
# PAYMENT DONE
# =========================================================

@router.callback_query(F.data == "payment_done")
async def payment_done(
    callback: CallbackQuery,
):

    await callback.message.answer(
        "🎉 Ajoyib!\n\n"
        "📷 Endi to'lov chekini (rasm) yuboring."
    )

    await callback.answer()