# =========================================================
# ADMIN MENU
# =========================================================

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
)

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📊 Statistika"),
            KeyboardButton(text="👥 Foydalanuvchilar"),
        ],
        [
            KeyboardButton(text="💳 Xaridorlar"),
            KeyboardButton(text="💰 To'lovlar"),
        ],
        [
            KeyboardButton(text="📢 Reklama Yuborish"),
            KeyboardButton(text="📨 Shaxsiy Xabar"),
        ],
        [
            KeyboardButton(text="⚙️ Sozlamalar"),
            KeyboardButton(text="📋 Loglar"),
        ],
        [
            KeyboardButton(text="⬅️ Admin Chiqish"),
        ],
    ],
    resize_keyboard=True,
    selective=True,
)