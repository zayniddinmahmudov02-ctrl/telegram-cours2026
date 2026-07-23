from aiogram import Router, F
from aiogram.types import Message

from database import db_execute
from keyboards import video_menu
from services.runtime import artikel_users
from config import COURSE_INFO

router = Router()
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

    if not info:
        await message.answer("❌ Kurs haqida ma'lumot topilmadi.")
        return

    text = (
        f"🎉 Hozirda barcha kurslar Katta CHEGIRMADA!\n\n"
        f"{course} Video Darslari\n\n"
        f"📚 {info['lessons']} dars\n\n"
        f"❌ Eski narx: {info['old_price']}\n"
        f"🔥 Chegirmadagi narx: {info['price']}\n\n"
        f"💳 To'lov:\n"
        f"9860 3501 4490 7192\n\n"
        f"👤 Zayniddinkhuja Makhmudov\n\n"
        f"📩 To'lovdan keyin chekni (rasm shaklida) shu botga yuboring.\n"
        f"Admin tasdiqlaydi va kurs havolasini yuboradi."
    )

    db_execute(
        "UPDATE users SET course=%s WHERE user_id=%s",
        (course, message.from_user.id)
    )

    await message.answer(text)


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