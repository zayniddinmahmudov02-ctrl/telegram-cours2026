import logging

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CopyTextButton,
)
from aiogram.fsm.context import FSMContext

from database import db_execute
from keyboards import video_menu
from services.runtime import artikel_users
from config import COURSE_INFO
from states.payment import PaymentState

router = Router()

CARD_NUMBER = "9860350144907192"

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
                    copy_text=CopyTextButton(
                        text=CARD_NUMBER
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ To'lov qildim",
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
        db_execute(
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
        f"💳 Kartaga to'lov qilib,"
        f" <b>\"✅ To'lov qildim\"</b> tugmasini bosing."
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
# START PAYMENT FSM
# =========================================================

@router.callback_query(F.data.startswith("payment:"))
async def start_payment(
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

    await state.update_data(
        course=course,
        amount=info["price"],
    )

    await state.set_state(
        PaymentState.waiting_receipt
    )

    await callback.message.answer(
        "📷 <b>To'lov chekini yuboring.</b>\n\n"
        "Rasm yoki PDF yuborishingiz mumkin.",
        parse_mode="HTML",
    )

    await callback.answer()