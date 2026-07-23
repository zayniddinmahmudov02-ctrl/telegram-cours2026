from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

video_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎬 Bepul Namuna Darslar")],
        [KeyboardButton(text="🇩🇪 A1")],
        [KeyboardButton(text="🇩🇪 A2")],
        [KeyboardButton(text="🇩🇪 B1")],
        [KeyboardButton(text="🔥 A1-B1")],
        [KeyboardButton(text="🔥 A1-C1")],
        [KeyboardButton(text="⬅️ Orqaga")],
    ],
    resize_keyboard=True,
)