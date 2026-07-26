from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

# =========================================================
# CHAMPIONS YEARS
# =========================================================

def champions_years_keyboard():

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📁 2026",
                    callback_data="champions_year_2026",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📁 2027",
                    callback_data="champions_year_2027",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📁 2028",
                    callback_data="champions_year_2028",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Reytinglar",
                    callback_data="leaderboard",
                )
            ],
        ]
    )

    return keyboard