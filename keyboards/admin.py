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
            KeyboardButton(text="🏅 Certificates"),
        ],
        [
            KeyboardButton(text="📋 Hausaufgaben Admin"),
        ],
        [
            KeyboardButton(text="⬅️ Admin Chiqish"),
        ],
    ],
    resize_keyboard=True,
    selective=True,
)

# =========================================================
# USERS SUBMENU
# =========================================================

users_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="✉️ Xabar Yuborish"),
        ],
        [
            KeyboardButton(text="⬅️ Admin Panel"),
        ],
    ],
    resize_keyboard=True,
    selective=True,
)