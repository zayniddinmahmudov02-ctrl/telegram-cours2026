from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from config import CHANNEL_USERNAME


def subscription_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Kanalga qo'shilish",
                    url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Tekshirish",
                    callback_data="check_sub",
                )
            ],
        ]
    )
