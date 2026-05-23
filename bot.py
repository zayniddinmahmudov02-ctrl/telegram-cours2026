from dotenv import load_dotenv
import os
import asyncio
import csv
import random
import logging
from contextlib import contextmanager

try:
    import psycopg2
    import psycopg2.pool
except ImportError:
    psycopg2 = None

from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    FSInputFile,
)
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================
# ENV
# =========================
load_dotenv()
TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# =========================
# FLASK (keep-alive)
# =========================
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Bot alive"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

Thread(target=run_web, daemon=True).start()

# =========================
# CONFIG
# =========================
ADMIN_ID = 7790766887
CHANNEL_USERNAME = "@vizu_deutsch"

COURSE_LINKS = {
    "🇩🇪 A1":   "https://t.me/+Y0ilZiDqgTJjZjMy",
    "🇩🇪 A2":   "https://t.me/+Co8biP05FtViZGEy",
    "🇩🇪 B1":   "https://t.me/+XcBAw2lLmdlmNDky",
    "🔥 A1-B1": "https://t.me/+ILaI0GhJkS1jYmQy",
    "🔥 A1-C1": "https://t.me/+J7IoPtpXu0s3ZGIy",
}

GROUP_LINKS = {
    "🇩🇪 A1":   "https://t.me/+_76BNOk0NTgxODRi",
    "🇩🇪 A2":   "https://t.me/+syhRWPBkeoxlZjQy",
    "🇩🇪 B1":   "https://t.me/+6vSnu6iFLBI1ZGIy",
    "🔥 A1-B1": "https://t.me/+ILaI0GhJkS1jYmQy",
    "🔥 A1-C1": "https://t.me/+J7IoPtpXu0s3ZGIy",
}

COURSE_INFO = {
    "🇩🇪 A1":   {"lessons": 14,  "price": "100.000 so'm"},
    "🇩🇪 A2":   {"lessons": 14,  "price": "150.000 so'm"},
    "🇩🇪 B1":   {"lessons": 20,  "price": "200.000 so'm"},
    "🔥 A1-B1": {"lessons": 48,  "price": "300.000 so'm"},
    "🔥 A1-C1": {"lessons": 100, "price": "600.000 so'm"},
}
# =========================
# DATABASE
# =========================

import psycopg2
from psycopg2 import pool

db_pool = None

def init_db_pool():
    global db_pool

    db_pool = pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        dsn=DATABASE_URL
    )

@contextmanager
def get_db():

    conn = db_pool.getconn()

    try:
        yield conn
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        db_pool.putconn(conn)

def db_execute(query, params=(), fetchone=False, fetchall=False):

    with get_db() as conn:

        with conn.cursor() as cur:

            cur.execute(query, params)

            if fetchone:
                return cur.fetchone()

            if fetchall:
                return cur.fetchall()

    return None

