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

# WORTSCHATZ DATA
wortschatz: dict[str, dict] = {}          # normalized word -> row dict
wortschatz_users: dict[int, bool] = {}     # module-local "currently in Wortschatz mode" tracker

# LOAD WORTSCHATZ
def load_wortschatz():
    csv_path = "Wortschatz.csv"
    if not os.path.exists(csv_path):
        logger.warning("Wortschatz.csv not found — Wortschatz feature disabled.")
        return
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    key = row["word"].strip().lower()
                    wortschatz[key] = {k: v.strip() for k, v in row.items()}
                except Exception as e:
                    logger.error(f"Wortschatz row error: {e}")
    except Exception as e:
        logger.error(f"Wortschatz file error: {e}")
    logger.info(f"Wortschatz loaded: {len(wortschatz)} words")


# MENU
wortschatz_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Wortschatz tizimini yopish")]],
    resize_keyboard=True
)


# FORMAT OUTPUT
def format_entry(entry: dict) -> str:
    word = entry["word"]
    translation = entry["translation"]
    level = entry["level"]
    example = entry["example"]
    word_type = entry["type"]

    if word_type == "Nomen":
        return (
            f"🇩🇪 <b>{entry['article']} {word}</b>\n\n"
            f"🇺🇿 <b>{translation}</b>\n\n"
            f"📊 Daraja: <b>{level}</b>\n\n"
            f"🔹 Plural: <b>{entry['plural']}</b>\n\n"
            f"✏️ Beispiel:\n<b>{example}</b>"
        )

    if word_type == "Verb":
        return (
            f"🇩🇪 <b>{word}</b>\n\n"
            f"🇺🇿 <b>{translation}</b>\n\n"
            f"📊 Daraja: <b>{level}</b>\n\n"
            f"🔹 Infinitiv: {word}\n"
            f"🔹 Präteritum: {entry['preteritum']}\n"
            f"🔹 Partizip II: {entry['partizip_ii']}\n\n"
            f"✏️ Beispiel:\n<b>{example}</b>"
        )

    if word_type == "Adjektiv":
        return (
            f"🇩🇪 <b>{word}</b>\n\n"
            f"🇺🇿 <b>{translation}</b>\n\n"
            f"📊 Daraja: <b>{level}</b>\n\n"
            f"🔹 Positiv: {entry['positiv']}\n"
            f"🔹 Komparativ: {entry['komparativ']}\n"
            f"🔹 Superlativ: {entry['superlativ']}\n\n"
            f"✏️ Beispiel:\n<b>{example}</b>"
        )

    return f"🇩🇪 <b>{word}</b>\n\n🇺🇿 <b>{translation}</b>"


# START
@router.message(F.text == "📚 Wortschatz")
async def wortschatz_start(message: Message):
    wortschatz_users[message.from_user.id] = True
    await message.answer(
        "🇩🇪 Nemischa so'zni yuboring:",
        reply_markup=wortschatz_menu
    )


# CLOSE
@router.message(F.text == "❌ Wortschatz tizimini yopish")
async def close_wortschatz_mode(message: Message):
    wortschatz_users.pop(message.from_user.id, None)
    await message.answer("✅ Wortschatz tizimi yopildi.", reply_markup=main_menu)


# SEARCH
@router.message(
    F.text,
    lambda message: message.from_user.id in wortschatz_users
)
async def wortschatz_handler(message: Message):
    word = message.text.lower().strip()
    entry = wortschatz.get(word)
    if entry:
        await message.answer(format_entry(entry), parse_mode="HTML")
    else:
        await message.answer("❌ Bu so'z Wortschatz bazasidan topilmadi.")
