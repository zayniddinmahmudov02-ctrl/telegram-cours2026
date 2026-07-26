from aiogram import Router, F
from aiogram.types import CallbackQuery

from keyboards.homework import (
    homework_levels_keyboard,
    homework_lessons_keyboard,
)

router = Router()


# =========================================================
# ONLINE HOMEWORK
# =========================================================

async def open_levels(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎓 <b>Online Kurs Homework</b>\n\n"
        "Darajani tanlang.",
        reply_markup=homework_levels_keyboard(
            course_type="online"
        ),
    )
    await callback.answer()


# =========================================================
# LEVELS
# =========================================================

@router.callback_query(F.data.startswith("hw_online_level:"))
async def online_level(callback: CallbackQuery):

    level = callback.data.split(":")[1]

    lesson_counts = {
        "A1": 14,
        "A2": 14,
        "B1": 20,
        "B2": 30,
        "C1": 22,
    }

    await callback.message.edit_text(
        f"🎓 <b>{level} Homework</b>\n\n"
        "Darsni tanlang.",
        reply_markup=homework_lessons_keyboard(
            course_type="online",
            level=level,
            total_lessons=lesson_counts[level],
        ),
    )

    await callback.answer()
from aiogram import Router, F
from aiogram.types import CallbackQuery

from keyboards.homework import (
    homework_components_keyboard,
)


# =========================================================
# LESSON
# =========================================================

@router.callback_query(F.data.startswith("hw_online_lesson:"))
async def online_lesson(callback: CallbackQuery):

    _, level, lesson = callback.data.split(":")

    await callback.message.edit_text(
        f"🎓 <b>{level}</b>\n"
        f"📖 Dars: <b>{lesson}</b>\n\n"
        "Homework turini tanlang.",
        reply_markup=homework_components_keyboard(
            course_type="online",
            level=level,
            lesson=int(lesson),
        ),
    )

    await callback.answer()


# =========================================================
# COMPONENT
# =========================================================

@router.callback_query(F.data.startswith("hw_online_component:"))
async def online_component(callback: CallbackQuery):

    _, level, lesson, component = callback.data.split(":")

    component_names = {
        "grammar": "📖 Grammatik",
        "reading": "📚 Lesen",
        "listening": "🎧 Hören",
        "writing": "✍️ Schreiben",
        "speaking": "🗣 Sprechen",
        "vocabulary": "📖 Wortschatz",
    }

    await callback.message.edit_text(
        f"🎓 <b>{level}</b>\n"
        f"📖 Dars: <b>{lesson}</b>\n"
        f"{component_names.get(component, component)}\n\n"
        "Quyidagi formatlardan birida homework yuboring:\n\n"
        "• ✍️ Matn\n"
        "• 🖼 Rasm\n"
        "• 📄 PDF/Hujjat\n"
        "• 🎵 Audio\n"
        "• 🎤 Voice",
    )

    await callback.answer()
from aiogram import F
from aiogram.types import (
    Message,
)

from database import homework
from database import homework_files

from states.homework import OnlineHomeworkState


# =========================================================
# TEXT
# =========================================================

@router.message(
    OnlineHomeworkState.waiting_file,
    F.text
)
async def receive_text(
    message: Message,
    state
):
    data = await state.get_data()

    submission = homework.create_submission(
        user_id=message.from_user.id,
        course_type="online",
        level=data["level"],
        lesson=data["lesson"],
        component=data["component"],
    )

    homework_files.add_file(
        message_id=submission["id"],
        sender="student",
        file_type="text",
        text_content=message.text,
    )

    await message.answer(
        "✅ Matn qabul qilindi.\n\n"
        "Yana fayl yuborishingiz yoki "
        "\"📤 Vazifalarni yuborish\" tugmasini bosishingiz mumkin."
    )
# =========================================================
# PHOTO
# =========================================================

@router.message(
    OnlineHomeworkState.waiting_file,
    F.photo
)
async def receive_photo(
    message: Message,
    state
):
    data = await state.get_data()

    submission = homework.create_submission(
        user_id=message.from_user.id,
        course_type="online",
        level=data["level"],
        lesson=data["lesson"],
        component=data["component"],
    )

    homework_files.add_file(
        message_id=submission["id"],
        sender="student",
        file_type="photo",
        telegram_file_id=message.photo[-1].file_id,
    )

    await message.answer(
        "✅ Rasm qabul qilindi."
    )
# =========================================================
# DOCUMENT
# =========================================================

