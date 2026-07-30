from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
)

# =========================================================
# CERTIFICATE MENU
# =========================================================

certificate_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🏅 A1 W-Zertifikat"),
            KeyboardButton(text="🏅 A2 W-Zertifikat"),
        ],
        [
            KeyboardButton(text="🏅 B1 W-Zertifikat"),
            KeyboardButton(text="🏅 B2 W-Zertifikat"),
        ],
        [
            KeyboardButton(text="🏅 C1 W-Zertifikat"),
        ],
        [
            KeyboardButton(text="🏆 Reytinglar"),
        ],
        [
            KeyboardButton(text="🎮 So'z O'yini"),
            KeyboardButton(text="⬅️ Darajalar"),
        ],
    ],
    resize_keyboard=True,
)

# =========================================================
# CERTIFICATE RESULT
# =========================================================

certificate_result_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📄 Sertifikatni ko'rish"),
        ],
        [
            KeyboardButton(text="📥 PDF yuklab olish"),
        ],
        [
            KeyboardButton(text="🔙 W-Zertifikat"),
        ],
    ],
    resize_keyboard=True,
)