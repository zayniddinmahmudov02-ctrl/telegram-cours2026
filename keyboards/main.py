from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from config import ADMIN_IDS

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📚 Artikel Topish"),
            KeyboardButton(text="🎮 So'z O'yini"),
        ],
        [
            KeyboardButton(text="🎥 Video Kurslar"),
        ],
        [
            KeyboardButton(text="🎬 Medien"),
            KeyboardButton(text="📚 Ma'lumotlar"),
        ],
        [
            KeyboardButton(text="📚 Hausaufgaben"),
        ],
        [
            KeyboardButton(text="👤 Mening Profilim"),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Bo'limni tanlang...",
)


# =========================================================
# MAIN MENU (ADMIN-AWARE)
# =========================================================

def main_menu_for(user_id: int) -> ReplyKeyboardMarkup:
    """Same main_menu, with an Admin Panel row for ADMIN_IDS only."""

    if user_id not in ADMIN_IDS:
        return main_menu

    return ReplyKeyboardMarkup(
        keyboard=main_menu.keyboard + [
            [KeyboardButton(text="👨‍💼 Admin Panel")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Bo'limni tanlang...",
    )