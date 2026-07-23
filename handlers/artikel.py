import csv
import logging
import os

from aiogram import Router, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from keyboards import main_menu

logger = logging.getLogger(__name__)

router = Router()

# =========================
# ARTIKEL DATA
# =========================

artikel: dict[str, str] = {}
artikel_users: dict[int, bool] = {}

# =========================
# LOAD ARTIKEL
# =========================

def load_artikel():

    csv_path = "nouns.csv"

    if not os.path.exists(csv_path):
        logger.warning("nouns.csv not found — Artikel feature disabled.")
        return

    try:

        with open(csv_path, "r", encoding="utf-8") as f:

            reader = csv.DictReader(f)

            for row in reader:

                try:

                    word = row["lemma"].lower().strip()
                    gender = row["genus"].lower().strip()

                    art_map = {
                        "m": "der",
                        "f": "die",
                        "n": "das"
                    }

                    article = art_map.get(gender)

                    if article:
                        artikel[word] = f"{article} {word.capitalize()}"

                except Exception as e:
                    logger.error(f"Artikel row error: {e}")

    except Exception as e:
        logger.error(f"Artikel file error: {e}")

    logger.info(f"Artikel loaded: {len(artikel)} words")
# =========================
# MENU
# =========================

artikel_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="❌ Artikel Tizimini Yopish"
            )
        ]
    ],
    resize_keyboard=True
)

# =========================
# START
# =========================

@router.message(F.text == "📚 Artikel Topish")
async def artikel_start(message: Message):

    artikel_users[message.from_user.id] = True

    await message.answer(

        "🔍 Nemischa so'z yuboring.\n\n"
        "Masalan:\n"
        "Haus\n"
        "Auto\n"
        "Mann\n\n"
        "❌ Chiqish uchun pastdagi tugmani bosing.",

        reply_markup=artikel_menu

    )

# =========================
# CLOSE
# =========================

@router.message(F.text == "❌ Artikel Tizimini Yopish")
async def close_artikel_mode(message: Message):

    artikel_users.pop(
        message.from_user.id,
        None
    )

    await message.answer(
        "✅ Artikel tizimi yopildi.",
        reply_markup=main_menu
    )

# =========================
# SEARCH
# =========================

@router.message(
    F.text,
    lambda message: message.from_user.id in artikel_users
)
async def artikel_handler(message: Message):

    word = message.text.lower().strip()

    result = artikel.get(word)

    await message.answer(

        result

        if result

        else

        "❌ So'z topilmadi.\n\n"
        "Boshqa so'z yuboring."

    )
    