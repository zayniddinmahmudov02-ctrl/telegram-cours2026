from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

homework_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🎓 Online Kurs"),
            KeyboardButton(text="🎥 Video Kurs"),
        ],
        [
            KeyboardButton(text="🗣 Speaking Kurs"),
        ],
        [
            KeyboardButton(text="⬅️ Orqaga"),
        ],
    ],
    resize_keyboard=True,
)

homework_category_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📝 Vazifa yuborish"),
        ],
        [
            KeyboardButton(text="💬 Kontakt mit Lehrer"),
        ],
        [
            KeyboardButton(text="⬅️ Orqaga"),
        ],
    ],
    resize_keyboard=True,
)

homework_level_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🟢 A1"),
            KeyboardButton(text="🔵 A2"),
        ],
        [
            KeyboardButton(text="🟡 B1"),
            KeyboardButton(text="🟠 B2"),
        ],
        [
            KeyboardButton(text="🔴 C1"),
        ],
        [
            KeyboardButton(text="⬅️ Orqaga"),
        ],
    ],
    resize_keyboard=True,
)

kompetenz_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📖 Lesen"),
            KeyboardButton(text="🎧 Hören"),
        ],
        [
            KeyboardButton(text="✍ Schreiben"),
            KeyboardButton(text="🗣 Sprechen"),
        ],
        [
            KeyboardButton(text="📚 Wortschatz"),
        ],
        [
            KeyboardButton(text="⬅️ Orqaga"),
        ],
    ],
    resize_keyboard=True,
)