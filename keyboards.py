from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# =========================================================
# MAIN MENU
# =========================================================

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

# =========================================================
# HOMEWORK
# =========================================================

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

# =========================================================
# VIDEO KURSLAR
# =========================================================

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

# =========================================================
# MEDIEN
# =========================================================

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

# =========================================================
# VIZU CERTIFICATE
# =========================================================

vizu_certificate_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏅 VIZU-A1")],
        [KeyboardButton(text="🏅 VIZU-A2")],
        [KeyboardButton(text="🏅 VIZU-B1")],
        [KeyboardButton(text="🏅 VIZU-B2")],
        [KeyboardButton(text="🏅 VIZU-C1")],
        [KeyboardButton(text="⬅️ Orqaga")],
    ],
    resize_keyboard=True,
)

# =========================================================
# PROFILE
# =========================================================

def profile_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏅 Mening Sertifikatlarim")],
            [KeyboardButton(text="✏️ Ism Familiyani o'zgartirish")],
            [KeyboardButton(text="⬅️ Orqaga")],
        ],
        resize_keyboard=True,
    )

# =========================================================
# INFORMATION
# =========================================================

info_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👨‍🏫 Ustoz haqida")],
        [KeyboardButton(text="🏆 Natijalar")],
        [KeyboardButton(text="📞 Admin bilan bog'lanish")],
        [KeyboardButton(text="⬅️ Orqaga")],
    ],
    resize_keyboard=True,
)

# =========================================================
# ADMIN
# =========================================================

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="📢 Reklama Yuborish")],
        [KeyboardButton(text="📨 Shaxsiy Xabar")],
        [KeyboardButton(text="⬅️ Admin Chiqish")],
    ],
    resize_keyboard=True,
)

# =========================================================
# DYNAMIC KEYBOARDS
# =========================================================

LESSON_COUNTS = {
    "A1": 14,
    "A2": 14,
    "B1": 20,
    "B2": 30,
    "C1": 22,
}


def build_lesson_menu(level: str):

    total = LESSON_COUNTS[level]

    keyboard = []
    row = []

    for i in range(1, total + 1):

        row.append(KeyboardButton(text=str(i)))

        if len(row) == 5:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([KeyboardButton(text="⬅️ Orqaga")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def build_speaking_lesson_menu():

    keyboard = []
    row = []

    for i in range(1, 21):

        row.append(KeyboardButton(text=str(i)))

        if len(row) == 5:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([KeyboardButton(text="⬅️ Orqaga")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )