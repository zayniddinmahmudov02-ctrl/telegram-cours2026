from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

video_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎬 Bepul Namuna Darslar")],
        [KeyboardButton(text="🇩🇪 A1 — 50% CHEGIRMA")],
        [KeyboardButton(text="🇩🇪 A2 — 50% CHEGIRMA")],
        [KeyboardButton(text="🇩🇪 B1 — 50% CHEGIRMA")],
        [KeyboardButton(text="🔥 A1-B1 — 50% CHEGIRMA")],
        [KeyboardButton(text="🔥 A1-C1 — 50% CHEGIRMA")],
        [KeyboardButton(text="⬅️ Orqaga")],
    ],
    resize_keyboard=True,
)