from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def teacher_chat_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✍️ Xabar yozish",
        callback_data="teacher_chat_write",
    )

    builder.button(
        text="📎 Fayl yuborish",
        callback_data="teacher_chat_file",
    )

    builder.button(
        text="⬅️ Orqaga",
        callback_data="hw_back",
    )

    builder.adjust(1)

    return builder.as_markup()