from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    Message,
)

from keyboards.homework import (
    homework_menu_keyboard,
)

from keyboards.main import main_menu_keyboard

from handlers import (
    homework_online,
    homework_video,
    homework_speaking,
    teacher_chat,
)

router = Router()
# =========================================================
# HOMEWORK MENU
# =========================================================

@router.message(F.text == "🏠 Homework")
async def homework_menu(message: Message):
    await message.answer(
        "🏠 <b>Homework</b>\n\n"
        "Kerakli bo'limni tanlang.",
        reply_markup=homework_menu_keyboard(),
    )


@router.callback_query(F.data == "homework")
async def homework_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏠 <b>Homework</b>\n\n"
        "Kerakli bo'limni tanlang.",
        reply_markup=homework_menu_keyboard(),
    )
    await callback.answer()


# =========================================================
# ONLINE HOMEWORK
# =========================================================

@router.callback_query(F.data == "hw_online")
async def online_homework(callback: CallbackQuery):
    await callback.answer()
    await homework_online.open_levels(callback)


# =========================================================
# VIDEO HOMEWORK
# =========================================================

@router.callback_query(F.data == "hw_video")
async def video_homework(callback: CallbackQuery):
    await callback.answer()
    await homework_video.open_levels(callback)


# =========================================================
# SPEAKING HOMEWORK
# =========================================================

@router.callback_query(F.data == "hw_speaking")
async def speaking_homework(callback: CallbackQuery):
    await callback.answer()
    await homework_speaking.open_levels(callback)


# =========================================================
# TEACHER CHAT
# =========================================================

@router.callback_query(F.data == "hw_teacher")
async def teacher(callback: CallbackQuery):
    await callback.answer()
    await teacher_chat.open_teacher(callback)


# =========================================================
# BACK TO MAIN MENU
# =========================================================

@router.callback_query(F.data == "hw_back")
async def back(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏠 <b>Asosiy menyu</b>",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()