@router.message(
    OnlineHomeworkState.waiting_file,
    F.document
)
async def receive_document(
    message: Message,
    state
):
    data = await state.get_data()

    submission = homework.create_submission(
        user_id=message.from_user.id,
        course_type="online",
        level=data["level"],
        lesson=data["lesson"],
        component=data["component"],
    )

    homework_files.add_file(
        message_id=submission["id"],
        sender="student",
        file_type="document",
        telegram_file_id=message.document.file_id,
    )

    await message.answer(
        "✅ Hujjat qabul qilindi."
    )
# =========================================================
# AUDIO
# =========================================================

@router.message(
    OnlineHomeworkState.waiting_file,
    F.audio
)
async def receive_audio(
    message: Message,
    state
):
    data = await state.get_data()

    submission = homework.create_submission(
        user_id=message.from_user.id,
        course_type="online",
        level=data["level"],
        lesson=data["lesson"],
        component=data["component"],
    )

    homework_files.add_file(
        message_id=submission["id"],
        sender="student",
        file_type="audio",
        telegram_file_id=message.audio.file_id,
    )

    await message.answer(
        "✅ Audio qabul qilindi."
    )
# =========================================================
# VOICE
# =========================================================

@router.message(
    OnlineHomeworkState.waiting_file,
    F.voice
)
async def receive_voice(
    message: Message,
    state
):
    data = await state.get_data()

    submission = homework.create_submission(
        user_id=message.from_user.id,
        course_type="online",
        level=data["level"],
        lesson=data["lesson"],
        component=data["component"],
    )

    homework_files.add_file(
        message_id=submission["id"],
        sender="student",
        file_type="voice",
        telegram_file_id=message.voice.file_id,
    )

    await message.answer(
        "✅ Voice xabar qabul qilindi."
    )
from aiogram import Bot
from aiogram.types import (
    CallbackQuery,
)

from database import homework
from database import homework_files

from states.homework import OnlineHomeworkState

from config import HOMEWORK_ONLINE_CHANNEL


# =========================================================
# SUBMIT HOMEWORK
# =========================================================

@router.callback_query(F.data == "hw_online_submit")
async def submit_homework(
    callback: CallbackQuery,
    state,
    bot: Bot,
):
    data = await state.get_data()

    submissions = homework.get_lesson_submissions(
        callback.from_user.id,
        "online",
        data["level"],
        data["lesson"],
    )

    if not submissions:
        await callback.answer(
            "Avval homework yuboring.",
            show_alert=True,
        )
        return

    for submission in submissions:

        files = homework_files.get_files(
            submission["id"]
        )

        homework.submit_homework(
            submission["id"]
        )

        text = (
            "📚 <b>Yangi Homework</b>\n\n"
            f"👤 User: {callback.from_user.full_name}\n"
            f"🆔 {callback.from_user.id}\n\n"
            f"📖 Level: {submission['level']}\n"
            f"📖 Lesson: {submission['lesson']}\n"
            f"📝 Component: {submission['component']}"
        )

        await bot.send_message(
            HOMEWORK_ONLINE_CHANNEL,
            text,
        )

        for file in files:

            if file["file_type"] == "text":
                await bot.send_message(
                    HOMEWORK_ONLINE_CHANNEL,
                    file["text_content"],
                )

            elif file["file_type"] == "photo":
                await bot.send_photo(
                    HOMEWORK_ONLINE_CHANNEL,
                    file["telegram_file_id"],
                )

            elif file["file_type"] == "document":
                await bot.send_document(
                    HOMEWORK_ONLINE_CHANNEL,
                    file["telegram_file_id"],
                )

            elif file["file_type"] == "audio":
                await bot.send_audio(
                    HOMEWORK_ONLINE_CHANNEL,
                    file["telegram_file_id"],
                )

            elif file["file_type"] == "voice":
                await bot.send_voice(
                    HOMEWORK_ONLINE_CHANNEL,
                    file["telegram_file_id"],
                )

    await state.clear()

    await callback.message.edit_text(
        "✅ Homework muvaffaqiyatli yuborildi.\n\n"
        "Natija tekshirilgandan so'ng sizga xabar beriladi."
    )

    await callback.answer()
# =========================================================
# CANCEL
# =========================================================

@router.callback_query(F.data == "hw_online_cancel")
async def cancel_homework(
    callback: CallbackQuery,
    state,
):
    await state.clear()

    await callback.message.edit_text(
        "❌ Homework bekor qilindi."
    )

    await callback.answer()
# =========================================================
# BACK
# =========================================================

@router.callback_query(F.data == "hw_online_back")
async def back_online(
    callback: CallbackQuery,
):
    await open_levels(callback)