from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# ==========================
# MAIN MENU
# ==========================

info_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🏫 VIZU-Academy",
                callback_data="info_vizu",
            )
        ],
        [
            InlineKeyboardButton(
                text="👨‍🏫 Zayniddinkhuja Makhmudov",
                url="https://zayniddinkhuja-makhmudov-cv.vercel.app",
            )
        ],
        [
            InlineKeyboardButton(
                text="🌐 Ijtimoiy tarmoqlarimiz",
                callback_data="info_social",
            )
        ],
        [
            InlineKeyboardButton(
                text="💬 Admin bilan bog'lanish",
                callback_data="info_admin",
            )
        ],
        [
            InlineKeyboardButton(
                text="🏆 Natijalar",
                url="https://t.me/vizu_de_results",
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Orqaga",
                callback_data="info_back",
            )
        ],
    ]
)

# ==========================
# BACK BUTTON
# ==========================

back_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⬅️ Ma'lumotlar",
                callback_data="info_menu",
            )
        ]
    ]
)

# ==========================
# SOCIAL
# ==========================

social_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📸 Instagram",
                url="https://www.instagram.com/vizu_deutsch",
            )
        ],
        [
            InlineKeyboardButton(
                text="✈️ Telegram",
                url="https://t.me/vizu_deutsch",
            )
        ],
        [
            InlineKeyboardButton(
                text="▶️ YouTube",
                url="https://www.youtube.com/@vizu_deutsch",
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Ma'lumotlar",
                callback_data="info_menu",
            )
        ],
    ]
)

# ==========================
# ADMIN
# ==========================

admin_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="👤 @Mahmudow_Z",
                url="https://t.me/Mahmudow_Z",
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Ma'lumotlar",
                callback_data="info_menu",
            )
        ],
    ]
)