from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def profile_keyboard():

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏅 Mening Sertifikatlarim")],
            [KeyboardButton(text="✏️ Ism Familiyani o'zgartirish")],
            [KeyboardButton(text="⬅️ Orqaga")],
        ],
        resize_keyboard=True,
    )