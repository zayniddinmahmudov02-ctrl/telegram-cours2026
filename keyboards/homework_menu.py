from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def homework_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text="🌐 Online Homework",
        callback_data="hw_online",
    )

    builder.button(
        text="🎥 Video Homework",
        callback_data="hw_video",
    )

    builder.button(
        text="🎤 Speaking Homework",
        callback_data="hw_speaking",
    )

    builder.button(
        text="👨‍🏫 Teacher Chat",
        callback_data="hw_teacher",
    )

    builder.button(
        text="⬅️ Orqaga",
        callback_data="hw_back",
    )

    builder.adjust(1)

    return builder.as_markup()