from aiogram import Router, F
from aiogram.types import (
    Message,
)

from database import (
    teacher_chat,
    teacher_message_files,
)

from states.homework import (
    TeacherReplyState,
)

router = Router()
# =========================================================
# START REPLY
# =========================================================

@router.message(F.text.startswith("/reply"))
async def start_reply(
    message: Message,
    state,
):

    if message.chat.type != "channel":
        return

    args = message.text.split()

    if len(args) != 2:

        await message.answer(
            "Foydalanish:\n"
            "/reply MESSAGE_ID"
        )

        return

    message_id = int(args[1])

    teacher_message = teacher_chat.get_message(
        message_id
    )

    if not teacher_message:

        await message.answer(
            "Savol topilmadi."
        )

        return

    await state.set_state(
        TeacherReplyState.waiting_reply
    )

    await state.update_data(
        message_id=message_id,
    )

    await message.answer(
        "Endi javobni yuboring.\n\n"
        "Text, Photo, PDF, Audio yoki Voice yuborishingiz mumkin."
    )
# =========================================================
# TEXT REPLY
# =========================================================

@router.message(
    TeacherReplyState.waiting_reply,
    F.text,
)
async def reply_text(
    message: Message,
    state,
):

    data = await state.get_data()

    teacher_message_files.add_file(
        message_id=data["message_id"],
        sender="teacher",
        file_type="text",
        text_content=message.text,
    )

    await message.answer(
        "✅ Javob saqlandi.\n"
        "Yana fayl yuborishingiz yoki /send yozishingiz mumkin."
    )
# =========================================================
# PHOTO REPLY
# =========================================================

@router.message(
    TeacherReplyState.waiting_reply,
    F.photo,
)
async def reply_photo(
    message: Message,
    state,
):

    data = await state.get_data()

    teacher_message_files.add_file(
        message_id=data["message_id"],
        sender="teacher",
        file_type="photo",
        telegram_file_id=message.photo[-1].file_id,
    )

    await message.answer(
        "✅ Rasm qo'shildi."
    )
# =========================================================
# DOCUMENT REPLY
# =========================================================

@router.message(
    TeacherReplyState.waiting_reply,
    F.document,
)
async def reply_document(
    message: Message,
    state,
):

    data = await state.get_data()

    teacher_message_files.add_file(
        message_id=data["message_id"],
        sender="teacher",
        file_type="document",
        telegram_file_id=message.document.file_id,
    )

    await message.answer(
        "✅ Hujjat qo'shildi."
    )


# =========================================================
# AUDIO REPLY
# =========================================================

@router.message(
    TeacherReplyState.waiting_reply,
    F.audio,
)
async def reply_audio(
    message: Message,
    state,
):

    data = await state.get_data()

    teacher_message_files.add_file(
        message_id=data["message_id"],
        sender="teacher",
        file_type="audio",
        telegram_file_id=message.audio.file_id,
    )

    await message.answer(
        "✅ Audio qo'shildi."
    )


# =========================================================
# VOICE REPLY
# =========================================================

@router.message(
    TeacherReplyState.waiting_reply,
    F.voice,
)
async def reply_voice(
    message: Message,
    state,
):

    data = await state.get_data()

    teacher_message_files.add_file(
        message_id=data["message_id"],
        sender="teacher",
        file_type="voice",
        telegram_file_id=message.voice.file_id,
    )

    await message.answer(
        "✅ Voice qo'shildi."
    )
from config import BOT_USERNAME


# =========================================================
# SEND ANSWER
# =========================================================

@router.message(F.text == "/send")
async def send_reply(
    message: Message,
    state,
    bot: Bot,
):

    data = await state.get_data()

    teacher_message = teacher_chat.get_message(
        data["message_id"]
    )

    if not teacher_message:

        await message.answer(
            "Savol topilmadi."
        )

        return

    files = teacher_message_files.get_teacher_files(
        data["message_id"]
    )

    await bot.send_message(
        teacher_message["user_id"],
        (
            "👨‍🏫 <b>O'qituvchi javobi</b>\n\n"
            "Savolingizga javob tayyorlandi."
        ),
    )

    for file in files:

        if file["file_type"] == "text":

            await bot.send_message(
                teacher_message["user_id"],
                file["text_content"],
            )

        elif file["file_type"] == "photo":

            await bot.send_photo(
                teacher_message["user_id"],
                file["telegram_file_id"],
            )

        elif file["file_type"] == "document":

            await bot.send_document(
                teacher_message["user_id"],
                file["telegram_file_id"],
            )

        elif file["file_type"] == "audio":

            await bot.send_audio(
                teacher_message["user_id"],
                file["telegram_file_id"],
            )

        elif file["file_type"] == "voice":

            await bot.send_voice(
                teacher_message["user_id"],
                file["telegram_file_id"],
            )

    teacher_chat.reply_message(
        message_id=data["message_id"],
        admin_id=message.from_user.id,
        reply_text="Answered",
    )

    await state.clear()

    await message.answer(
        "✅ Javob foydalanuvchiga yuborildi."
    )
# =========================================================
# CANCEL
# =========================================================

@router.message(F.text == "/cancel")
async def cancel_reply(
    message: Message,
    state,
):

    await state.clear()

    await message.answer(
        "❌ Javob bekor qilindi."
    )
