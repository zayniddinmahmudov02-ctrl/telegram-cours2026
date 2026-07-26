from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message

from config.settings import (
    HOMEWORK_ONLINE_CHANNEL_ID,
)

from database import (
    homework,
    homework_files,
)

from keyboards.homework import (
    homework_levels_keyboard,
    homework_lessons_keyboard,
    homework_components_keyboard,
    homework_submit_keyboard,
)

from states.homework import (
    OnlineHomeworkState,
)

router = Router()

# =========================================================
# OPEN LEVELS
# =========================================================

async def open_levels(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎓 <b>Online Homework</b>\n\n"
        "Darajani tanlang.",
        reply_markup=homework_levels_keyboard(
            course_type="online"
        ),
    )
    await callback.answer()


# =========================================================
# SELECT LEVEL
# =========================================================

@router.callback_query(F.data.startswith("hw_online_level:"))
async def select_level(callback: CallbackQuery):

    level = callback.data.split(":")[1]

    lesson_counts = {
        "A1": 14,
        "A2": 14,
        "B1": 20,
        "B2": 30,
        "C1": 22,
    }

    await callback.message.edit_text(
        f"🎓 <b>{level}</b>\n\n"
        "Darsni tanlang.",
        reply_markup=homework_lessons_keyboard(
            course_type="online",
            level=level,
            total_lessons=lesson_counts[level],
        ),
    )

    await callback.answer()


# =========================================================
# SELECT LESSON
# =========================================================

@router.callback_query(F.data.startswith("hw_online_lesson:"))
async def select_lesson(callback: CallbackQuery):

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
# SELECT COMPONENT
# =========================================================

@router.callback_query(F.data.startswith("hw_online_component:"))
async def select_component(
    callback: CallbackQuery,
    state: FSMContext,
):

    _, level, lesson, component = callback.data.split(":")

    component_names = {
        "grammar": "📖 Grammatik",
        "reading": "📚 Lesen",
        "listening": "🎧 Hören",
        "writing": "✍️ Schreiben",
        "speaking": "🗣 Sprechen",
        "vocabulary": "📖 Wortschatz",
    }

    await state.clear()

    await state.update_data(
        course_type="online",
        level=level,
        lesson=int(lesson),
        component=component,
    )

    await state.set_state(
        OnlineHomeworkState.waiting_file
    )

    await callback.message.edit_text(
        f"🎓 <b>{level}</b>\n"
        f"📖 Dars: <b>{lesson}</b>\n"
        f"{component_names.get(component, component)}\n\n"
        "📤 Homeworkni yuboring.\n\n"
        "Qo'llab-quvvatlanadigan formatlar:\n"
        "• ✍️ Matn\n"
        "• 🖼 Rasm\n"
        "• 📄 Hujjat (PDF, DOC va boshqalar)\n"
        "• 🎵 Audio\n"
        "• 🎤 Voice\n\n"
        "Bir nechta fayl yuborishingiz mumkin. "
        "Hammasini yuborib bo'lgach, "
        "\"📤 Vazifalarni yuborish\" tugmasini bosing.",
    )

    await callback.answer()
from aiogram import F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database import homework
from database import homework_files

from keyboards.homework import homework_submit_keyboard

from states.homework import OnlineHomeworkState


# =========================================================
# CREATE SUBMISSION
# =========================================================

async def get_submission_id(
    message: Message,
    state: FSMContext,
) -> int:

    data = await state.get_data()

    submission_id = data.get("submission_id")

    if submission_id:
        return submission_id

    submission = homework.create_submission(
        user_id=message.from_user.id,
        course_type=data["course_type"],
        level=data["level"],
        lesson=data["lesson"],
        component=data["component"],
    )

    submission_id = submission["id"]

    await state.update_data(
        submission_id=submission_id
    )

    return submission_id


# =========================================================
# SAVE FILE
# =========================================================

async def save_file(
    message: Message,
    state: FSMContext,
    file_type: str,
    telegram_file_id: str | None = None,
    text_content: str | None = None,
):

    submission_id = await get_submission_id(
        message,
        state,
    )

    homework_files.add_file(
        submission_id=submission_id,
        file_type=file_type,
        telegram_file_id=telegram_file_id,
        text_content=text_content,
    )

    await message.answer(
        "✅ Homework qabul qilindi.\n\n"
        "Yana fayl yuborishingiz mumkin yoki "
        "\"📤 Vazifalarni yuborish\" tugmasini bosing.",
        reply_markup=homework_submit_keyboard(),
    )


# =========================================================
# TEXT
# =========================================================

@router.message(
    OnlineHomeworkState.waiting_file,
    F.text,
)
async def receive_text(
    message: Message,
    state: FSMContext,
):
    await save_file(
        message,
        state,
        file_type="text",
        text_content=message.text,
    )


# =========================================================
# PHOTO
# =========================================================

@router.message(
    OnlineHomeworkState.waiting_file,
    F.photo,
)
async def receive_photo(
    message: Message,
    state: FSMContext,
):
    await save_file(
        message,
        state,
        file_type="photo",
        telegram_file_id=message.photo[-1].file_id,
    )


