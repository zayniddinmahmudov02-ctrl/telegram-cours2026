from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

# =========================================================
# BACK
# =========================================================

def champions_back_keyboard():

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Yillar",
                    callback_data="champions",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏆 Reytinglar",
                    callback_data="leaderboard",
                )
            ],
        ]
    )

    return keyboard