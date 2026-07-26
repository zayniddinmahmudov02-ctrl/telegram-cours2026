from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message

from config.settings import (
    HOMEWORK_SPEAKING_CHANNEL_ID,
)

from database import (
    homework,
    homework_files,
)

from keyboards.homework import (
    homework_levels_keyboard,
    homework_lessons_keyboard,
    speaking_task_keyboard,
)

from states.homework import (
    SpeakingHomeworkState,
)

router = Router()
# =========================================================
# OPEN LEVELS
# =========================================================

async def open_levels(callback: CallbackQuery):

    await callback.message.edit_text(
        "🗣 <b>Speaking Homework</b>\n\n"
        "Darajani tanlang.",
        reply_markup=homework_levels_keyboard(
            course_type="speaking"
        ),
    )

    await callback.answer()
# =========================================================
# LEVEL
# =========================================================

@router.callback_query(F.data.startswith("hw_speaking_level:"))
async def speaking_level(callback: CallbackQuery):

    level = callback.data.split(":")[1]

    lesson_counts = {
        "A1": 14,
        "A2": 14,
        "B1": 20,
        "B2": 30,
        "C1": 22,
    }

    await callback.message.edit_text(
        f"🗣 <b>{level}</b>\n\n"
        "Lessonni tanlang.",
        reply_markup=homework_lessons_keyboard(
            course_type="speaking",
            level=level,
            total_lessons=lesson_counts[level],
        ),
    )

    await callback.answer()
# =========================================================
# LESSON
# =========================================================

@router.callback_query(F.data.startswith("hw_speaking_lesson:"))
async def speaking_lesson(
    callback: CallbackQuery,
    state,
):

    _, level, lesson = callback.data.split(":")

    await state.set_state(
        SpeakingHomeworkState.waiting_task
    )

    await state.update_data(
        level=level,
        lesson=int(lesson),
    )

    await callback.message.edit_text(
        f"🗣 <b>{level}</b>\n"
        f"📖 Lesson {lesson}\n\n"
        "Task raqamini kiriting.\n\n"
        "Masalan:\n"
        "<code>1</code>",
    )

    await callback.answer()
# =========================================================
# TASK NUMBER
# =========================================================

@router.message(
    SpeakingHomeworkState.waiting_task,
    F.text,
)
async def speaking_task(
    message: Message,
    state,
):

    if not message.text.isdigit():

        await message.answer(
            "Task raqamini kiriting."
        )

        return

    task_number = int(message.text)

    data = await state.get_data()

    await state.set_state(
        SpeakingHomeworkState.waiting_file
    )

    await state.update_data(
        task_number=task_number,
    )

    await message.answer(
        f"🗣 Task {task_number}\n\n"
        "Homework yuboring.",
        reply_markup=speaking_task_keyboard(),
    )
# =========================================================
# TEXT
# =========================================================

@router.message(
    SpeakingHomeworkState.waiting_file,
    F.text,
)
async def speaking_text(
    message: Message,
    state,
):
    data = await state.get_data()

    submission = homework.create_submission(
        user_id=message.from_user.id,
        course_type="speaking",
        level=data["level"],
        lesson=data["lesson"],
        component="speaking",
        task_number=data["task_number"],
    )

    homework_files.add_file(
        message_id=submission["id"],
        sender="student",
        file_type="text",
        text_content=message.text,
    )

    await message.answer(
        "✅ Javob saqlandi.",
        reply_markup=speaking_task_keyboard(),
    )
# =========================================================
# PHOTO
# =========================================================

@router.message(
    SpeakingHomeworkState.waiting_file,
    F.photo,
)
async def speaking_photo(
    message: Message,
    state,
):
    data = await state.get_data()

    submission = homework.create_submission(
        user_id=message.from_user.id,
        course_type="speaking",
        level=data["level"],
        lesson=data["lesson"],
        component="speaking",
        task_number=data["task_number"],
    )

    homework_files.add_file(
        message_id=submission["id"],
        sender="student",
        file_type="photo",
        telegram_file_id=message.photo[-1].file_id,
    )

    await message.answer(
        "✅ Rasm saqlandi.",
        reply_markup=speaking_task_keyboard(),
    )
# =========================================================
# DOCUMENT
# =========================================================

@router.message(
    SpeakingHomeworkState.waiting_file,
    F.document,
)
async def speaking_document(
    message: Message,
    state,
):
    data = await state.get_data()

    submission = homework.create_submission(
        user_id=message.from_user.id,
        course_type="speaking",
        level=data["level"],
        lesson=data["lesson"],
        component="speaking",
        task_number=data["task_number"],
    )

    homework_files.add_file(
        message_id=submission["id"],
        sender="student",
        file_type="document",
        telegram_file_id=message.document.file_id,
    )

    await message.answer(
        "✅ Hujjat saqlandi.",
        reply_markup=speaking_task_keyboard(),
    )