def init_tables():

    db_execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            full_name TEXT,
            phone TEXT,
            course TEXT,
            approved INTEGER DEFAULT 0,
            score INTEGER DEFAULT 0
        )
    """)

    try:
        db_execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS score INTEGER DEFAULT 0"
        )
    except:
        pass

    try:
        db_execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS course TEXT"
        )
    except:
        pass
# =========================
# BOT
# =========================
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# =========================
# STATES
# =========================
class RegisterState(StatesGroup):
    waiting_for_name  = State()
    waiting_for_phone = State()

class BroadcastState(StatesGroup):
    waiting_for_message = State()

class PersonalMessageState(StatesGroup):
    waiting_for_id   = State()
    waiting_for_text = State()

# =========================
# KEYBOARDS
# =========================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 Artikel Topish")],
        [KeyboardButton(text="🎮 So'z O'yini")],
        [KeyboardButton(text="🎥 Video Kurslar")],
        [KeyboardButton(text="👨‍🏫 Ustoz haqida"), KeyboardButton(text="🏆 Natijalar")],
        [KeyboardButton(text="📞 Admin bilan bog'lanish")],
    ],
    resize_keyboard=True,
)

video_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🇩🇪 A1"), KeyboardButton(text="🇩🇪 A2")],
        [KeyboardButton(text="🇩🇪 B1"), KeyboardButton(text="🇩🇪 B2")],
        [KeyboardButton(text="🇩🇪 C1")],
        [KeyboardButton(text="🔥 A1-B1")],
        [KeyboardButton(text="🔥 B2-C1")],
        [KeyboardButton(text="🔥 A1-C1")],
        [KeyboardButton(text="🎬 Namuna Dars")],
        [KeyboardButton(text="⬅️ Orqaga")],
    ],
    resize_keyboard=True,
)

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="👥 Foydalanuvchilar")],
        [KeyboardButton(text="💳 Xaridorlar")],
        [KeyboardButton(text="📢 Reklama Yuborish")],
        [KeyboardButton(text="📨 Shaxsiy Xabar")],
        [KeyboardButton(text="⬅️ Admin Chiqish")],
    ],
    resize_keyboard=True,
)

word_game_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 A-Blok Teste")],
        [KeyboardButton(text="🏆 Top 100")],
        [KeyboardButton(text="⬅️ Orqaga")],
    ],
    resize_keyboard=True,
)

# =========================
# HELPERS
# =========================
def is_admin(message: Message) -> bool:
    return message.from_user.id == ADMIN_ID

async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status not in ("left", "kicked")
    except Exception:
        return True  # if check fails, don't block the user

# =========================
# ARTIKEL DATA
# =========================
artikel: dict[str, str] = {}
artikel_users: set[int] = set()

def load_artikel():
    csv_path = "nouns.csv"

    if not os.path.exists(csv_path):
        logger.warning("nouns.csv not found — Artikel feature disabled.")
        return

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                word = row["lemma"].lower().strip()
                gender = str(row["genus"]).lower().strip()

                art_map = {
                    "m": "der",
                    "f": "die",
                    "n": "das"
                }

                art = art_map.get(gender)

                if art:
                    artikel[word] = f"{art} {word.capitalize()}"

            except:
                pass

    logger.info(f"Artikel loaded: {len(artikel)} words")
# =========================
# QUIZ DATA
# =========================
QUIZ_QUESTIONS = [
    {"german": "der Apfel",      "correct": "olma",        "wrong": "mashina"},
    {"german": "das Haus",       "correct": "uy",          "wrong": "telefon"},
    {"german": "die Schule",     "correct": "maktab",      "wrong": "oyna"},
    {"german": "der Lehrer",     "correct": "o'qituvchi",  "wrong": "daryo"},
    {"german": "die Mutter",     "correct": "ona",         "wrong": "stul"},
    {"german": "der Vater",      "correct": "ota",         "wrong": "sumka"},
    {"german": "das Buch",       "correct": "kitob",       "wrong": "muz"},
    {"german": "die Tasche",     "correct": "sumka",       "wrong": "oy"},
    {"german": "der Tisch",      "correct": "stol",        "wrong": "telefon"},
    {"german": "das Wasser",     "correct": "suv",         "wrong": "gul"},
    {"german": "die Tür",        "correct": "eshik",       "wrong": "non"},
    {"german": "der Hund",       "correct": "it",          "wrong": "oyna"},
    {"german": "die Katze",      "correct": "mushuk",      "wrong": "qalam"},
    {"german": "das Auto",       "correct": "mashina",     "wrong": "stakan"},
    {"german": "der Freund",     "correct": "do'st",       "wrong": "muzlatgich"},
    {"german": "die Freundin",   "correct": "dugona",      "wrong": "dengiz"},
    {"german": "das Handy",      "correct": "telefon",     "wrong": "stul"},
    {"german": "der Stuhl",      "correct": "stul",        "wrong": "oy"},
    {"german": "die Blume",      "correct": "gul",         "wrong": "maktab"},
    {"german": "das Fenster",    "correct": "oyna",        "wrong": "sumka"},
    {"german": "der Bruder",     "correct": "aka uka",     "wrong": "telefon"},
    {"german": "die Schwester",  "correct": "opa singil",  "wrong": "daryo"},
    {"german": "das Brot",       "correct": "non",         "wrong": "muz"},
    {"german": "der Bleistift",  "correct": "qalam",       "wrong": "stul"},
    {"german": "die Lampe",      "correct": "chiroq",      "wrong": "eshik"},
    {"german": "das Bett",       "correct": "karavot",     "wrong": "sumka"},
    {"german": "der Arzt",       "correct": "shifokor",    "wrong": "oy"},
    {"german": "die Stadt",      "correct": "shahar",      "wrong": "telefon"},
    {"german": "das Land",       "correct": "davlat",      "wrong": "gul"},
    {"german": "der Student",    "correct": "talaba",      "wrong": "mashina"},
    {"german": "die Arbeit",     "correct": "ish",         "wrong": "telefon"},
    {"german": "das Essen",      "correct": "ovqat",       "wrong": "stol"},
    {"german": "der Kaffee",     "correct": "qahva",       "wrong": "sumka"},
    {"german": "die Zeitung",    "correct": "gazeta",      "wrong": "oyna"},
    {"german": "das Kind",       "correct": "bola",        "wrong": "muz"},
    {"german": "der Zug",        "correct": "poyezd",      "wrong": "telefon"},
    {"german": "die Frage",      "correct": "savol",       "wrong": "stul"},
    {"german": "das Bild",       "correct": "rasm",        "wrong": "sumka"},
    {"german": "der Ball",       "correct": "to'p",        "wrong": "oy"},
    {"german": "die Antwort",    "correct": "javob",       "wrong": "gul"},
    {"german": "das Zimmer",     "correct": "xona",        "wrong": "telefon"},
    {"german": "der Computer",   "correct": "kompyuter",   "wrong": "daryo"},
    {"german": "die Musik",      "correct": "musiqa",      "wrong": "stol"},
    {"german": "das Fahrrad",    "correct": "velosiped",   "wrong": "muz"},
    {"german": "der Park",       "correct": "park",        "wrong": "sumka"},
    {"german": "die Familie",    "correct": "oila",        "wrong": "telefon"},
    {"german": "das Spiel",      "correct": "o'yin",       "wrong": "oyna"},
    {"german": "der Abend",      "correct": "kechqurun",   "wrong": "gul"},
    {"german": "die Uhr",        "correct": "soat",        "wrong": "stul"},
    {"german": "das Meer",       "correct": "dengiz",      "wrong": "sumka"},
    {"german": "der Morgen",     "correct": "ertalab",     "wrong": "telefon"},
    {"german": "die Nacht",      "correct": "tun",         "wrong": "muz"},
    {"german": "das Wetter",     "correct": "ob havo",     "wrong": "stol"},
    {"german": "der Sommer",     "correct": "yoz",         "wrong": "daryo"},
    {"german": "die Sonne",      "correct": "quyosh",      "wrong": "sumka"},
    {"german": "das Jahr",       "correct": "yil",         "wrong": "telefon"},
    {"german": "der Winter",     "correct": "qish",        "wrong": "oyna"},
    {"german": "die Woche",      "correct": "hafta",       "wrong": "stul"},
    {"german": "das Wochenende", "correct": "hafta oxiri", "wrong": "muz"},
    {"german": "der Monat",      "correct": "oy",          "wrong": "telefon"},
    {"german": "die Minute",     "correct": "daqiqa",      "wrong": "sumka"},
    {"german": "das Problem",    "correct": "muammo",      "wrong": "stol"},
    {"german": "der Name",       "correct": "ism",         "wrong": "gul"},
    {"german": "die Sprache",    "correct": "til",         "wrong": "oyna"},
    {"german": "das Foto",       "correct": "rasm",        "wrong": "telefon"},
    {"german": "der Kuchen",     "correct": "tort",        "wrong": "muz"},
    {"german": "die Suppe",      "correct": "sho'rva",     "wrong": "stul"},
    {"german": "das Ei",         "correct": "tuxum",       "wrong": "sumka"},
    {"german": "der Fisch",      "correct": "baliq",       "wrong": "telefon"},
    {"german": "die Banane",     "correct": "banan",       "wrong": "oyna"},
    {"german": "das Fleisch",    "correct": "go'sht",      "wrong": "muz"},
    {"german": "der Saft",       "correct": "sharbat",     "wrong": "telefon"},
    {"german": "die Orange",     "correct": "apelsin",     "wrong": "stol"},
    {"german": "das Gemüse",     "correct": "sabzavot",    "wrong": "sumka"},
    {"german": "der Markt",      "correct": "bozor",       "wrong": "gul"},
    {"german": "die Reise",      "correct": "sayohat",     "wrong": "oyna"},
    {"german": "das Ticket",     "correct": "chipta",      "wrong": "telefon"},
    {"german": "der Flughafen",  "correct": "aeroport",    "wrong": "muz"},
    {"german": "die Straße",     "correct": "ko'cha",      "wrong": "stul"},
    {"german": "das Hotel",      "correct": "mehmonxona",  "wrong": "sumka"},
    {"german": "der Chef",       "correct": "rahbar",      "wrong": "telefon"},
    {"german": "die Küche",      "correct": "oshxona",     "wrong": "oyna"},
    {"german": "das Messer",     "correct": "pichoq",      "wrong": "muz"},
    {"german": "der Löffel",     "correct": "qoshiq",      "wrong": "stul"},
    {"german": "die Gabel",      "correct": "sanchqi",     "wrong": "sumka"},
    {"german": "das Glas",       "correct": "stakan",      "wrong": "telefon"},
    {"german": "der Teller",     "correct": "tarelka",     "wrong": "gul"},
    {"german": "die Kleidung",   "correct": "kiyim",       "wrong": "oyna"},
    {"german": "das Hemd",       "correct": "ko'ylak",     "wrong": "muz"},
    {"german": "der Schuh",      "correct": "oyoq kiyim",  "wrong": "telefon"},
    {"german": "die Jacke",      "correct": "kurtka",      "wrong": "sumka"},
    {"german": "das Geld",       "correct": "pul",         "wrong": "oyna"},
    {"german": "der Preis",      "correct": "narx",        "wrong": "telefon"},
    {"german": "die Bank",       "correct": "bank",        "wrong": "stol"},
    {"german": "das Geschäft",   "correct": "do'kon",      "wrong": "muz"},
    {"german": "der Beruf",      "correct": "kasb",        "wrong": "sumka"},
    {"german": "die Universität","correct": "universitet", "wrong": "telefon"},
    {"german": "das Krankenhaus","correct": "kasalxona",   "wrong": "oyna"},
    {"german": "der Urlaub",     "correct": "ta'til",      "wrong": "gul"},
    {"german": "die Nachricht",  "correct": "xabar",       "wrong": "stul"},
]

# Per-user quiz lock: prevents running two quizzes simultaneously
quiz_running: set[int] = set()
quiz_stop_flags = {}
# active quiz questions: question_id -> correct answer
active_questions: dict[str, str] = {}
# answered_users: question_id -> set of user_ids who already answered
answered_users: dict[str, set] = {}

# =========================
# START
# =========================
@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id

    if not await check_subscription(user_id):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="📢 Kanalga A'zo Bo'lish", url="https://t.me/vizu_deutsch")
        ]])
        await message.answer("❌ Botdan foydalanish uchun kanalga a'zo bo'ling.", reply_markup=keyboard)
        return

    db_execute(
        "INSERT INTO users (user_id, approved) VALUES (%s, 0) ON CONFLICT DO NOTHING",
        (user_id,)
    )

    if user_id != ADMIN_ID:
        try:
            await bot.send_message(
                ADMIN_ID,
                f"🔔 Yangi foydalanuvchi!\n\n"
                f"👤 Ism: {message.from_user.full_name}\n"
                f"🆔 ID: {user_id}\n"
                f"Username: @{message.from_user.username}",
            )
        except Exception:
            pass

    await message.answer(
        "🇩🇪 Nemis Tili Video Darslari Botiga Xush Kelibsiz!\n\n"
        "🎉 Hozirda barcha kurslar 50% CHEGIRMADA!",
        reply_markup=main_menu,
    )

# =========================
# USTOZ HAQIDA
# =========================
@dp.message(F.text == "👨‍🏫 Ustoz haqida")
async def teacher_info(message: Message):
    if not os.path.exists("teacher.jpg"):
        await message.answer("Ustoz haqida ma'lumot tez orada qo'shiladi.")
        return
    photo = FSInputFile("teacher.jpg")
    await message.answer_photo(photo=photo)

# =========================
# NATIJALAR
# =========================
@dp.message(F.text == "🏆 Natijalar")
async def results(message: Message):
    await message.answer("🏆 O'quvchilar natijalari:\nhttps://t.me/+o8b2cf3rwAs1MzFi")

# =========================
# ADMIN CONTACT
# =========================
@dp.message(F.text == "📞 Admin bilan bog'lanish")
async def admin_contact(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="👨‍💻 Admin Profil", url="https://t.me/Mahmudow_Z")
    ]])
    await message.answer("📩 Admin bilan bog'lanish uchun tugmani bosing 👇", reply_markup=keyboard)

# =========================
# VIDEO COURSES
# =========================
@dp.message(F.text == "🎥 Video Kurslar")
async def video_courses(message: Message):
    artikel_users.discard(message.from_user.id)
    await message.answer("🎥 Kerakli kursni tanlang:", reply_markup=video_menu)

# =========================
# SAMPLE LESSON
# =========================
@dp.message(F.text == "🎬 Namuna Dars")
async def sample_lesson(message: Message):
    await message.answer("🎬 Namuna Dars:\nhttps://t.me/+yUxu7EOWyd82ODhi")

# =========================
# BACK
# =========================
@dp.message(F.text == "⬅️ Orqaga")
async def go_back(message: Message):
    artikel_users.discard(message.from_user.id)
    await message.answer("🏠 Asosiy Menu", reply_markup=main_menu)

# =========================
# COURSE HANDLER
# =========================
async def send_course_info(message: Message, course: str):
    info = COURSE_INFO[course]
    text = (
        f"🎉 Hozirda barcha kurslar 50% CHEGIRMADA!\n\n"
        f"{course} Video Darslari\n\n"
        f"📚 {info['lessons']} dars\n\n"
        f"🔥 Narx: {info['price']}\n\n"
        f"✅ Grammatika\n✅ Lesen\n✅ Hören\n✅ Schreiben\n✅ Sprechen\n\n"
        f"💳 To'lov:\n9860 3501 4490 7192\n\n"
        f"👤 Zayniddinkhuja Makhmudov\n\n"
        f"📩 To'lovdan keyin chekni shu botga yuboring.\n"
        f"Admin tasdiqlaydi va kurs havolasini yuboradi."
    )
    # store chosen course in DB immediately
    db_execute("UPDATE users SET course = %s WHERE user_id = %s", (course, message.from_user.id))
    await message.answer(text)

UNAVAILABLE_MSG = "⏳ Kurslar hozirda tayyor emas.\nTayyor bo'lishi bilan yuklaymiz."

@dp.message(F.text == "🇩🇪 A1")
async def course_a1(message: Message): await send_course_info(message, "🇩🇪 A1")

@dp.message(F.text == "🇩🇪 A2")
async def course_a2(message: Message): await send_course_info(message, "🇩🇪 A2")

@dp.message(F.text == "🇩🇪 B1")
async def course_b1(message: Message): await send_course_info(message, "🇩🇪 B1")

@dp.message(F.text == "🇩🇪 B2")
async def course_b2(message: Message): await message.answer(UNAVAILABLE_MSG)

@dp.message(F.text == "🇩🇪 C1")
async def course_c1(message: Message): await message.answer(UNAVAILABLE_MSG)

@dp.message(F.text == "🔥 A1-B1")
async def course_a1b1(message: Message): await send_course_info(message, "🔥 A1-B1")

@dp.message(F.text == "🔥 B2-C1")
async def course_b2c1(message: Message): await message.answer(UNAVAILABLE_MSG)

@dp.message(F.text == "🔥 A1-C1")
async def course_a1c1(message: Message): await send_course_info(message, "🔥 A1-C1")

# =========================
# CHECK PHOTO (payment receipt)
# =========================
@dp.message(F.photo)
async def check_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await message.answer("👤 Ism va familiyangizni yuboring:")
    await state.set_state(RegisterState.waiting_for_name)

@dp.message(RegisterState.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon Raqamni Yuborish", request_contact=True)]],
        resize_keyboard=True,
    )
    await message.answer("📱 Telefon raqamingizni yuboring:", reply_markup=keyboard)
    await state.set_state(RegisterState.waiting_for_phone)

@dp.message(RegisterState.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext):
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text.strip()
        if len(phone) < 7:
            await message.answer("❌ Telefon raqam noto'g'ri.\n\nQayta yuboring.")
            return

    data = await state.get_data()
    photo     = data["photo"]
    full_name = data["full_name"]
    user      = message.from_user

    # read course from DB (stored when user clicked course button)
    row = db_execute("SELECT course FROM users WHERE user_id = %s", (user.id,), fetchone=True)
    course = (row[0] or "Kurs tanlanmagan") if row else "Kurs tanlanmagan"

    db_execute(
        "UPDATE users SET full_name = %s, phone = %s WHERE user_id = %s",
        (full_name, phone, user.id),
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Approve", callback_data=f"approve:{user.id}"),
        InlineKeyboardButton(text="❌ Reject",  callback_data=f"reject:{user.id}"),
    ]])

    caption = (
        f"💳 Yangi xaridor!\n\n"
        f"👤 Ism: {full_name}\n"
        f"📱 Telefon: {phone}\n\n"
        f"🆔 ID: {user.id}\n"
        f"📚 Kurs: {course}\n\n"
        f"Username: @{user.username}"
    )

    await bot.send_photo(ADMIN_ID, photo=photo, caption=caption, reply_markup=keyboard)
    await message.answer(
        "✅ Ma'lumotlaringiz adminga yuborildi!\nTasdiqlanishini kuting.",
        reply_markup=main_menu,
    )
    await state.clear()

# =========================
# APPROVE / REJECT
# =========================
@dp.callback_query(F.data.startswith("approve:"))
async def approve_user(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    db_execute("UPDATE users SET approved = 1 WHERE user_id = %s", (user_id,))

    row = db_execute("SELECT course FROM users WHERE user_id = %s", (user_id,), fetchone=True)
    course = row[0] if row else ""

    course_link = COURSE_LINKS.get(course, "https://t.me/vizu_deutsch")
    group_link  = GROUP_LINKS.get(course, "https://t.me/vizu_deutsch")

    await bot.send_message(
        user_id,
        f"✅ To'lovingiz tasdiqlandi!\n\n"
        f"🎥 Kurs kanali:\n{course_link}\n\n"
        f"💬 Savollar guruhi:\n{group_link}\n\n"
        f"📚 Yaxshi o'qish tilaymiz!",
    )
    await callback.message.answer("✅ To'lov tasdiqlandi")
    await callback.answer()

@dp.callback_query(F.data.startswith("reject:"))
async def reject_user(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    await bot.send_message(user_id, "❌ Chekingiz tasdiqlanmadi.\n\nIltimos qayta yuboring.")
    await callback.message.answer("❌ Chek rad qilindi")
    await callback.answer()

# =========================
# WORD GAME MENU
# =========================
@dp.message(F.text == "🎮 So'z O'yini")
async def word_game(message: Message):
    artikel_users.discard(message.from_user.id)
    await message.answer("🎮 Wortspiel — So'z O'yini", reply_markup=word_game_menu)

# =========================
# QUIZ
# =========================

quiz_stop_flags = {}

@dp.message(F.text == "📚 A-Blok Teste")
async def start_quiz(message: Message):

    user_id = message.from_user.id

    if user_id in quiz_running:
        await message.answer("⚠️ Test allaqachon boshlangan.")
        return

    quiz_running.add(user_id)

    try:

        await message.answer(
            "🚀 Test boshlandi!\n\n"
            "⏳ Har savol uchun 10 soniya!"
        )

        quiz_stop_flags[user_id] = False

        questions = random.sample(QUIZ_QUESTIONS, len(QUIZ_QUESTIONS))

        for index, question in enumerate(questions):

            if quiz_stop_flags.get(user_id):
                break

            answers = [question["correct"], question["wrong"]]
            random.shuffle(answers)

            question_id = f"{user_id}_{index}"

            active_questions[question_id] = question["correct"]
            answered_users[question_id] = set()

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"A) {answers[0]}",
                            callback_data=f"quiz:{question_id}:{answers[0]}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=f"B) {answers[1]}",
                            callback_data=f"quiz:{question_id}:{answers[1]}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="⛔ Testni Yakunlash",
                            callback_data=f"stopquiz:{user_id}"
                        )
                    ]
                ]
            )

            sent = await message.answer(
                f"📚 Test {index + 1}/{len(QUIZ_QUESTIONS)}\n\n"
                f"🇩🇪 {question['german']}\n\n"
                f"⏳ 10 soniya qoldi!",
                reply_markup=keyboard
            )

            for sec in range(10, 0, -1):

                if quiz_stop_flags.get(user_id):
                    break

                try:
                    await bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=sent.message_id,
                        text=(
                            f"📚 Test {index + 1}/{len(QUIZ_QUESTIONS)}\n\n"
                            f"🇩🇪 {question['german']}\n\n"
                            f"⏳ {sec} soniya qoldi!"
                        ),
                        reply_markup=keyboard
                    )
                except:
                    pass

                await asyncio.sleep(1)

            active_questions.pop(question_id, None)
            answered_users.pop(question_id, None)

            try:
                await bot.edit_message_reply_markup(
                    chat_id=message.chat.id,
                    message_id=sent.message_id,
                    reply_markup=None
                )
            except:
                pass

            if quiz_stop_flags.get(user_id):
                break

            await message.answer(
                f"⏰ Vaqt tugadi!\n\n"
                f"✅ To'g'ri javob: {question['correct']}"
            )

        row = db_execute(
            "SELECT score FROM users WHERE user_id = %s",
            (user_id,),
            fetchone=True
        )

        total_score = row[0] if row else 0

        if quiz_stop_flags.get(user_id):
            await message.answer(
                f"🏁 Test erta yakunlandi!\n\n"
                f"🏆 Umumiy balingiz: {total_score}"
            )
        else:
            await message.answer(
                f"🏁 Test tugadi!\n\n"
                f"🏆 Umumiy balingiz: {total_score}"
            )

    finally:
        quiz_running.discard(user_id)
        quiz_stop_flags.pop(user_id, None)
@dp.callback_query(F.data.startswith("stopquiz:"))
async def stop_quiz(callback: CallbackQuery):

    user_id = int(callback.data.split(":")[1])

    quiz_stop_flags[user_id] = True

    await callback.answer("⛔ Test yakunlandi!")
# =========================
# QUIZ ANSWER CALLBACK
# =========================
@dp.callback_query(F.data.startswith("quiz:"))
async def quiz_answer(callback: CallbackQuery):
    user_id = callback.from_user.id
    _, question_id, selected = callback.data.split(":", 2)

    if question_id not in active_questions:
        await callback.answer("❌ Savol tugagan.", show_alert=True)
        return

    if user_id in answered_users[question_id]:
        await callback.answer("❌ Siz javob berib bo'ldingiz!", show_alert=True)
        return

    answered_users[question_id].add(user_id)
    correct = active_questions[question_id]

    if selected == correct:
        db_execute("UPDATE users SET score = score + 1 WHERE user_id = %s", (user_id,))
        await callback.answer("✅ To'g'ri!")
    else:
        await callback.answer(f"❌ Noto'g'ri!\n\n✅ {correct}", show_alert=True)

# =========================
# TOP 100
# =========================
@dp.message(F.text == "🏆 Top 100")
async def top_players(message: Message):
    result = db_execute(
        "SELECT COALESCE(full_name, 'Unknown'), score FROM users ORDER BY score DESC LIMIT 100",
        fetchall=True,
    )

    if not result:
        await message.answer("❌ Reyting bo'sh.")
        return

    lines = ["🏆 TOP 100 O'YINCHILAR\n"]
    for i, (name, score) in enumerate(result, 1):
        lines.append(f"{i}. {name} — {score} ball")

    await message.answer("\n".join(lines))

# =========================
# ADMIN PANEL
# =========================
@dp.message(F.text == "/admin")
async def admin_panel(message: Message):
    if not is_admin(message):
        return
    await message.answer("⚙️ Admin Panel", reply_markup=admin_menu)

@dp.message(F.text == "⬅️ Admin Chiqish")
async def admin_exit(message: Message):
    if not is_admin(message):
        return
    await message.answer("🏠 Asosiy Menu", reply_markup=main_menu)

# =========================
# STATISTICS
# =========================
@dp.message(F.text == "📊 Statistika")
async def stats(message: Message):
    if not is_admin(message):
        return

    total = db_execute("SELECT COUNT(*) FROM users", fetchone=True)[0]
    buyers = db_execute("SELECT COUNT(*) FROM users WHERE approved = 1", fetchone=True)[0]
    courses = db_execute(
        "SELECT course, COUNT(*) FROM users WHERE approved = 1 GROUP BY course",
        fetchall=True,
    )

    course_text = ""
    if courses:
        for name, count in courses:
            course_text += f"\n  {name or '—'}: {count} ta"

    await message.answer(
        f"📊 BOT STATISTIKASI\n\n"
        f"👥 Foydalanuvchilar: {total}\n"
        f"💳 Xaridorlar: {buyers}\n\n"
        f"📚 Kurs bo'yicha:{course_text}"
    )

# =========================
# USERS LIST
# =========================
@dp.message(F.text == "👥 Foydalanuvchilar")
async def users_list(message: Message):
    if not is_admin(message):
        return

    result = db_execute("SELECT user_id, full_name, course FROM users", fetchall=True)
    if not result:
        await message.answer("Userlar yo'q")
        return

    lines = []
    for uid, name, course in result:
        lines.append(f"🆔 {uid}\n👤 {name or '—'}\n📚 {course or '—'}\n")

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:4000] + "\n..."

    await message.answer(text)

# =========================
# BUYERS LIST
# =========================
@dp.message(F.text == "💳 Xaridorlar")
async def buyers_list(message: Message):
    if not is_admin(message):
        return

    result = db_execute(
        "SELECT user_id, full_name, phone, course FROM users WHERE approved = 1",
        fetchall=True,
    )
    if not result:
        await message.answer("Xaridorlar yo'q")
        return

    lines = ["💳 Tasdiqlangan xaridorlar:\n"]
    for uid, name, phone, course in result:
        lines.append(f"🆔 {uid}\n👤 {name or '—'}\n📱 {phone or '—'}\n📚 {course or '—'}\n")

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:4000] + "\n..."

    await message.answer(text)

# =========================
# PERSONAL MESSAGE
# =========================
@dp.message(F.text == "📨 Shaxsiy Xabar")
async def personal_message_start(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    await message.answer("🆔 Foydalanuvchi ID sini yuboring:")
    await state.set_state(PersonalMessageState.waiting_for_id)

@dp.message(PersonalMessageState.waiting_for_id)
async def personal_message_id(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam yuboring.")
        return
    await state.update_data(target_id=int(message.text))
    await message.answer("📝 Xabar matnini yuboring:")
    await state.set_state(PersonalMessageState.waiting_for_text)

@dp.message(PersonalMessageState.waiting_for_text)
async def personal_message_send(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    data = await state.get_data()
    target_id = data["target_id"]
    try:
        await bot.send_message(target_id, message.text)
        await message.answer("✅ Xabar yuborildi!")
    except Exception as e:
        await message.answer(f"❌ Xabar yuborilmadi: {e}")
    await state.clear()

# =========================
# BROADCAST
# =========================
@dp.message(F.text == "📢 Reklama Yuborish")
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    await message.answer("📢 Yuboriladigan xabarni kiriting:")
    await state.set_state(BroadcastState.waiting_for_message)

@dp.message(BroadcastState.waiting_for_message)
async def send_broadcast(message: Message, state: FSMContext):
    if not is_admin(message):
        return

    result = db_execute("SELECT user_id FROM users", fetchall=True)
    success = failed = 0

    for (uid,) in result:
        try:
            await bot.send_message(uid, message.text)
            success += 1
            await asyncio.sleep(0.05)  # ~20 msg/sec — within Telegram limits
        except Exception:
            failed += 1

    await message.answer(
        f"✅ Xabar yuborildi!\n\n"
        f"👥 Muvaffaqiyatli: {success}\n"
        f"❌ Yuborilmadi: {failed}"
    )
    await state.clear()

# =========================
# ARTIKEL TOPISH
# =========================
_MENU_BUTTONS = {
    "🎮 So'z O'yini", "🎥 Video Kurslar", "👨‍🏫 Ustoz haqida",
    "🏆 Natijalar", "📞 Admin bilan bog'lanish", "⬅️ Orqaga",
    "🇩🇪 A1", "🇩🇪 A2", "🇩🇪 B1", "🇩🇪 B2", "🇩🇪 C1",
    "🔥 A1-B1", "🔥 B2-C1", "🔥 A1-C1", "🎬 Namuna Dars",
    "/admin", "📊 Statistika", "👥 Foydalanuvchilar",
    "💳 Xaridorlar", "📢 Reklama Yuborish", "📨 Shaxsiy Xabar",
    "⬅️ Admin Chiqish", "📚 A-Blok Teste", "🏆 Top 100",
}

@dp.message(F.text == "📚 Artikel Topish")
async def artikel_start(message: Message):
    artikel_users.add(message.from_user.id)
    await message.answer("📚 Artikelini topmoqchi bo'lgan so'zni yozing.")

@dp.message(F.text)
async def artikel_handler(message: Message):
    user_id = message.from_user.id

    if user_id not in artikel_users:
        return

    if message.text in _MENU_BUTTONS:
        artikel_users.discard(user_id)
        return

    word = message.text.lower().strip()
    result = artikel.get(word)
    await message.answer(result if result else "❌ So'z topilmadi")

# =========================
# RUN
# =========================
async def main():
    init_db_pool()
    init_tables()
    load_artikel()
    logger.info("BOT ISHGA TUSHDI ✅")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())