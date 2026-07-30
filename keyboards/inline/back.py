from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

# =========================================================
# CHAMPIONS BACK KEYBOARD
# =========================================================

def champions_back_keyboard() -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Yillar",
                    callback_data="champions_monthly",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏆 Reytinglar",
                    callback_data="lb_back",
                ),
            ],
        ]
    )