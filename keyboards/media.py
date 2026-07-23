from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

medien_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 De-Bücher")],
        [KeyboardButton(text="🎵 De-Musik")],
        [KeyboardButton(text="🎬 De-Filme")],
        [KeyboardButton(text="🔍 Qidiruv")],
        [KeyboardButton(text="⬅️ Orqaga")],
    ],
    resize_keyboard=True,
)

films_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🟢 A1-A2 Filmlari")],
        [KeyboardButton(text="🔵 B1-B2 Filmlari")],
        [KeyboardButton(text="🔴 C1 Filmlari")],
        [KeyboardButton(text="🌟 Ommaviy Filmlar")],
        [KeyboardButton(text="⬅️ Medien")],
    ],
    resize_keyboard=True,
)