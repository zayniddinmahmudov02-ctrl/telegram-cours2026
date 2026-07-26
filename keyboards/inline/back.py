from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

# =========================================================
# BACK
# =========================================================

def champions_back_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Yillar",
                    callback_data="lb_champions",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏆 Reytinglar",
                    callback_data="lb_back",
                )
            ],
        ]
    )