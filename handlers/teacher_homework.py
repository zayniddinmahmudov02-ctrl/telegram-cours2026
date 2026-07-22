from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from loader import bot, dp
from database import *
from config import TEACHER_CHANNEL_ID

# =========================================================
# RATING KEYBOARD
# =========================================================

def rating_keyboard(submission_id):
    keyboard = InlineKeyboardMarkup(row_width=5)
    keyboard.add(
        InlineKeyboardButton("⭐1", callback_data=f"hw_rate:{submission_id}:1"),
        InlineKeyboardButton("⭐2", callback_data=f"hw_rate:{submission_id}:2"),
        InlineKeyboardButton("⭐3", callback_data=f"hw_rate:{submission_id}:3"),
        InlineKeyboardButton("⭐4", callback_data=f"hw_rate:{submission_id}:4"),
        InlineKeyboardButton("⭐5", callback_data=f"hw_rate:{submission_id}:5")
    )
    return keyboard

# =========================================================
# SEND HOMEWORK
# =========================================================

async def send_homework_to_teacher(submission_id, state):
    submission = get_homework_submission(submission_id)
    files = get_homework_files(submission_id)

    text = (
        "📥 <b>Yangi Homework</b>\n\n"
        f"👤 {submission['full_name']}\n"
        f"🆔 {submission['user_id']}\n\n"
        f"📂 {submission['category']}\n"
        f"📚 {submission['level']}\n"
        f"📖 Lesson {submission['lesson']}\n"
    )

    if submission["category"] == "Speaking":
        text += f"📝 Task {submission['task_number']}\n"
    else:
        text += f"📘 {submission['kompetenz']}\n"

    text += f"\n📎 Materiallar: {len(files)} ta"

    await bot.send_message(
        TEACHER_CHANNEL_ID,
        text,
        parse_mode="HTML",
        reply_markup=rating_keyboard(submission_id)
    )

    for file in files:
        if file["type"] == "photo":
            await bot.send_photo(
                TEACHER_CHANNEL_ID,
                file["file_id"]
            )
        elif file["type"] == "voice":
            await bot.send_voice(
                TEACHER_CHANNEL_ID,
                file["file_id"]
            )
        elif file["type"] == "audio":
            await bot.send_audio(
                TEACHER_CHANNEL_ID,
                file["file_id"]
            )
        elif file["type"] == "document":
            await bot.send_document(
                TEACHER_CHANNEL_ID,
                file["file_id"]
            )
        elif file["type"] == "text":
            await bot.send_message(
                TEACHER_CHANNEL_ID,
                f"📝\n\n{file['text']}"
            )

# =========================================================
# RATING
# =========================================================

@dp.callback_query_handler(lambda c: c.data.startswith("hw_rate:"))
async def homework_rating(callback: types.CallbackQuery):
    _, submission_id, stars = callback.data.split(":")
    submission_id = int(submission_id)
    stars = int(stars)

    save_homework_score(
        submission_id,
        callback.from_user.id,
        stars
    )

    submission = get_homework_submission(submission_id)

    await bot.send_message(
        submission["user_id"],
        f"🎉 Homework tekshirildi.\n\n"
        f"⭐ Baho: {stars}/5"
    )

    await callback.answer("Baho saqlandi.")