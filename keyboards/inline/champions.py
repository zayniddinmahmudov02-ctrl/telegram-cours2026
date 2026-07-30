from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

# =========================================================
# CHAMPIONS HOME (MONTHLY / WEEKLY)
# =========================================================

def champions_home_keyboard() -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📅 Monthly Champions",
                    callback_data="champions_monthly",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📅 Weekly Champions",
                    callback_data="champions_weekly",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📅 Daily Champions",
                    callback_data="champions_daily",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Reytinglar",
                    callback_data="lb_back",
                ),
            ],
        ]
    )


# =========================================================
# CHAMPIONS YEARS KEYBOARD
# =========================================================

def champions_years_keyboard() -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📁 2026",
                    callback_data="champions_year_2026",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📁 2027",
                    callback_data="champions_year_2027",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📁 2028",
                    callback_data="champions_year_2028",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Champions",
                    callback_data="lb_champions",
                ),
            ],
        ]
    )


# =========================================================
# WEEKLY CHAMPIONS BACK KEYBOARD
# =========================================================

def weekly_champions_back_keyboard() -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Champions",
                    callback_data="lb_champions",
                ),
            ],
        ]
    )