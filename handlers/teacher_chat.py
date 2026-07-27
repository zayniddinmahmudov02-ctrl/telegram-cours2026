from aiogram import Router, F
from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message

from database import teacher_chat

from keyboards.homework import (
    teacher_chat_keyboard,
)

from states.homework import TeacherChatState

router = Router()


# =========================================================
# OPEN TEACHER CHAT
# =========================================================

async def open_teacher(callback: CallbackQuery):

    if not teacher_chat.can_send_today(callback.from_user.id):

        await callback.answer(
            "❌ Siz bugungi 3 ta savol limitingizdan foydalandingiz.",
            show_alert=True,
        )

        return

    await callback.message.edit_text(
        "💬 <b>Kontakt mit Lehrer</b>\n\n"
        "O'qituvchiga savolingizni yuboring.\n\n"
        "Quyidagilarni yuborishingiz mumkin:\n"
        "• ✍️ Matn\n"
        "• 🖼 Rasm\n"
        "• 📄 PDF/Hujjat\n"
        "• 🎵 Audio\n"
        "• 🎤 Voice",
        reply_markup=teacher_chat_keyboard(),
    )

    await callback.answer()

    await callback.message.bot.fsm.get_context(
        bot=callback.bot,
        chat_id=callback.from_user.id,
        user_id=callback.from_user.id,
    ).set_state(
        TeacherChatState.waiting_message
    )
# =========================================================
# TEXT
# =========================================================

@router.message(
    TeacherChatState.waiting_message,
    F.text,
)
async def receive_text(
    message: Message,
    state,
):

    chat = teacher_chat.create_message(
        message.from_user.id
    )

    await state.update_data(
        message_id=chat["id"]
    )

    await message.answer(
        "✅ Xabar qabul qilindi.\n\n"
        "Agar kerak bo'lsa yana fayl yuboring yoki "
        "\"📤 Yuborish\" tugmasini bosing.",
        reply_markup=teacher_chat_keyboard(),
    )
from config import TEACHER_CHAT_CHANNEL_ID
from database import teacher_message_files


# =========================================================
# PHOTO
# =========================================================

@router.message(
    TeacherChatState.waiting_message,
    F.photo,
)
async def receive_photo(
    message: Message,
    state,
):
    data = await state.get_data()

    if "message_id" not in data:
        chat = teacher_chat.create_message(
            message.from_user.id
        )

        await state.update_data(
            message_id=chat["id"]
        )

        data = await state.get_data()

    teacher_message_files.add_file(
        message_id=data["message_id"],
        sender="student",
        file_type="photo",
        telegram_file_id=message.photo[-1].file_id,
    )

    await message.answer(
        "✅ Rasm qo'shildi.\n\n"
        "Yana fayl yuborishingiz yoki "
        "\"📤 Yuborish\" tugmasini bosishingiz mumkin.",
        reply_markup=teacher_chat_keyboard(),
    )


# =========================================================
# DOCUMENT
# =========================================================

@router.message(
    TeacherChatState.waiting_message,
    F.document,
)
async def receive_document(
    message: Message,
    state,
):
    data = await state.get_data()

    if "message_id" not in data:
        chat = teacher_chat.create_message(
            message.from_user.id
        )

        await state.update_data(
            message_id=chat["id"]
        )

        data = await state.get_data()

    teacher_message_files.add_file(
        message_id=data["message_id"],
        sender="student",
        file_type="document",
        telegram_file_id=message.document.file_id,
    )

    await message.answer(
        "✅ Hujjat qo'shildi.",
        reply_markup=teacher_chat_keyboard(),
    )


# =========================================================
# AUDIO
# =========================================================

@router.message(
    TeacherChatState.waiting_message,
    F.audio,
)
async def receive_audio(
    message: Message,
    state,
):
    data = await state.get_data()

    if "message_id" not in data:
        chat = teacher_chat.create_message(
            message.from_user.id
        )

        await state.update_data(
            message_id=chat["id"]
        )

        data = await state.get_data()

    teacher_message_files.add_file(
        message_id=data["message_id"],
        sender="student",
        file_type="audio",
        telegram_file_id=message.audio.file_id,
    )

    await message.answer(
        "✅ Audio qo'shildi.",
        reply_markup=teacher_chat_keyboard(),
    )


# =========================================================
# VOICE
# =========================================================

@router.message(
    TeacherChatState.waiting_message,
    F.voice,
)
async def receive_voice(
    message: Message,
    state,
):
    data = await state.get_data()

    if "message_id" not in data:
        chat = teacher_chat.create_message(
            message.from_user.id
        )

        await state.update_data(
            message_id=chat["id"]
        )

        data = await state.get_data()

    teacher_message_files.add_file(
        message_id=data["message_id"],
        sender="student",
        file_type="voice",
        telegram_file_id=message.voice.file_id,
    )

    await message.answer(
        "✅ Voice xabar qo'shildi.",
        reply_markup=teacher_chat_keyboard(),
    )


# =========================================================
# SUBMIT QUESTION
# =========================================================

@router.callback_query(F.data == "teacher_chat_submit")
async def submit_question(
    callback: CallbackQuery,
    state,
    bot: Bot,
):
    data = await state.get_data()

    if "message_id" not in data:
        await callback.answer(
            "Avval savol yuboring.",
            show_alert=True,
        )
        return

    message_data = teacher_chat.get_message(
        data["message_id"]
    )

    files = teacher_message_files.get_files(
        data["message_id"]
    )

    await bot.send_message(
        TEACHER_CHAT_CHANNEL_ID,
        (
            "💬 <b>Yangi savol</b>\n\n"
            f"👤 {callback.from_user.full_name}\n"
            f"🆔 {callback.from_user.id}\n"
            f"📝 ID: {message_data['id']}"
        ),
    )

    for file in files:

        if file["file_type"] == "text":
            await bot.send_message(
                TEACHER_CHAT_CHANNEL_ID,
                file["text_content"],
            )

        elif file["file_type"] == "photo":
            await bot.send_photo(
                TEACHER_CHAT_CHANNEL_ID,
                file["telegram_file_id"],
            )

        elif file["file_type"] == "document":
            await bot.send_document(
                TEACHER_CHAT_CHANNEL_ID,
                file["telegram_file_id"],
            )

        elif file["file_type"] == "audio":
            await bot.send_audio(
                TEACHER_CHAT_CHANNEL_ID,
                file["telegram_file_id"],
            )

        elif file["file_type"] == "voice":
            await bot.send_voice(
                TEACHER_CHAT_CHANNEL_ID,
                file["telegram_file_id"],
            )

    await callback.message.edit_text(
        "✅ Savolingiz o'qituvchiga yuborildi.\n\n"
        "Javob tayyor bo'lishi bilan sizga yuboriladi."
    )

    await state.clear()

    await callback.answer()


# =========================================================
# CANCEL
# =========================================================

@router.callback_query(F.data == "teacher_chat_cancel")
async def cancel_teacher_chat(
    callback: CallbackQuery,
    state,
):
    await state.clear()

    await callback.message.edit_text(
        "❌ Savol yuborish bekor qilindi."
    )

    await callback.answer()