# =========================================================
# DOCUMENT
# =========================================================

@router.message(
    OnlineHomeworkState.waiting_file,
    F.document,
)
async def receive_document(
    message: Message,
    state: FSMContext,
):
    await save_file(
        message,
        state,
        file_type="document",
        telegram_file_id=message.document.file_id,
    )


# =========================================================
# AUDIO
# =========================================================

@router.message(
    OnlineHomeworkState.waiting_file,
    F.audio,
)
async def receive_audio(
    message: Message,
    state: FSMContext,
):
    await save_file(
        message,
        state,
        file_type="audio",
        telegram_file_id=message.audio.file_id,
    )


# =========================================================
# VOICE
# =========================================================

@router.message(
    OnlineHomeworkState.waiting_file,
    F.voice,
)
async def receive_voice(
    message: Message,
    state: FSMContext,
):
    await save_file(
        message,
        state,
        file_type="voice",
        telegram_file_id=message.voice.file_id,
    )
from aiogram import Bot, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from database import homework
from database import homework_files

from config import HOMEWORK_ONLINE_CHANNEL


# =========================================================
# SUBMIT HOMEWORK
# =========================================================

@router.callback_query(F.data == "hw_online_submit")
async def submit_homework(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
):
    data = await state.get_data()

    submission_id = data.get("submission_id")

    if not submission_id:
        await callback.answer(
            "Avval homework yuboring.",
            show_alert=True,
        )
        return

    submission = homework.get_submission(submission_id)

    if not submission:
        await callback.answer(
            "Homework topilmadi.",
            show_alert=True,
        )
        return

    files = homework_files.get_files(submission_id)

    if not files:
        await callback.answer(
            "Homework fayllari topilmadi.",
            show_alert=True,
        )
        return

    homework.submit_homework(submission_id)

    await bot.send_message(
        HOMEWORK_ONLINE_CHANNEL,
        format_submission_text(
            callback,
            submission,
        ),
    )

    for file in files:
        await send_homework_file(
            bot,
            HOMEWORK_ONLINE_CHANNEL,
            file,
        )

    await state.clear()

    await callback.message.edit_text(
        "✅ Homework muvaffaqiyatli yuborildi.\n\n"
        "O'qituvchi tekshirganidan so'ng sizga natija yuboriladi."
    )

    await callback.answer()
from aiogram import F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext


# =========================================================
# CANCEL HOMEWORK
# =========================================================

@router.callback_query(F.data == "hw_online_cancel")
async def cancel_homework(
    callback: CallbackQuery,
    state: FSMContext,
):
    await state.clear()

    await callback.message.edit_text(
        "❌ Homework bekor qilindi.\n\n"
        "Barcha saqlanmagan ma'lumotlar o'chirildi."
    )

    await callback.answer()


# =========================================================
# BACK TO LEVELS
# =========================================================

@router.callback_query(F.data == "hw_online_back")
async def back_to_levels(
    callback: CallbackQuery,
    state: FSMContext,
):
    await state.clear()

    await open_levels(callback)
from aiogram import Bot


# =========================================================
# COMPONENT NAME
# =========================================================

def component_name(component: str) -> str:
    names = {
        "grammar": "📖 Grammatik",
        "reading": "📚 Lesen",
        "listening": "🎧 Hören",
        "writing": "✍️ Schreiben",
        "speaking": "🗣 Sprechen",
        "vocabulary": "📖 Wortschatz",
    }

    return names.get(component, component)


# =========================================================
# SUBMISSION TEXT
# =========================================================

def format_submission_text(callback, submission) -> str:
    user = callback.from_user

    username = (
        f"@{user.username}"
        if user.username
        else "Mavjud emas"
    )

    return (
        "📨 <b>Yangi Online Homework</b>\n\n"
        f"👤 <b>Talaba:</b> {user.full_name}\n"
        f"🆔 <code>{user.id}</code>\n"
        f"🌐 <b>Username:</b> {username}\n\n"
        f"🎓 <b>Daraja:</b> {submission['level']}\n"
        f"📖 <b>Dars:</b> {submission['lesson']}\n"
        f"{component_name(submission['component'])}\n\n"
        f"🆔 <b>Submission ID:</b> "
        f"<code>{submission['id']}</code>"
    )


# =========================================================
# SEND FILE
# =========================================================

async def send_homework_file(
    bot: Bot,
    chat_id: int | str,
    file: dict,
):

    file_type = file["file_type"]

    if file_type == "text":
        await bot.send_message(
            chat_id,
            file["text_content"],
        )

    elif file_type == "photo":
        await bot.send_photo(
            chat_id,
            file["telegram_file_id"],
        )

    elif file_type == "document":
        await bot.send_document(
            chat_id,
            file["telegram_file_id"],
        )

    elif file_type == "audio":
        await bot.send_audio(
            chat_id,
            file["telegram_file_id"],
        )

    elif file_type == "voice":
        await bot.send_voice(
            chat_id,
            file["telegram_file_id"],
        )