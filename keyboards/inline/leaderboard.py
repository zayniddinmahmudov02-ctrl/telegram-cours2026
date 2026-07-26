from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

# =========================================================
# LEADERBOARD
# =========================================================

def leaderboard_keyboard():

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📅 Kunlik",
                    callback_data="lb_daily",
                ),
                InlineKeyboardButton(
                    text="📆 Haftalik",
                    callback_data="lb_weekly",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🗓 Oylik",
                    callback_data="lb_monthly",
                ),
                InlineKeyboardButton(
                    text="🌍 Global",
                    callback_data="lb_global",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👑 Champions",
                    callback_data="champions",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="back_main",
                ),
            ],
        ]
    )

    return keyboard