from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📚 Artikel Topish"),
            KeyboardButton(text="🎮 So'z O'yini"),
        ],
        [
            KeyboardButton(text="🎥 Video Kurslar"),
            KeyboardButton(text="📝 Homework"),
        ],
        [
            KeyboardButton(text="🎬 Medien"),
            KeyboardButton(text="🏅 VIZU-Zertifikat"),
        ],
        [
            KeyboardButton(text="📚 Ma'lumotlar"),
            KeyboardButton(text="👤 Mening Profilim"),
        ],
    ],
    resize_keyboard=True,
)