# =========================================================
# AUDIO
# =========================================================

@router.message(
    SpeakingHomeworkState.waiting_file,
    F.audio,
)
async def speaking_audio(
    message: Message,
    state,
):
    data = await state.get_data()

    submission = homework.create_submission(
        user_id=message.from_user.id,
        course_type="speaking",
        level=data["level"],
        lesson=data["lesson"],
        component="speaking",
        task_number=data["task_number"],
    )

    homework_files.add_file(
        message_id=submission["id"],
        sender="student",
        file_type="audio",
        telegram_file_id=message.audio.file_id,
    )

    await message.answer(
        "✅ Audio saqlandi.",
        reply_markup=speaking_task_keyboard(),
    )
# =========================================================
# VOICE
# =========================================================

@router.message(
    SpeakingHomeworkState.waiting_file,
    F.voice,
)
async def speaking_voice(
    message: Message,
    state,
):
    data = await state.get_data()

    submission = homework.create_submission(
        user_id=message.from_user.id,
        course_type="speaking",
        level=data["level"],
        lesson=data["lesson"],
        component="speaking",
        task_number=data["task_number"],
    )

    homework_files.add_file(
        message_id=submission["id"],
        sender="student",
        file_type="voice",
        telegram_file_id=message.voice.file_id,
    )

    await message.answer(
        "✅ Voice saqlandi.",
        reply_markup=speaking_task_keyboard(),
    )
# =========================================================
# NEXT TASK
# =========================================================

@router.callback_query(F.data == "hw_speaking_next")
async def next_task(
    callback: CallbackQuery,
    state,
):
    await state.set_state(
        SpeakingHomeworkState.waiting_task
    )

    await callback.message.edit_text(
        "🔢 Keyingi task raqamini kiriting."
    )

    await callback.answer()
# =========================================================
# FINISH LESSON
# =========================================================

@router.callback_query(F.data == "hw_speaking_finish")
async def finish_lesson(
    callback: CallbackQuery,
    state,
    bot: Bot,
):
    data = await state.get_data()

    submissions = homework.get_lesson_submissions(
        callback.from_user.id,
        "speaking",
        data["level"],
        data["lesson"],
    )

    if not submissions:

        await callback.answer(
            "Homework topilmadi.",
            show_alert=True,
        )

        return

    await bot.send_message(
        HOMEWORK_SPEAKING_CHANNEL_ID,
        (
            "🗣 <b>Speaking Homework</b>\n\n"
            f"👤 {callback.from_user.full_name}\n"
            f"🆔 {callback.from_user.id}\n\n"
            f"📖 Level: {data['level']}\n"
            f"📚 Lesson: {data['lesson']}"
        ),
    )

    for submission in submissions:

        homework.submit_homework(
            submission["id"]
        )

        await bot.send_message(
            HOMEWORK_SPEAKING_CHANNEL_ID,
            (
                f"🎯 Task {submission['task_number']}"
            ),
        )

        files = homework_files.get_files(
            submission["id"]
        )

        for file in files:

            if file["file_type"] == "text":

                await bot.send_message(
                    HOMEWORK_SPEAKING_CHANNEL_ID,
                    file["text_content"],
                )

            elif file["file_type"] == "photo":

                await bot.send_photo(
                    HOMEWORK_SPEAKING_CHANNEL_ID,
                    file["telegram_file_id"],
                )

            elif file["file_type"] == "document":

                await bot.send_document(
                    HOMEWORK_SPEAKING_CHANNEL_ID,
                    file["telegram_file_id"],
                )

            elif file["file_type"] == "audio":

                await bot.send_audio(
                    HOMEWORK_SPEAKING_CHANNEL_ID,
                    file["telegram_file_id"],
                )

            elif file["file_type"] == "voice":

                await bot.send_voice(
                    HOMEWORK_SPEAKING_CHANNEL_ID,
                    file["telegram_file_id"],
                )

    await state.clear()

    await callback.message.edit_text(
        "✅ Speaking homework muvaffaqiyatli yuborildi.\n\n"
        "Natija tekshirilgach sizga yuboriladi."
    )

    await callback.answer()
# =========================================================
# CANCEL
# =========================================================

@router.callback_query(F.data == "hw_speaking_cancel")
async def cancel(
    callback: CallbackQuery,
    state,
):
    await state.clear()

    await callback.message.edit_text(
        "❌ Speaking homework bekor qilindi."
    )

    await callback.answer()
# =========================================================
# BACK
# =========================================================

@router.callback_query(F.data == "hw_speaking_back")
async def back(
    callback: CallbackQuery,
):
    await open_levels(callback)
