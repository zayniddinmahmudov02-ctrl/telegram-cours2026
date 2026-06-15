# =========================================================
# STANDARD LIBRARY IMPORTS
# =========================================================
import os
import csv
import uuid
import random
import logging
import asyncio
import random
import hashlib
import hmac

logger = logging.getLogger(__name__)
from datetime import datetime, timedelta, date
from contextlib import contextmanager
from threading import Thread
from typing import (
    Optional,
    Callable,
    Dict,
    Any,
)

# =========================================================
# WEB & ENVIRONMENT
# =========================================================
from flask import Flask
from dotenv import load_dotenv

# =========================================================
# DATABASE
# =========================================================
import psycopg2
from psycopg2 import pool

# =========================================================
# IMAGE PROCESSING
# =========================================================
from PIL import (
    Image,
    ImageDraw,
    ImageFont
)

# =========================================================
# REPORTLAB
# =========================================================
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet

from reportlab.pdfgen import canvas

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage
)

# =========================================================
# AIOGRAM
# =========================================================
from aiogram import (
    Bot,
    Dispatcher,
    F,
    BaseMiddleware
)

from aiogram.types import (
    Message,
    CallbackQuery,
    FSInputFile,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from aiogram.filters import (
    CommandStart,
    Command,
    StateFilter
)

from aiogram.fsm.storage.memory import (
    MemoryStorage
)

from aiogram.fsm.state import (
    State,
    StatesGroup
)

from aiogram.fsm.context import (
    FSMContext
)

from aiogram.utils.keyboard import (
    InlineKeyboardBuilder
)
from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable
# =========================================================
# LOGGING
# =========================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================================================
# CONFIGURATION
# =========================================================
GENERATED_DIR = "generated"
CERTIFICATE_DIR = "certificates"
TOTAL_WORDS = 5555

# =========================================================
# ENV VARIABLES
# =========================================================
load_dotenv()

TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
ADMIN_CHANNEL_ID = int(os.getenv("ADMIN_CHANNEL_ID", "0"))

CHANNEL_USERNAME = "@vizu_deutsch"
# =========================================================
# RATING CHANNELS
# =========================================================

SPRECHEN_CHANNEL_ID = -1003858674950

SCHREIBEN_CHANNEL_ID = -1003895627242
# =========================================================
# SECURITY CHECK
# =========================================================
if not TOKEN:
    raise ValueError("TOKEN topilmadi")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL topilmadi")
# =========================================================
# COURSE LINKS
# =========================================================
COURSE_LINKS = {
    "🇩🇪 A1": "https://t.me/+Y0ilZiDqgTJjZjMy",
    "🇩🇪 A2": "https://t.me/+Co8biP05FtViZGEy",
    "🇩🇪 B1": "https://t.me/+XcBAw2lLmdlmNDky",
    "🔥 A1-B1": "https://t.me/+ILaI0GhJkS1jYmQy",
    "🔥 A1-C1": "https://t.me/+9sT2uj8rbHM1YTNi",
}

# =========================================================
# GROUP LINKS
# =========================================================
GROUP_LINKS = {
    "🇩🇪 A1": "https://t.me/+_76BNOk0NTgxODRi",
    "🇩🇪 A2": "https://t.me/+syhRWPBkeoxlZjQy",
    "🇩🇪 B1": "https://t.me/+6vSnu6iFLBI1ZGIy",
    "🔥 A1-B1": "https://t.me/+ILaI0GhJkS1jYmQy",
    "🔥 A1-C1": "https://t.me/+pW308gWaYUwwNmY6",
}

COURSE_INFO = {
    "🇩🇪 A1": {
        "lessons": 14,
        "old_price": "200.000 so'm",
        "price": "50.000 so'm"
    },
    "🇩🇪 A2": {
        "lessons": 14,
        "old_price": "300.000 so'm",
        "price": "100.000 so'm"
    },
    "🇩🇪 B1": {
        "lessons": 20,
        "old_price": "400.000 so'm",
        "price": "100.000 so'm"
    },
    "🔥 A1-B1": {
        "lessons": 48,
        "old_price": "600.000 so'm",
        "price": "200.000 so'm"
    },
    "🔥 A1-C1": {
        "lessons": 100,
        "old_price": "1.200.000 so'm",
        "price": "400.000 so'm"
    },
}

# =========================================================
# GLOBALS
# =========================================================

QUIZ_DATA = {}
quiz_running = set()
quiz_sessions = {}
active_questions = {}
active_lessons = {}
answered_users = {}
approved_users = set()
artikel_data = {}
admin_sessions = {}
last_daily_reset = None
vizu_lesen_questions = []
vizu_lesen_progress = {}
vizu_horen_questions = []
vizu_horen_progress = {}
vizu_sprechen_progress = {}
vizu_mock_deadlines = {}
# =========================================================
# ACTIVE LEVELS
# =========================================================

selected_levels = {}
# =========================================================
# GRAMMATIK PROGRESS
# =========================================================

grammatik_progress = {}
# =========================================================
# LESEN PROGRESS
# =========================================================

lesen_progress = {}
# =========================================================
# HOREN PROGRESS
# =========================================================

horen_progress = {}

LESSON_QUIZ_DATA = {}
lesson_quiz_sessions = {}
lesson_active_questions = {}
lesson_answered_users = {}

# =========================================================
# DATABASE POOL MANAGEMENT
# =========================================================
db_pool = None

def init_db_pool():
    global db_pool
    try:
        if db_pool:
            try:
                db_pool.closeall()
            except Exception:
                pass

        db_pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=20,
            dsn=DATABASE_URL
        )
        logger.info("Database connected ✅")
    except Exception as e:
        logger.error(f"Database pool error: {e}")
        raise

@contextmanager
def get_db():
    global db_pool
    conn = None
    try:
        if not db_pool:
            init_db_pool()

        try:
            conn = db_pool.getconn()
        except Exception as e:
            logger.error(f"Reconnect DB: {e}")
            init_db_pool()
            conn = db_pool.getconn()

        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        logger.error(f"DB transaction error: {e}")
        raise
    finally:
        if conn and db_pool:
            try:
                db_pool.putconn(conn)
            except Exception as e:
                logger.error(f"Return connection error: {e}")

def db_execute(query, params=(), fetchone=False, fetchall=False):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                if fetchone:
                    return cur.fetchone()
                if fetchall:
                    return cur.fetchall()
        return None
    except Exception as e:
        logger.error(f"DB execute error: {e}")
        return None
# =========================================================
# INIT TABLES
# =========================================================

def init_tables():

    # USERS TABLE
    db_execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            full_name TEXT,
            phone TEXT,
            course TEXT,
            approved INTEGER DEFAULT 0,

            score INTEGER DEFAULT 0,
            total_score INTEGER DEFAULT 0,
            daily_score INTEGER DEFAULT 0,

            unlocked_level TEXT DEFAULT 'A1',
            last_daily_reset DATE,

            vizu_a1_access INTEGER DEFAULT 0,
            vizu_a2_access INTEGER DEFAULT 0,
            vizu_b1_access INTEGER DEFAULT 0,
            vizu_b2_access INTEGER DEFAULT 0,
            vizu_c1_access INTEGER DEFAULT 0
        )
    """)
# =========================================================
# W CERTIFICATES TABLE
# =========================================================

def init_w_certificates_table():
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS w_certificates (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            level TEXT NOT NULL,
            rank TEXT NOT NULL,
            cert_id TEXT UNIQUE NOT NULL,
            percent REAL NOT NULL,
            score INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE (user_id, level)
        )
        """
    )

    # LESSON PROGRESS
    db_execute("""
        CREATE TABLE IF NOT EXISTS lesson_progress (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            level TEXT NOT NULL,
            lesson INTEGER NOT NULL,
            completed BOOLEAN DEFAULT FALSE,
            completed_at TIMESTAMP DEFAULT NOW(),
            UNIQUE (user_id, level, lesson)
        )
    """)

    # ACTIVE LESSONS
    db_execute("""
        CREATE TABLE IF NOT EXISTS active_lessons (
            user_id BIGINT PRIMARY KEY,
            level TEXT NOT NULL,
            lesson INTEGER NOT NULL,
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # LESSON TASK PROGRESS
    db_execute("""
        CREATE TABLE IF NOT EXISTS lesson_task_progress (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            level TEXT NOT NULL,
            lesson INTEGER NOT NULL,
            task_name TEXT NOT NULL,
            completed BOOLEAN DEFAULT FALSE,
            completed_at TIMESTAMP DEFAULT NOW(),
            UNIQUE (user_id, level, lesson, task_name)
        )
    """)
# =========================================================
# LESSON SCORES
# =========================================================

db_execute("""
    CREATE TABLE IF NOT EXISTS lesson_scores (
        id SERIAL PRIMARY KEY,

        user_id BIGINT NOT NULL,

        level TEXT NOT NULL,

        lesson INTEGER NOT NULL,

        task_name TEXT NOT NULL,

        score INTEGER DEFAULT 0,

        rated_by BIGINT,

        rated_at TIMESTAMP DEFAULT NOW(),

        UNIQUE (
            user_id,
            level,
            lesson,
            task_name
        )
    )
""")
# LEVEL EXAMS
db_execute("""
    CREATE TABLE IF NOT EXISTS level_exams (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        level TEXT NOT NULL,
        score INTEGER DEFAULT 0,
        final_exam_passed BOOLEAN DEFAULT FALSE,
        passed_at TIMESTAMP DEFAULT NOW(),
        UNIQUE (user_id, level)
    )
""")
# LESSON ANSWERS
db_execute("""
    CREATE TABLE IF NOT EXISTS lesson_answers (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        level TEXT NOT NULL,
        lesson INTEGER NOT NULL,
        task_type TEXT,
        answer_text TEXT,
        answer_file TEXT,
        checked BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT NOW()
    )
""")

# QUIZ PROGRESS
db_execute("""
    CREATE TABLE IF NOT EXISTS quiz_progress (
        user_id BIGINT NOT NULL,
        level TEXT NOT NULL,
        block_number INTEGER NOT NULL,
        best_score INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, level, block_number)
    )
""")
# =========================================================
# VIZU ATTEMPTS TABLE
# =========================================================

def init_vizu_attempts_table():

    db_execute("""
        CREATE TABLE IF NOT EXISTS vizu_attempts (

            id SERIAL PRIMARY KEY,

            user_id BIGINT NOT NULL,

            level TEXT NOT NULL,

            attempted_at TIMESTAMP DEFAULT NOW()

        )
    """)

    logger.info(
        "VIZU ATTEMPTS TABLE READY ✅"
    )
    # VIZU CERTIFICATE REQUESTS
    db_execute("""
        CREATE TABLE IF NOT EXISTS vizu_requests (
            id SERIAL PRIMARY KEY,

            user_id BIGINT NOT NULL,
            level TEXT NOT NULL,

            status TEXT DEFAULT 'pending',

            approved_by BIGINT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
# =========================================================
# VIZU LESEN RESULTS TABLE
# =========================================================

def init_vizu_lesen_results_table():

    db_execute("""
        CREATE TABLE IF NOT EXISTS vizu_lesen_results (

            user_id BIGINT PRIMARY KEY,

            score INTEGER DEFAULT 0,

            completed_at TIMESTAMP DEFAULT NOW()

        )
    """)

    logger.info(
        "VIZU LESEN RESULTS READY ✅"
    )

# =========================================================
# VIZU HOREN RESULTS TABLE
# =========================================================

def init_vizu_horen_results_table():
    db_execute("""
        CREATE TABLE IF NOT EXISTS vizu_horen_results (
            user_id BIGINT PRIMARY KEY,
            score INTEGER DEFAULT 0,
            completed_at TIMESTAMP DEFAULT NOW()
        )
    """)
    logger.info("VIZU HOREN RESULTS READY ✅")
# =========================================================
# VIZU SCHREIBEN RESULTS TABLE
# =========================================================

def init_vizu_schreiben_results_table():

    db_execute("""
        CREATE TABLE IF NOT EXISTS
        vizu_schreiben_results (

            user_id BIGINT PRIMARY KEY,

            score INTEGER DEFAULT 0,

            completed_at TIMESTAMP DEFAULT NOW()

        )
    """)

    logger.info(
        "VIZU SCHREIBEN RESULTS READY ✅"
    )
# =========================================================
# VIZU SPRECHEN RESULTS TABLE
# =========================================================

def init_vizu_sprechen_results_table():

    db_execute("""
        CREATE TABLE IF NOT EXISTS
        vizu_sprechen_results (

            user_id BIGINT PRIMARY KEY,

            score INTEGER DEFAULT 0,

            completed_at TIMESTAMP DEFAULT NOW()

        )
    """)

    logger.info(
        "VIZU SPRECHEN RESULTS READY ✅"
    )
# =========================================================
# CERTIFICATES TABLE
# =========================================================

def init_certificate_table():

    db_execute("""
        CREATE TABLE IF NOT EXISTS
        certificates (

            user_id BIGINT PRIMARY KEY,

            total_score INTEGER,

            created_at TIMESTAMP DEFAULT NOW()

        )
    """)

    logger.info(
        "CERTIFICATES TABLE READY ✅"
    )
    # INDEXES
    db_execute("CREATE INDEX IF NOT EXISTS idx_users_score ON users(score)")
    db_execute("CREATE INDEX IF NOT EXISTS idx_users_total_score ON users(total_score)")
    db_execute("CREATE INDEX IF NOT EXISTS idx_users_daily_score ON users(daily_score)")
    db_execute("CREATE INDEX IF NOT EXISTS idx_users_course ON users(course)")
    db_execute("CREATE INDEX IF NOT EXISTS idx_users_approved ON users(approved)")
    db_execute("CREATE INDEX IF NOT EXISTS idx_quiz_progress_user ON quiz_progress(user_id)")

    logger.info("DATABASE TABLES READY ✅")

# =========================================================
# FLASK WEB SERVER (FOR KEEP-ALIVE)
# =========================================================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running ✅"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )
# =========================================================
# HELPER FUNCTIONS & STATES (Pylance xatolarini to'g'rilash uchun)
# =========================================================


def generate_certificate_id():
    # random funksiyasi import qilinganligiga ishonch hosil qiling
    return f"VIZU-{random.randint(100000, 999999)}"

def get_existing_certificate(user_id, rank):
    # db_execute funksiyasi yuqorida e'lon qilingan
    return db_execute(
        "SELECT certificate_id FROM certificates WHERE user_id = %s AND rank = %s",
        (user_id, rank),
        fetchone=True
    )

# =========================================================
# BOT INSTANCE & STORAGE
# =========================================================
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# =========================================================
# STATES GROUP
# =========================================================

class VizuSchreibenState(
    StatesGroup
):

    teil1 = State()

    teil2 = State()
class VizuHorenState(StatesGroup):
    solving = State()

class VizuLesenState(StatesGroup):
    solving = State()

class RegisterState(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()

class VizuCertificateState(StatesGroup):
    waiting_for_payment_check = State()
    waiting_for_ticket_photo = State()

class BroadcastState(StatesGroup):
    waiting_for_message = State()

class PersonalMessageState(StatesGroup):
    waiting_for_id = State()
    waiting_for_text = State()

class ProfileState(StatesGroup):
    change_name = State()

class SchreibenRateState(
    StatesGroup
):
    waiting_score = State()
# =========================================================
# SCHREIBEN STATE
# =========================================================

class SchreibenState(
    StatesGroup
):

    waiting_file = State()


# =========================================================
# SPRECHEN STATE
# =========================================================

class SprechenState(
    StatesGroup
):

    waiting_voice = State()
# =========================================================
# VIZU SPRECHEN STATE
# =========================================================

class VizuSprechenState(
    StatesGroup
):

    teil1 = State()

    teil21 = State()

    teil22 = State()

    teil31 = State()

    teil32 = State()
# =========================================================
# KEYBOARDS (REPLY MARKUPS)
# =========================================================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
         KeyboardButton(text="📚 Artikel Topish"),
         KeyboardButton(text="🎮 So'z O'yini")],

        [KeyboardButton(text="🎥 Video Kurslar"),
         KeyboardButton(text="🎓 Darslarni O'rganish")],

        [KeyboardButton(text="🎬 Medien"),
         KeyboardButton(text="🏅 VIZU-Zertifikat")],
         
        [KeyboardButton(text="📚 Ma'lumotlar"),
         KeyboardButton(text="👤 Mening Profilim")]
    ],
    resize_keyboard=True
)
video_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎬 Bepul Namuna Darslar")],
        [KeyboardButton(text="🇩🇪 A1")],
        [KeyboardButton(text="🇩🇪 A2")],
        [KeyboardButton(text="🇩🇪 B1")],
        [KeyboardButton(text="🔥 A1-B1")],
        [KeyboardButton(text="🔥 A1-C1")],
        [KeyboardButton(text="⬅️ Orqaga")]
    ],
    resize_keyboard=True
)

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="📢 Reklama Yuborish")],
        [KeyboardButton(text="📨 Shaxsiy Xabar")],
        [KeyboardButton(text="⬅️ Admin Chiqish")]
    ],
    resize_keyboard=True
)

info_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👨‍🏫 Ustoz haqida")],
        [KeyboardButton(text="🏆 Natijalar")],
        [KeyboardButton(text="📞 Admin bilan bog'lanish")],
        [KeyboardButton(text="⬅️ Orqaga")]
    ],
    resize_keyboard=True
)

lessons_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🇩🇪 A1"), KeyboardButton(text="🇩🇪 A2")],
        [KeyboardButton(text="🇩🇪 B1"), KeyboardButton(text="🇩🇪 B2")],
        [KeyboardButton(text="🇩🇪 C1")],
        [KeyboardButton(text="🤖 AI Teacher")],
        [KeyboardButton(text="⬅️ Orqaga")]
    ],
    resize_keyboard=True
)

def profile_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏅 Mening Sertifikatlarim")],
            [KeyboardButton(text="✏️ Ism Familiyani o'zgartirish")],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )
medien_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 De-Bücher")],
        [KeyboardButton(text="🎵 De-Musik")],
        [KeyboardButton(text="🎬 De-Filme")],
        [KeyboardButton(text="📺 De-Videos")],
        [KeyboardButton(text="⬅️ Orqaga")]
    ],
    resize_keyboard=True
)
# =========================================================
# VIZU CERTIFICATE MENU
# =========================================================

vizu_certificate_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏅 VIZU-A1")],
        [KeyboardButton(text="🏅 VIZU-A2")],
        [KeyboardButton(text="🏅 VIZU-B1")],
        [KeyboardButton(text="🏅 VIZU-B2")],
        [KeyboardButton(text="🏅 VIZU-C1")],
        [KeyboardButton(text="⬅️ Orqaga")]
    ],
    resize_keyboard=True
)
# =========================================================
# OPEN VIZU CERTIFICATE MENU
# =========================================================

@dp.message(F.text == "🏅 VIZU-Zertifikat")
async def open_vizu_certificate_menu(
    message: Message
):

    await message.answer(

        "🏅 VIZU Academy Zertifikate\n\n"

        "Kerakli sertifikat darajasini tanlang:",

        reply_markup=vizu_certificate_menu_keyboard

    )

# =========================================================
# Medien Handler
# =========================================================

@dp.message(F.text == "🎬 Medien")
async def open_medien(message: Message):

    await message.answer(
        "🎬 Medien bo'limi",
        reply_markup=medien_menu
    )
# =========================================================
# MEDIEN
# =========================================================

MUSIC_CHANNEL_ID = -1003763602068

music_tracks = {}

try:
    with open(
        "Musik.csv",
        "r",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:
            music_tracks[
                int(row["track_number"])
            ] = int(
                row["message_id"]
            )

except Exception as e:
    logger.error(
        f"MUSIK CSV ERROR: {e}"
    )

TOTAL_TRACKS = len(
    music_tracks
)

# =========================================================
# MUSIC KEYBOARD
# =========================================================

def build_music_keyboard(
    page=1
):

    builder = InlineKeyboardBuilder()

    start = (
        (page - 1) * 5
    ) + 1

    end = min(
        start + 4,
        TOTAL_TRACKS
    )

    for track in range(
        start,
        end + 1
    ):

        builder.row(
            InlineKeyboardButton(
                text=f"🎵 {track}",
                callback_data=f"music_{track}"
            )
        )

    navigation = []

    if page > 1:
        navigation.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=f"music_page_{page-1}"
            )
        )

    if end < TOTAL_TRACKS:
        navigation.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"music_page_{page+1}"
            )
        )

    if navigation:
        builder.row(*navigation)

    return builder.as_markup()

# =========================================================
# DE-MUSIK
# =========================================================

@dp.message(
    F.text == "🎵 De-Musik"
)
async def open_music(
    message: Message
):

    if not music_tracks:

        await message.answer(
            "❌ Musik.csv topilmadi."
        )

        return

    await message.answer(
        f"🎵 Deutsche Musik\n\n"
        f"🎼 Jami qo'shiqlar: {TOTAL_TRACKS}\n\n"
        f"Kerakli qo'shiqni tanlang:",
        reply_markup=build_music_keyboard(1)
    )

# =========================================================
# MUSIC PAGE
# =========================================================

@dp.callback_query(
    F.data.startswith(
        "music_page_"
    )
)
async def music_page_handler(
    callback: CallbackQuery
):

    page = int(
        callback.data.split("_")[-1]
    )

    await callback.message.edit_reply_markup(
        reply_markup=
        build_music_keyboard(page)
    )

    await callback.answer()

# =========================================================
# SEND MUSIC
# =========================================================

@dp.callback_query(
    F.data.startswith(
        "music_"
    )
)
async def send_music(
    callback: CallbackQuery
):

    if callback.data.startswith(
        "music_page_"
    ):
        return

    track_number = int(
        callback.data.split("_")[1]
    )

    message_id = music_tracks.get(
        track_number
    )

    if not message_id:

        await callback.answer(
            "❌ Qo'shiq topilmadi",
            show_alert=True
        )

        return

    try:

        await bot.copy_message(
            chat_id=
            callback.from_user.id,

            from_chat_id=
            MUSIC_CHANNEL_ID,

            message_id=
            message_id
        )

        await callback.answer(
            f"🎵 Track #{track_number}"
        )

    except Exception as e:

        logger.error(
            f"MUSIC ERROR: {e}"
        )

        await callback.answer(
            "❌ Audio yuborishda xatolik",
            show_alert=True
        )
# =========================================================
# DE-BUCHER
# =========================================================

@dp.message(F.text == "📚 De-Bücher")
async def open_books(message: Message):

    await message.answer(

        "📚 Nemis kitoblari bo'limi\n\n"
        "🚧 Tez orada ishga tushiriladi."

    )
# =========================================================
# DE-FILME
# =========================================================

@dp.message(F.text == "🎬 De-Filme")
async def open_films(message: Message):

    await message.answer(

        "🎬 Nemis filmlari bo'limi\n\n"
        "🚧 Tez orada ishga tushiriladi."

    )
# =========================================================
# DE-VIDEOS
# =========================================================

@dp.message(F.text == "📺 De-Videos")
async def open_videos(message: Message):

    await message.answer(

        "📺 Nemis videolari bo'limi\n\n"
        "🚧 Tez orada ishga tushiriladi."

    )
# =========================================================
# BACK FROM MEDIEN
# =========================================================

@dp.message(F.text == "⬅️ Orqaga")
async def back_to_main_menu(
    message: Message
):

    await message.answer(
        "🏠 Asosiy menyu",
        reply_markup=main_menu
    )
# =========================================================
# GLOBAL CONSTANTS
# =========================================================
LESSON_TASKS = ["Grammatik", "Lesen", "Hören", "Schreiben", "Sprechen"]

# Har bir daraja uchun darslar nomini dinamik hosil qilish uchun 
# bazaviy raqamlarni saqlaymiz
LESSON_COUNTS = {
    "A1": 14,
    "A2": 14,
    "B1": 20,
    "B2": 30,
    "C1": 22
}

def get_lesson_list(level):
    """
    Berilgan daraja uchun "1-dars", "2-dars" ... formatida 
    list qaytaruvchi funksiya.
    """
    max_count = LESSON_COUNTS.get(level, 0)
    return [f"{i}-dars" for i in range(1, max_count + 1)]

# =========================================================
# HELPER FUNCTIONS & OPTIMIZED DB GETTERS
# =========================================================
def is_admin(message: Message) -> bool:
    if message.from_user:
        return message.from_user.id == ADMIN_ID
    return False

def get_available_levels(course: str) -> list:
    mapping = {
        "🇩🇪 A1": ["A1"],
        "🇩🇪 A2": ["A2"],
        "🇩🇪 B1": ["B1"],
        "🔥 A1-B1": ["A1", "A2", "B1"],
        "🔥 A1-C1": ["A1", "A2", "B1", "B2", "C1"]
    }
    return mapping.get(course, [])

def build_lessons_menu(levels: list) -> ReplyKeyboardMarkup:
    keyboard = []
    row = []
    
    for level in levels:
        row.append(KeyboardButton(text=f"📘 {level}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
            
    if row:
        keyboard.append(row)
        
    keyboard.append([KeyboardButton(text="🤖 AI Teacher")])
    keyboard.append([KeyboardButton(text="⬅️ Orqaga")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_unlocked_lesson(user_id: int, level: str) -> int:
    # COALESCE yordamida agar dars bajarilmagan bo'lsa avtomat 1 qaytaradi
    row = db_execute(
        """
        SELECT COALESCE(MAX(lesson), 0) + 1
        FROM lesson_progress
        WHERE user_id = %s AND level = %s AND completed = TRUE
        """,
        (user_id, level),
        fetchone=True
    )
    return row[0] if row else 1

def get_next_task(user_id: int, level: str, lesson: int) -> Optional[str]:
    # Barcha topshiriqlarni bitta so'rovda olib kelamiz (Davl ichida DB ga qayta murojaat qilinmaydi)
    rows = db_execute(
        """
        SELECT task_name 
        FROM lesson_task_progress 
        WHERE user_id = %s AND level = %s AND lesson = %s AND completed = TRUE
        """,
        (user_id, level, lesson),
        fetchall=True
    )
    
    completed_tasks = {r[0] for r in rows} if rows else set()
    
    for task in LESSON_TASKS:
        if task not in completed_tasks:
            return task
            
    return None

def is_final_exam_passed(user_id: int, level: str) -> bool:
    row = db_execute(
        """
        SELECT final_exam_passed
        FROM level_exams
        WHERE user_id = %s AND level = %s
        """,
        (user_id, level),
        fetchone=True
    )
    return bool(row[0]) if row else False
# =========================================================
# LEVEL LESSONS MENU
# =========================================================

def build_level_lessons_menu(
    level,
    unlocked,
    exam_passed=False
):

    total_lessons = LESSON_COUNTS.get(
        level,
        10
    )

    keyboard = []

    current_row = []

    for lesson in range(
        1,
        total_lessons + 1
    ):

        if lesson < unlocked:

            text = (
                f"✅ Unterricht {lesson}"
            )

        elif lesson == unlocked:

            text = (
                f"📖 Unterricht {lesson}"
            )

        else:

            text = (
                f"🔒 Unterricht {lesson}"
            )

        current_row.append(
            KeyboardButton(
                text=text
            )
        )

        if len(current_row) == 4:

            keyboard.append(
                current_row
            )

            current_row = []

    if current_row:

        keyboard.append(
            current_row
        )

    keyboard.append(
        [
            KeyboardButton(
                text="⬅️ Orqaga"
            )
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=
        f"🇩🇪 {level} darslaridan birini tanlang..."
    )
# =========================================================
# BUILD TASK MENU
# =========================================================

def build_task_menu(
    user_id,
    level,
    lesson
):

    builder = InlineKeyboardBuilder()

    next_task = get_next_task(
        user_id,
        level,
        lesson
    )

    rows = db_execute(
        """
        SELECT task_name

        FROM lesson_task_progress

        WHERE user_id = %s
        AND level = %s
        AND lesson = %s
        AND completed = TRUE
        """,
        (
            user_id,
            level,
            lesson
        ),
        fetchall=True
    )

    completed_tasks = {
        row[0]
        for row in rows
    } if rows else set()

    for task in LESSON_TASKS:

        if task in completed_tasks:

            icon = "✅"

            callback = (
                f"start_{task}_{lesson}"
            )

        elif task == next_task:

            icon = "📖"

            callback = (
                f"start_{task}_{lesson}"
            )

        else:

            icon = "🔒"

            callback = "locked_task"

        builder.row(
            InlineKeyboardButton(
                text=f"{icon} {task}",
                callback_data=callback
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data=f"level_{level}"
        )
    )

    return builder.as_markup()
# =========================================================
# UNTERRICHT HANDLER
# =========================================================

@dp.message(
    F.text.regexp(
        r"^📖 Unterricht \d+$"
    )
)
async def lesson_handler(
    message: Message
):

    user_id = message.from_user.id

    try:

        lesson_num = int(
            message.text.split()[-1]
        )

        # FOYDALANUVCHI TANLAGAN LEVEL
        level = selected_levels.get(
            user_id,
            "A1"
        )

        # ACTIVE LESSON
        active_lessons[user_id] = {

            "level": level,

            "lesson": lesson_num
        }

        await message.answer(

            f"🇩🇪 {level}\n\n"

            f"📖 Unterricht {lesson_num}\n\n"

            f"Kerakli vazifani bajaring:",

            reply_markup=
            build_task_menu(
                user_id,
                level,
                lesson_num
            )
        )

    except Exception as e:

        logger.exception(
            f"LESSON_HANDLER_ERROR: {e}"
        )

        await message.answer(
            "❌ Darsni ochishda xatolik."
        )
# =========================================================
# START GRAMMATIK
# =========================================================
async def start_task_logic(callback: CallbackQuery, task_name: str, 
                           load_func, progress_dict, send_func):
    user_id = callback.from_user.id
    
    if user_id not in active_lessons:
        await callback.answer("Dars topilmadi.")
        return

    level = active_lessons[user_id]["level"]
    lesson = active_lessons[user_id]["lesson"]

    # Bazadan tekshirish
    row = db_execute(
        "SELECT completed FROM lesson_task_progress WHERE user_id = %s AND level = %s AND lesson = %s AND task_name = %s",
        (user_id, level, lesson, task_name),
        fetchone=True
    )

    if row and row[0]:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Qayta ishlash", callback_data=f"repeat_task:{task_name}")
        builder.button(text="❌ Bekor qilish", callback_data="close_menu")
        builder.adjust(1)
        await callback.message.answer(f"✅ Siz {task_name} bo'limini oldin yakunlagansiz. Qayta ishlamoqchimisiz?", reply_markup=builder.as_markup())
        await callback.answer()
        return

    tasks = load_func(level, lesson)
    if not tasks:
        await callback.answer(f"{task_name} topilmadi.")
        return

    # Progressni belgilash
    progress_dict[user_id] = {
        "level": level, "lesson": lesson, "tasks": tasks, "index": 0, "score": 0
    }
    if task_name == "Grammatik":
        progress_dict[user_id]["teil"] = 1

    await callback.message.answer(f"📚 {task_name}\nJami savollar: {len(tasks)}")
    await send_func(callback.message, user_id)
    await callback.answer()

# Misol uchun Grammatik uchun handler
@dp.callback_query(F.data.startswith("start_Grammatik_"))
async def start_grammatik(callback: CallbackQuery):
    await start_task_logic(callback, "Grammatik", load_grammatik, grammatik_progress, send_grammatik_question)
# =========================================================
# SEND GRAMMATIK QUESTION
# =========================================================

async def send_grammatik_question(
    message,
    user_id
):

    progress = grammatik_progress[
        user_id
    ]

    task = progress["tasks"][
        progress["index"]
    ]

    options = [

        task["correct"],

        task["wrong1"],

        task["wrong2"]

    ]

    random.shuffle(
        options
    )

    builder = InlineKeyboardBuilder()

    for option in options:

        builder.button(

            text=option,

            callback_data=
            f"grammatik_answer:{option}"
        )

    builder.adjust(1)

    await message.answer(

        f"📚 Savol "
        f"{progress['index'] + 1}"
        f"/{len(progress['tasks'])}\n\n"

        f"{task['question']}",

        reply_markup=
        builder.as_markup()
    )
# =========================================================
# GRAMMATIK ANSWER
# =========================================================

@dp.callback_query(
    F.data.startswith(
        "grammatik_answer:"
    )
)
async def grammatik_answer(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    if user_id not in grammatik_progress:

        return

    progress = grammatik_progress[
        user_id
    ]

    answer = callback.data.split(
        ":",
        1
    )[1]

    task = progress["tasks"][
        progress["index"]
    ]

    if answer == task["correct"]:

        progress["score"] += 1

        await callback.answer(
            "✅ To'g'ri"
        )

    else:

        await callback.answer(
            f"❌ {task['correct']}"
        )

    progress["index"] += 1

    if progress["index"] >= len(
        progress["tasks"]
    ):

        db_execute(
            """
            INSERT INTO
            lesson_task_progress
            (
                user_id,
                level,
                lesson,
                task_name,
                completed
            )
            VALUES
            (
                %s,%s,%s,%s,TRUE
            )
            ON CONFLICT DO NOTHING
            """,
            (
                user_id,
                progress["level"],
                progress["lesson"],
                "Grammatik"
            )
        )

        await callback.message.answer(

            f"🏁 Grammatik yakunlandi!\n\n"

            f"Natija: "
            f"{progress['score']}"
            f"/{len(progress['tasks'])}"
        )

        del grammatik_progress[
            user_id
        ]

        return

    await send_grammatik_question(
        callback.message,
        user_id
    )
@dp.callback_query(F.data.startswith("repeat_task:"))
async def repeat_task(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in active_lessons:
        return

    task_name = callback.data.split(":", 1)[1]
    level = active_lessons[user_id]["level"]
    lesson = active_lessons[user_id]["lesson"]

    # 1. Ma'lumotlarni yuklash va funksiyalar xaritasi
    tasks_map = {
        "Grammatik": (load_grammatik, grammatik_progress, send_grammatik_question),
        "Lesen": (load_lesen, lesen_progress, send_lesson_lesen_question),
        "Horen": (load_horen, horen_progress, send_lesson_horen_question),
    }

    if task_name not in tasks_map:
        await callback.answer("Noto'g'ri topshiriq turi!")
        return

    load_func, progress_dict, send_func = tasks_map[task_name]
    tasks = load_func(level, lesson)

    if not tasks:
        await callback.answer(f"{task_name} topilmadi.")
        return

    # 2. Progressni yangilash
    progress_data = {
        "level": level,
        "lesson": lesson,
        "tasks": tasks,
        "index": 0,
        "score": 0
    }
    
    # Grammatik uchun maxsus qo'shimcha
    if task_name == "Grammatik":
        progress_data["teil"] = 1

    progress_dict[user_id] = progress_data

    # 3. Javob qaytarish va keyingi qadam
    await callback.message.answer(f"🔄 {task_name} qayta boshlandi.")
    await send_func(callback.message, user_id)
    await callback.answer()
# =========================================================
# SCORE KEYBOARD
# =========================================================

def build_score_keyboard(
    user_id,
    level,
    lesson,
    task_name
):

    builder = InlineKeyboardBuilder()

    for score in range(21):

        builder.button(

            text=str(score),

            callback_data=
            f"rate:{user_id}:{level}:{lesson}:{task_name}:{score}"
        )

    builder.adjust(5)

    return builder.as_markup()
# =========================================================
# CLOSE MENU
# =========================================================

@dp.callback_query(
    F.data == "close_menu"
)
async def close_menu(
    callback: CallbackQuery
):

    await callback.message.delete()

    await callback.answer()
# =========================================================
# START LESEN
# =========================================================

@dp.callback_query(
    F.data.startswith(
        "start_Lesen_"
    )
)
async def start_lesen(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    if user_id not in active_lessons:

        await callback.answer(
            "Dars topilmadi."
        )

        return

    level = active_lessons[user_id]["level"]

    lesson = active_lessons[user_id]["lesson"]

    # =====================================================
    # CHECK PREVIOUS ATTEMPT
    # =====================================================

    row = db_execute(
        """
        SELECT completed

        FROM lesson_task_progress

        WHERE user_id = %s
        AND level = %s
        AND lesson = %s
        AND task_name = 'Lesen'
        """,
        (
            user_id,
            level,
            lesson
        ),
        fetchone=True
    )

    if row and row[0]:

        builder = InlineKeyboardBuilder()

        builder.button(
            text="🔄 Qayta ishlash",
            callback_data="repeat_task:Lesen"
        )

        builder.button(
            text="❌ Bekor qilish",
            callback_data="close_menu"
        )

        builder.adjust(1)

        await callback.message.answer(
            "✅ Siz ushbu Lesen bo'limini oldin yakunlagansiz.\n\n"
            "Qayta ishlamoqchimisiz?",
            reply_markup=builder.as_markup()
        )

        await callback.answer()

        return

    # =====================================================
    # SEND IMAGE
    # =====================================================

    image_path = get_lesen_image(
        level,
        lesson
    )

    if image_path:

        await callback.message.answer_photo(
            FSInputFile(image_path),
            caption=
            f"📖 Lesen\n\n"
            f"🇩🇪 {level} | Unterricht {lesson}"
        )

    # =====================================================
    # LOAD TASKS
    # =====================================================

    tasks = load_lesen(
        level,
        lesson
    )

    if not tasks:

        await callback.answer(
            "Lesen topilmadi."
        )

        return

    lesen_progress[user_id] = {

        "level": level,

        "lesson": lesson,

        "tasks": tasks,

        "index": 0,

        "score": 0
    }
    # =====================================================
    # START BUTTON
    # =====================================================

    builder = InlineKeyboardBuilder()

    builder.button(
        text="▶️ Testni Boshlash",
        callback_data="begin_lesen"
    )

    builder.adjust(1)

    logger.info(
        f"LESEN READY | USER={user_id}"
    )

    logger.info(
        f"LESEN USERS: "
        f"{list(lesen_progress.keys())}"
    )

    await callback.message.answer(

        "📖 Matnni yoki rasmni diqqat bilan o'qing.\n\n"
        "Tayyor bo'lsangiz testni boshlang.",

        reply_markup=
        builder.as_markup()
    )

    await callback.answer()
# =========================================================
# BEGIN LESEN
# =========================================================

@dp.callback_query(
    F.data == "begin_lesen"
)
async def begin_lesen(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    logger.info(
        f"BEGIN LESEN CLICKED | USER={user_id}"
    )

    logger.info(
        f"CURRENT LESEN USERS: "
        f"{list(lesen_progress.keys())}"
    )

    if user_id not in lesen_progress:

        logger.error(
            f"LESEN PROGRESS NOT FOUND | USER={user_id}"
        )

        await callback.answer(
            "❌ Lesen sessiyasi topilmadi.",
            show_alert=True
        )

        return

    try:

        await send_lesson_lesen_question(
            callback.message,
            user_id
        )

        logger.info(
            f"FIRST LESEN QUESTION SENT | USER={user_id}"
        )

    except Exception as e:

        logger.exception(
            f"BEGIN LESEN ERROR: {e}"
        )

        await callback.answer(
            "❌ Testni boshlashda xatolik.",
            show_alert=True
        )

        return

    await callback.answer()
# =========================================================
# SEND LESEN QUESTION
# =========================================================

async def send_lesson_lesen_question(
    message,
    user_id
):

    if user_id not in lesen_progress:

        logger.error(
            f"LESEN PROGRESS NOT FOUND: {user_id}"
        )

        return

    progress = lesen_progress[user_id]

    if progress["index"] >= len(
        progress["tasks"]
    ):

        logger.error(
            f"LESEN INDEX ERROR: {user_id}"
        )

        return

    task = progress["tasks"][
        progress["index"]
    ]

    options = [

        task.get("correct", ""),

        task.get("wrong1", ""),

        task.get("wrong2", "")
    ]

    options = [
        x for x in options
        if x
    ]

    random.shuffle(
        options
    )

    builder = InlineKeyboardBuilder()

    for option in options:

        builder.button(
            text=option,
            callback_data=f"lesen:{option}"
        )

    builder.adjust(1)

    await message.answer(

        f"📖 Frage "
        f"{progress['index'] + 1}"
        f"/{len(progress['tasks'])}\n\n"

        f"{task.get('question', 'Frage fehlt')}",

        reply_markup=
        builder.as_markup()
    )
# =========================================================
# LESEN ANSWER
# =========================================================

@dp.callback_query(
    F.data.startswith(
        "lesen:"
    )
)
async def lesen_answer(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    if user_id not in lesen_progress:
        return

    progress = lesen_progress[user_id]

    answer = callback.data.split(
        ":",
        1
    )[1]

    task = progress["tasks"][
        progress["index"]
    ]

    if answer == task["correct"]:

        progress["score"] += 1

        await callback.answer(
            "✅ Richtig"
        )

    else:

        await callback.answer(
            "❌ Falsch"
        )

    progress["index"] += 1

    if progress["index"] >= len(
        progress["tasks"]
    ):

        db_execute(
            """
            INSERT INTO
            lesson_task_progress
            (
                user_id,
                level,
                lesson,
                task_name,
                completed
            )
            VALUES
            (
                %s,%s,%s,%s,TRUE
            )
            ON CONFLICT
            (
                user_id,
                level,
                lesson,
                task_name
            )
            DO UPDATE SET
            completed = TRUE
            """,
            (
                user_id,
                progress["level"],
                progress["lesson"],
                "Lesen"
            )
        )

        await callback.message.answer(

            f"🏁 Lesen yakunlandi\n\n"

            f"Natija: "
            f"{progress['score']}"
            f"/{len(progress['tasks'])}"
        )

        del lesen_progress[user_id]

        return

    await send_lesson_lesen_question(
        callback.message,
        user_id
    )
# =========================================================
# HOREN FILE HELPERS
# =========================================================

def get_lesson_horen_audio(
    level,
    lesson
):

    return os.path.join(
        "A1-C1-Level",
        "horen_audio",
        f"{level}-{lesson}.mp3"
    )


def get_horen_photo(
    level,
    lesson
):

    return os.path.join(
        "A1-C1-Level",
        "horen_photo",
        f"{level}-{lesson}.png"
    )


# =========================================================
# HELPER: answer index hash (oldini olish uchun)
# =========================================================

SECRET_KEY = os.environ.get("BOT_SECRET_KEY", "change_this_in_production")


def make_answer_token(user_id: int, index: int, correct: str) -> str:
    """
    Foydalanuvchi to'g'ri javobni callback_data orqali soxtalashtira
    olmasligi uchun HMAC token yaratadi.
    """
    raw = f"{user_id}:{index}:{correct}"
    return hmac.new(
        SECRET_KEY.encode(),
        raw.encode(),
        hashlib.sha256
    ).hexdigest()[:16]


def verify_answer_token(user_id: int, index: int, correct: str, token: str) -> bool:
    expected = make_answer_token(user_id, index, correct)
    return hmac.compare_digest(expected, token)


# =========================================================
# START HOREN
# =========================================================
@dp.callback_query(
    F.data.startswith("start_Hören_")
)
async def start_hören(callback: CallbackQuery):

    # log callback info here (callback is only defined inside handler)
    logger.warning(f"[HOREN] CLICKED: {callback.data}")
    logger.warning(f"[HOREN] USER: {callback.from_user.id}")

    user_id = callback.from_user.id

    # --- Aktiv dars tekshiruvi ---
    lesson_data = active_lessons.get(user_id)
    if not lesson_data:
        await callback.answer("Dars topilmadi.", show_alert=True)
        return

    level  = lesson_data["level"]
    lesson = lesson_data["lesson"]

    # --- Oldingi urinish tekshiruvi ---
    row = db_execute(
        """
        SELECT completed
        FROM lesson_task_progress
        WHERE user_id = %s
          AND level   = %s
          AND lesson  = %s
          AND task_name = 'Horen'
        """,
        (user_id, level, lesson),
        fetchone=True
    )

    if row and row[0]:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Qayta ishlash",  callback_data="repeat_task:Horen")
        builder.button(text="❌ Bekor qilish",    callback_data="close_menu")
        builder.adjust(1)

        await callback.message.answer(
            "✅ Siz ushbu Hören bo'limini oldin yakunlagansiz.\n\n"
            "Qayta ishlamoqchimisiz?",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        return

    # --- Savollarni yuklash ---
    tasks = load_horen(level, lesson)
    if not tasks:
        await callback.answer("Horen topilmadi.", show_alert=True)
        return

    # --- Progressni saqlash ---
    horen_progress[user_id] = {
        "level":  level,
        "lesson": lesson,
        "tasks":  tasks,
        "index":  0,
        "score":  0,
    }

    # --- Audio yuborish ---
    audio_path = get_horen_audio(level, lesson)
    if os.path.exists(audio_path):
        await callback.message.answer_audio(
            audio=FSInputFile(audio_path),
            caption=(
                f"🎧 Horen\n\n"
                f"🇩🇪 {level} | Unterricht {lesson}"
            )
        )

    # --- Rasm yuborish ---
    photo_path = get_horen_photo(level, lesson)
    if os.path.exists(photo_path):
        await callback.message.answer_photo(FSInputFile(photo_path))

    # --- Boshlash tugmasi ---
    builder = InlineKeyboardBuilder()
    builder.button(text="▶️ Testni Boshlash", callback_data="begin_horen")
    builder.adjust(1)

    await callback.message.answer(
        "🎧 Audio va rasmni diqqat bilan ko'rib chiqing.\n\n"
        "Tayyor bo'lsangiz testni boshlang.",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


# =========================================================
# SAVOL YUBORISH (ichki funksiya)
# =========================================================

async def send_lesson_horen_question(message, user_id: int):
    """
    Joriy savolni shuffled variantlar bilan yuboradi.
    Har bir tugma callback_data = "horen:{token}:{option}" ko'rinishida.
    Token serverda tekshiriladi — foydalanuvchi soxta javob yubora olmaydi.
    """
    progress = horen_progress.get(user_id)
    if not progress:
        await message.answer("❌ Sessiya topilmadi. Qaytadan boshlang.")
        return

    index = progress["index"]

    # Chegaradan chiqib ketishdan himoya
    if index >= len(progress["tasks"]):
        logger.warning(f"[HOREN] user={user_id} index={index} out of range")
        await message.answer("❌ Ichki xatolik. Qaytadan boshlang.")
        horen_progress.pop(user_id, None)
        return

    task = progress["tasks"][index]
    correct = task["correct"]

    options = [correct, task["wrong1"], task["wrong2"]]
    random.shuffle(options)

    # Har bir variant uchun HMAC token
    token = make_answer_token(user_id, index, correct)

    builder = InlineKeyboardBuilder()
    for option in options:
        builder.button(
            text=option,
            callback_data=f"horen:{token}:{option}"
        )
    builder.adjust(1)

    await message.answer(
        f"🎧 Frage {index + 1}/{len(progress['tasks'])}\n\n"
        f"{task['question']}",
        reply_markup=builder.as_markup()
    )


# =========================================================
# JAVOB QABUL QILISH
# =========================================================

@dp.callback_query(F.data.startswith("horen:"))
async def horen_answer(callback: CallbackQuery):

    user_id = callback.from_user.id

    progress = horen_progress.get(user_id)
    if not progress:
        await callback.answer("❌ Sessiya topilmadi.", show_alert=True)
        return

    # --- Callback ma'lumotini ajratish ---
    parts = callback.data.split(":", 2)
    if len(parts) != 3:
        await callback.answer("❌ Noto'g'ri format.", show_alert=True)
        return

    _, received_token, chosen_option = parts

    index   = progress["index"]
    tasks   = progress["tasks"]

    if index >= len(tasks):
        await callback.answer("❌ Savol topilmadi.", show_alert=True)
        return

    task    = tasks[index]
    correct = task["correct"]

    # --- Token tekshiruvi (soxtalashtirish oldini olish) ---
    if not verify_answer_token(user_id, index, correct, received_token):
        logger.warning(
            f"[HOREN] Invalid token: user={user_id} "
            f"index={index} option={chosen_option!r}"
        )
        await callback.answer("❌ Token xatosi. Qaytadan boshlang.", show_alert=True)
        horen_progress.pop(user_id, None)
        return

    # --- Javobni baholash ---
    if chosen_option == correct:
        progress["score"] += 1
        await callback.answer("✅ Richtig!")
    else:
        await callback.answer(f"❌ To'g'ri javob: {correct}", show_alert=True)

    progress["index"] += 1

    # --- Tugadimi? ---
    if progress["index"] >= len(tasks):

        score  = progress["score"]
        total  = len(tasks)
        level  = progress["level"]
        lesson = progress["lesson"]

        # DB ga yozish
        try:
            db_execute(
                """
                INSERT INTO lesson_task_progress
                    (user_id, level, lesson, task_name, completed)
                VALUES
                    (%s, %s, %s, %s, TRUE)
                ON CONFLICT (user_id, level, lesson, task_name)
                DO UPDATE SET completed = TRUE
                """,
                (user_id, level, lesson, "Horen")
            )
        except Exception as e:
            logger.exception(f"[HOREN] DB write error: {e}")

        await callback.message.answer(
            f"🏁 Hören yakunlandi!\n\n"
            f"Natija: {score}/{total}"
        )

        # Sessiyani tozalash
        horen_progress.pop(user_id, None)
        return

    # --- Keyingi savol ---
    await send_lesson_horen_question(callback.message, user_id)


# =========================================================
# BOSHLASH TUGMASI
# =========================================================

@dp.callback_query(F.data == "begin_horen")
async def begin_horen(callback: CallbackQuery):

    user_id = callback.from_user.id

    if user_id not in horen_progress:
        await callback.answer(
            "❌ Horen sessiyasi topilmadi. Qaytadan boshlang.",
            show_alert=True
        )
        return

    try:
        await send_lesson_horen_question(callback.message, user_id)
    except Exception as e:
        logger.exception(f"[HOREN] begin_horen error: {e}")
        await callback.message.answer(
            "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring."
        )
        horen_progress.pop(user_id, None)
        return

    await callback.answer()
# =========================================================
# SCHREIBEN PHOTO
# =========================================================

def get_schreiben_photo(
    level,
    lesson
):

    return os.path.join(
        "A1-C1-Level",
        "schreiben_photo",
        f"{level}-{lesson}.png"
    )


# =========================================================
# SPRECHEN PHOTO
# =========================================================

def get_sprechen_photo(
    level,
    lesson
):

    return os.path.join(
        "A1-C1-Level",
        "sprechen_photo",
        f"{level}-{lesson}.png"
    )
# =========================================================
# START SCHREIBEN
# =========================================================

@dp.callback_query(
    F.data.startswith(
        "start_Schreiben_"
    )
)
async def start_schreiben(
    callback: CallbackQuery,
    state: FSMContext
):

    user_id = callback.from_user.id

    if user_id not in active_lessons:

        await callback.answer(
            "Dars topilmadi."
        )

        return

    level = active_lessons[user_id]["level"]

    lesson = active_lessons[user_id]["lesson"]

    # =====================================================
    # CHECK PREVIOUS ATTEMPT
    # =====================================================

    row = db_execute(
        """
        SELECT completed

        FROM lesson_task_progress

        WHERE user_id = %s
        AND level = %s
        AND lesson = %s
        AND task_name = 'Schreiben'
        """,
        (
            user_id,
            level,
            lesson
        ),
        fetchone=True
    )

    if row and row[0]:

        builder = InlineKeyboardBuilder()

        builder.button(
            text="🔄 Qayta ishlash",
            callback_data="repeat_task:Schreiben"
        )

        builder.button(
            text="❌ Bekor qilish",
            callback_data="close_menu"
        )

        builder.adjust(1)

        await callback.message.answer(
            "✅ Siz ushbu Schreiben bo'limini oldin yakunlagansiz.\n\n"
            "Qayta ishlamoqchimisiz?",
            reply_markup=builder.as_markup()
        )

        await callback.answer()

        return

    photo_path = get_schreiben_photo(
        level,
        lesson
    )

    if os.path.exists(photo_path):

        await callback.message.answer_photo(
            FSInputFile(photo_path),
            caption=
            f"✍️ Schreiben\n\n"
            f"🇩🇪 {level}\n"
            f"📖 Unterricht {lesson}\n\n"
            f"Topshiriqni bajaring va rasm yoki PDF yuboring."
        )

    await state.update_data(
        level=level,
        lesson=lesson
    )

    await state.set_state(
        SchreibenState.waiting_file
    )

    await callback.answer()
# =========================================================
# RECEIVE SCHREIBEN
# =========================================================

@dp.message(
    SchreibenState.waiting_file,
    F.photo | F.document
)
async def receive_schreiben(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    level = data["level"]

    lesson = data["lesson"]

    caption = (
        f"✍️ SCHREIBEN\n\n"
        f"👤 USER ID: {message.from_user.id}\n"
        f"🇩🇪 LEVEL: {level}\n"
        f"📖 LESSON: {lesson}"
    )

    await bot.send_message(

        SCHREIBEN_CHANNEL_ID,

        caption,

        reply_markup=
        build_score_keyboard(
            message.from_user.id,
            level,
            lesson,
            "Schreiben"
        )
    )

    await bot.forward_message(

        chat_id=SCHREIBEN_CHANNEL_ID,

        from_chat_id=message.chat.id,

        message_id=message.message_id
    )

    await message.answer(

        "✅ Schreiben topshirig'i yuborildi.\n\n"
        "Ustoz tekshirganidan keyin ball beriladi."
    )

    await state.clear()
# =========================================================
# INVALID SCHREIBEN
# =========================================================

@dp.message(
    SchreibenState.waiting_file
)
async def invalid_schreiben(
    message: Message
):

    await message.answer(
        "❌ Rasm yoki PDF yuboring."
    )
# =========================================================
# START SPRECHEN
# =========================================================

@dp.callback_query(
    F.data.startswith(
        "start_Sprechen_"
    )
)
async def start_sprechen(
    callback: CallbackQuery,
    state: FSMContext
):

    user_id = callback.from_user.id

    if user_id not in active_lessons:

        await callback.answer(
            "Dars topilmadi."
        )

        return

    level = active_lessons[user_id]["level"]

    lesson = active_lessons[user_id]["lesson"]

    row = db_execute(
        """
        SELECT completed

        FROM lesson_task_progress

        WHERE user_id=%s
        AND level=%s
        AND lesson=%s
        AND task_name='Sprechen'
        """,
        (
            user_id,
            level,
            lesson
        ),
        fetchone=True
    )

    if row and row[0]:

        builder = InlineKeyboardBuilder()

        builder.button(
            text="🔄 Qayta ishlash",
            callback_data="repeat_task:Sprechen"
        )

        builder.button(
            text="❌ Bekor qilish",
            callback_data="close_menu"
        )

        builder.adjust(1)

        await callback.message.answer(
            "✅ Siz ushbu Sprechen bo'limini oldin yakunlagansiz.\n\n"
            "Qayta ishlamoqchimisiz?",
            reply_markup=builder.as_markup()
        )

        await callback.answer()

        return

    photo_path = get_sprechen_photo(
        level,
        lesson
    )

    if os.path.exists(
        photo_path
    ):

        await callback.message.answer_photo(
            FSInputFile(
                photo_path
            ),
            caption=
            f"🎤 Sprechen\n\n"
            f"🇩🇪 {level}\n"
            f"📖 Unterricht {lesson}\n\n"
            f"Voice yuboring."
        )

    await state.update_data(
        level=level,
        lesson=lesson
    )

    await state.set_state(
        SprechenState.waiting_voice
    )

    await callback.answer()
# =========================================================
# RECEIVE SPRECHEN
# =========================================================

@dp.message(
    SprechenState.waiting_voice,
    F.voice
)
async def receive_sprechen(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    level = data["level"]

    lesson = data["lesson"]

    caption = (
        f"🎤 SPRECHEN\n\n"
        f"👤 USER ID: {message.from_user.id}\n"
        f"🇩🇪 LEVEL: {level}\n"
        f"📖 LESSON: {lesson}"
    )

    await bot.send_message(

        SPRECHEN_CHANNEL_ID,

        caption,

        reply_markup=
        build_score_keyboard(
            message.from_user.id,
            level,
            lesson,
            "Sprechen"
        )
    )

    await bot.forward_message(

        chat_id=SPRECHEN_CHANNEL_ID,

        from_chat_id=message.chat.id,

        message_id=message.message_id
    )

    await message.answer(

        "✅ Sprechen topshirig'i yuborildi.\n\n"
        "Ustoz tekshirganidan keyin ball beriladi."
    )

    await state.clear()
# =========================================================
# INVALID SPRECHEN
# =========================================================

@dp.message(
    SprechenState.waiting_voice
)
async def invalid_sprechen(
    message: Message
):

    await message.answer(
        "❌ Voice yuboring."
    )

# =========================================================
# SCORE KEYBOARD
# =========================================================

def build_score_keyboard(
    user_id,
    level,
    lesson,
    task_name
):

    builder = InlineKeyboardBuilder()

    for score in range(21):

        builder.button(
            text=str(score),
            callback_data=
            f"rate:{user_id}:{level}:{lesson}:{task_name}:{score}"
        )

    builder.adjust(5)

    return builder.as_markup()
# =========================================================
# RATE TASK
# =========================================================

@dp.callback_query(
    F.data.startswith(
        "rate:"
    )
)
async def rate_task(
    callback: CallbackQuery
):

    if callback.from_user.id != ADMIN_ID:

        await callback.answer()

        return

    _, user_id, level, lesson, task_name, score = (
        callback.data.split(":")
    )

    user_id = int(user_id)

    lesson = int(lesson)

    score = int(score)

    # =====================================================
    # SAVE SCORE
    # =====================================================

    db_execute(
        """
        INSERT INTO lesson_scores
        (
            user_id,
            level,
            lesson,
            task_name,
            score,
            rated_by
        )
        VALUES
        (
            %s,%s,%s,%s,%s,%s
        )
        ON CONFLICT
        (
            user_id,
            level,
            lesson,
            task_name
        )
        DO UPDATE SET
            score = EXCLUDED.score,
            rated_by = EXCLUDED.rated_by,
            rated_at = NOW()
        """,
        (
            user_id,
            level,
            lesson,
            task_name,
            score,
            callback.from_user.id
        )
    )

    # =====================================================
    # COMPLETE TASK
    # =====================================================

    db_execute(
        """
        INSERT INTO lesson_task_progress
        (
            user_id,
            level,
            lesson,
            task_name,
            completed
        )
        VALUES
        (
            %s,%s,%s,%s,TRUE
        )
        ON CONFLICT
        (
            user_id,
            level,
            lesson,
            task_name
        )
        DO UPDATE SET
            completed = TRUE,
            completed_at = NOW()
        """,
        (
            user_id,
            level,
            lesson,
            task_name
        )
    )

    # =====================================================
    # USER NOTIFICATION
    # =====================================================

    try:

        await bot.send_message(

            user_id,

            f"✅ {task_name} tekshirildi.\n\n"
            f"Natija: {score}/20"
        )

    except Exception:

        pass

    # =====================================================
    # LESSON COMPLETED ?
    # =====================================================

    rows = db_execute(
        """
        SELECT task_name

        FROM lesson_task_progress

        WHERE user_id = %s
        AND level = %s
        AND lesson = %s
        AND completed = TRUE
        """,
        (
            user_id,
            level,
            lesson
        ),
        fetchall=True
    )

    completed_tasks = {
        row[0]
        for row in rows
    }

    required_tasks = {

        "Grammatik",

        "Lesen",

        "Horen",

        "Schreiben",

        "Sprechen"
    }

    if required_tasks.issubset(
        completed_tasks
    ):

        db_execute(
            """
            INSERT INTO lesson_progress
            (
                user_id,
                level,
                lesson,
                completed
            )
            VALUES
            (
                %s,%s,%s,TRUE
            )
            ON CONFLICT
            (
                user_id,
                level,
                lesson
            )
            DO UPDATE SET
                completed = TRUE,
                completed_at = NOW()
            """,
            (
                user_id,
                level,
                lesson
            )
        )

        try:

            await bot.send_message(

                user_id,

                f"🎉 Unterricht {lesson} muvaffaqiyatli yakunlandi!\n\n"
                f"✅ Keyingi dars ochildi."
            )

        except Exception:

            pass

    # =====================================================
    # UPDATE ADMIN MESSAGE
    # =====================================================

    try:

        await callback.message.edit_text(

            callback.message.text +

            f"\n\n✅ BAHOLANDI: {score}/20"
        )

    except Exception:

        pass

    await callback.answer(
        "Ball saqlandi."
    )
# =========================================================
# CHECK LESSON COMPLETED
# =========================================================

def check_lesson_completed(
    user_id,
    level,
    lesson
):

    rows = db_execute(
        """
        SELECT task_name

        FROM lesson_task_progress

        WHERE user_id = %s
        AND level = %s
        AND lesson = %s
        AND completed = TRUE
        """,
        (
            user_id,
            level,
            lesson
        ),
        fetchall=True
    )

    completed = {
        row[0]
        for row in rows
    }

    required = {

        "Grammatik",

        "Lesen",

        "Horen",

        "Schreiben",

        "Sprechen"
    }

    return required.issubset(
        completed
    )
# =========================================================
# COMPLETE LESSON
# =========================================================

async def complete_lesson(
    user_id,
    level,
    lesson
):

    db_execute(
        """
        INSERT INTO lesson_progress
        (
            user_id,
            level,
            lesson,
            completed
        )
        VALUES
        (
            %s,%s,%s,TRUE
        )
        ON CONFLICT
        (
            user_id,
            level,
            lesson
        )
        DO UPDATE SET
            completed = TRUE,
            completed_at = NOW()
        """,
        (
            user_id,
            level,
            lesson
        )
    )

    try:

        await bot.send_message(

            user_id,

            f"🎉 Unterricht {lesson} yakunlandi!\n\n"

            f"✅ Keyingi dars ochildi."
        )

    except Exception:

        pass
# =========================================================
# CHECK SUBSCRIPTION
# =========================================================

async def check_subscription(
    user_id: int
) -> bool:
    try:

        member = await bot.get_chat_member(
            CHANNEL_USERNAME,
            user_id
        )

        return member.status not in (
            "left",
            "kicked"
        )

    except Exception as e:

        logger.error(
            f"Subscription error: {e}"
        )

        return False


# =========================================================
# SUBSCRIPTION MIDDLEWARE
# =========================================================

class SubscriptionMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable,
        event,
        data: Dict[str, Any]
    ):

        if not getattr(
            event,
            "from_user",
            None
        ):
            return await handler(
                event,
                data
            )

        # ADMIN BYPASS
        if event.from_user.id == ADMIN_ID:
            return await handler(
                event,
                data
            )

        # /start
        if isinstance(
            event,
            Message
        ):

            if (
                event.text
                and
                event.text.startswith(
                    "/start"
                )
            ):
                return await handler(
                    event,
                    data
                )

        # CHECK SUB CALLBACK
        if isinstance(
            event,
            CallbackQuery
        ):

            if event.data == "check_sub":
                return await handler(
                    event,
                    data
                )

        subscribed = await check_subscription(
            event.from_user.id
        )

        if not subscribed:

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📢 Kanalga A'zo Bo'lish",
                            url="https://t.me/vizu_deutsch"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="✅ Tekshirish",
                            callback_data="check_sub"
                        )
                    ]
                ]
            )

            text = (
                "❌ Botdan foydalanish uchun "
                "avval kanalga a'zo bo'ling."
            )

            try:

                if isinstance(
                    event,
                    Message
                ):

                    await event.answer(
                        text,
                        reply_markup=keyboard
                    )

                elif isinstance(
                    event,
                    CallbackQuery
                ):

                    await event.message.answer(
                        text,
                        reply_markup=keyboard
                    )

                    await event.answer()

            except Exception as e:

                logger.error(
                    f"Subscription middleware error: {e}"
                )

            return

        return await handler(
            event,
            data
        )


# =========================================================
# GLOBAL SUBSCRIPTION PROTECTION
# =========================================================

dp.message.middleware(
    SubscriptionMiddleware()
)

dp.callback_query.middleware(
    SubscriptionMiddleware()
)
# =========================================================
# ADMIN TEXT LOG
# =========================================================

async def send_admin_log(
    text
):
    logger.info(
        f"ADMIN_CHANNEL_ID = {ADMIN_CHANNEL_ID}"
    )

    if not ADMIN_CHANNEL_ID:
        logger.warning(
            "ADMIN_CHANNEL_ID topilmadi!"
        )
        return

    try:
        await bot.send_message(
            chat_id=    ADMIN_CHANNEL_ID,
            text=text
        )
        logger.info(
            "ADMIN LOG SENT ✅"
        )
    except Exception as e:
        logger.exception(
            f"Admin log error: {e}"
        )

# =========================================================
# ADMIN PHOTO LOG
# =========================================================

async def send_admin_photo_log(
    photo_path,
    caption
):
    logger.info(
        f"ADMIN_CHANNEL_ID = {ADMIN_CHANNEL_ID}"
    )

    if not ADMIN_CHANNEL_ID:
        logger.warning(
            "ADMIN_CHANNEL_ID topilmadi!"
        )
        return

    if not os.path.exists(
        photo_path
    ):
        logger.warning(
            f"Photo not found: {photo_path}"
        )
        return

    try:
        await bot.send_photo(
            chat_id=ADMIN_CHANNEL_ID,
            photo=FSInputFile(
                photo_path
            ),
            caption=caption
        )
        logger.info(
            "ADMIN PHOTO SENT ✅"
        )
    except Exception as e:
        logger.exception(
            f"Admin photo log error: {e}"
        )

# =========================================================
# SAFE MESSAGE
# =========================================================

async def safe_message(
    user_id,
    text,
    reply_markup=None
):
    try:
        await bot.send_message(
            user_id,
            text,
            reply_markup=reply_markup
        )
        return True
    except Exception as e:
        logger.error(
            f"Safe message error: {e}"
        )
        return False

# =========================================================
# SAFE PHOTO
# =========================================================

async def safe_photo(
    user_id,
    photo,
    caption=None,
    reply_markup=None
):
    try:
        await bot.send_photo(
            user_id,
            photo,
            caption=caption,
            reply_markup=reply_markup
        )
        return True
    except Exception as e:
        logger.error(
            f"Safe photo error: {e}"
        )
        return False

# =========================
# ARTIKEL DATA
# =========================

artikel: dict[str, str] = {}
artikel_users: dict[int, float] = {}

def load_artikel():
    csv_path = "nouns.csv"

    if not os.path.exists(csv_path):
        logger.warning(
            "nouns.csv not found — Artikel feature disabled."
        )
        return

    try:
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
                except Exception as e:
                    logger.error(f"Row parsing error in load_artikel: {e}")
    except Exception as e:
        logger.error(f"File open error in load_artikel: {e}")

    logger.info(
        f"Artikel loaded: {len(artikel)} words"
    )
# =========================
# ARTIKEL TOPISH
# =========================

artikel_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ Artikel Tizimini Yopish")]
    ],
    resize_keyboard=True
)


@dp.message(F.text == "📚 Artikel Topish")
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
# CLOSE ARTIKEL MODE
# =========================

@dp.message(F.text == "❌ Artikel Tizimini Yopish")
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
# ARTIKEL HANDLER
# =========================

@dp.message(
    F.text,
    lambda message: message.from_user.id in artikel_users
)
async def artikel_handler(message: Message):

    word = message.text.lower().strip()

    result = artikel.get(word)

    await message.answer(
        result if result else (
            "❌ So'z topilmadi.\n\n"
            "Boshqa so'z yuboring."
        )
    )
# =========================
# CLOSE ARTIKEL MODE
# =========================

@dp.message(F.text == "❌ Artikel Tizimini Yopish")
async def close_artikel_mode(message: Message):

    artikel_users.pop(
        message.from_user.id,
        None
    )

    await message.answer(

        "✅ Artikel tizimi yopildi.",

        reply_markup=main_menu

    )
# =========================================================
# START COMMAND HANDLER
# =========================================================

@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    full_name = message.from_user.full_name or "Foydalanuvchi"

    # 1. Kanal obunasini tekshirish
    if not await check_subscription(user_id):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📢 Kanalga A'zo Bo'lish",
                        url="https://t.me/vizu_deutsch"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✅ Tekshirish",
                        callback_data="check_sub"
                    )
                ]
            ]
        )

        await message.answer(
            "❌ Botdan foydalanish uchun avval rasmiy kanalimizga a'zo bo'lishingiz kerak.",
            reply_markup=keyboard
        )
        return

    # 2. Foydalanuvchini ma'lumotlar bazasiga qo'shish yoki yangilash
    db_execute(
        """
        INSERT INTO users (user_id, full_name, approved, unlocked_level) 
        VALUES (%s, %s, 0, 'A1') 
        ON CONFLICT (user_id) 
        DO UPDATE SET full_name = EXCLUDED.full_name
        """,
        (user_id, full_name)
    )
    await message.answer(
    "🇩🇪 Nemis Tili o'rganish uchun @vizu_academy_bot ga xush kelibsiz!\n\n"
    "Platformamiz orqali nemis tilini zamonaviy va qulay usulda o'rganing:\n\n"
    "📚 Video darslar orqali bosqichma-bosqich ta'lim\n"
    "📝 So`zlar artikelini oson toping\n"
    "🎯 Mock Test va imtihon tayyorgarligi\n"
    "🎮 So'z o'yinlari orqali lug'at boyligini oshirish\n"
    "📊 Natijalaringizni kuzatish imkoniyati\n"
    "🏆 A1 → C1 gacha tizimli o'quv dasturi\n\n"
    "🔥 Hozirda barcha video kurslar uchun Katta chegirmalar!\n\n"
    "💰 Atigi 50.000 so'm bilan bugunoq o'rganishni boshlang.\n\n"
    "👇 Kerakli bo'limni tanlang:",
    reply_markup=main_menu
)

# =========================================================
# CHECK SUBSCRIPTION BUTTON
# =========================================================

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    full_name = callback.from_user.full_name or "Foydalanuvchi"

    if await check_subscription(user_id):
        await callback.answer("✅ Obuna tasdiqlandi!")

        db_execute(
            """
            INSERT INTO users (user_id, full_name, approved) 
            VALUES (%s, %s, 0) 
            ON CONFLICT (user_id) 
            DO UPDATE SET full_name = EXCLUDED.full_name
            """,
            (user_id, full_name)
        )

        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            "✅ <b>Obuna muvaffaqiyatli tasdiqlandi!</b>\n\n"
            "🇩🇪 Nemis tili darslari botiga xush kelibsiz. Quyidagi menyudan kerakli bo'limni tanlang:",
            reply_markup=main_menu
        )
    else:
        await callback.answer(
            text="❌ Siz hali ham kanalga a'zo bo'lmadingiz! Iltimos, avval kanalga a'zo bo'ling.",
            show_alert=True
        )

# =========================
# MA'LUMOTLAR MENU
# =========================

@dp.message(F.text == "📚 Ma'lumotlar")
async def information_menu(message: Message):
    await message.answer(
        "📚 Ma'lumotlar bo'limi",
        reply_markup=info_menu
    )

# =========================
# USTOZ HAQIDA
# =========================

@dp.message(F.text == "👨‍🏫 Ustoz haqida")
async def teacher_info(message: Message):
    if not os.path.exists("teacher.jpg"):
        await message.answer(
            "Ustoz haqida ma'lumot tez orada qo'shiladi."
        )
        return

    photo = FSInputFile("teacher.jpg")
    await message.answer_photo(
        photo=photo
    )

# =========================
# NATIJALAR
# =========================

@dp.message(F.text == "🏆 Natijalar")
async def results(message: Message):
    await message.answer(
        "🏆 O'quvchilar natijalari:\n"
        "https://t.me/+o8b2cf3rwAs1MzFi"
    )

# =========================
# ADMIN CONTACT
# =========================

@dp.message(F.text == "📞 Admin bilan bog'lanish")
async def admin_contact(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👨‍💻 Admin Profil",
                    url="https://t.me/Mahmudow_Z"
                )
            ]
        ]
    )

    await message.answer(
        "📩 Admin bilan bog'lanish uchun tugmani bosing 👇",
        reply_markup=keyboard
    )

# =========================
# VIDEO COURSES
# =========================

@dp.message(F.text == "🎥 Video Kurslar")
async def video_courses(message: Message):
    artikel_users.pop(message.from_user.id, None)
    await message.answer(
        "🎥 Kerakli kursni tanlang:",
        reply_markup=video_menu
    )

# =========================================================
# MY PROFILE
# =========================================================

@dp.message(F.text == "👤 Mening Profilim")
async def my_profile(message: Message):
    user = db_execute(
        """
        SELECT
            full_name, phone, course, total_score, daily_score, unlocked_level
        FROM users
        WHERE user_id = %s
        """,
        (message.from_user.id,),
        fetchone=True
    )

    if not user:
        await message.answer(
            "❌ Profil topilmadi."
        )
        return

    await message.answer(
        f"👤 Mening Profilim\n\n"
        f"👨 Ism: {user[0] or '-'}\n"
        f"📱 Telefon: {user[1] or '-'}\n"
        f"🎓 Kurs: {user[2] or '-'}\n\n"
        f"🏆 Umumiy XP: {user[3] or 0}\n"
        f"🔥 Bugungi XP: {user[4] or 0}\n"
        f"🔓 Daraja: {user[5] or 'A1'}",
        reply_markup=profile_keyboard()
    )
# =========================================================
# MY CERTIFICATES
# =========================================================

@dp.message(
    F.text == "🏅 Mening Sertifikatlarim"
)
async def my_certificates(
    message: Message
):

    pdf_path = (
        f"certificates/{message.from_user.id}.pdf"
    )

    if not os.path.exists(
        pdf_path
    ):

        await message.answer(

            "❌ Sizda hali sertifikat mavjud emas."

        )

        return

    await message.answer_document(

        document=FSInputFile(
            pdf_path
        ),

        caption=(

            "🏅 VIZU Academy Sertifikati\n\n"

            "📄 Sertifikatingiz qayta yuklandi."

        )

    )
# =========================================================
# CHANGE NAME START
# =========================================================

@dp.message(F.text == "✏️ Ism Familiyani o'zgartirish")
async def change_name_start(message: Message, state: FSMContext):
    await state.set_state(ProfileState.change_name)
    await message.answer(
        "✏️ Yangi ism va familiyangizni yuboring.\n\n"
        "Masalan:\n"
        "Zayniddin Mahmudov"
    )

# =========================================================
# CHANGE NAME SAVE
# =========================================================

@dp.message(StateFilter(ProfileState.change_name))
async def change_name_save(message: Message, state: FSMContext):
    full_name = message.text.strip()
    words = full_name.split()

    # Ism va familiya formati mukammal tekshiruvi
    if len(words) < 2 or any(len(w) < 2 for w in words):
        await message.answer(
            "❌ Iltimos, ism va familiyangizni to'liq va to'g'ri kiriting.\n"
            "Masalan: Zayniddin Mahmudov"
        )
        return

    db_execute(
        """
        UPDATE users
        SET full_name = %s
        WHERE user_id = %s
        """,
        (full_name, message.from_user.id)
    )

    await state.clear()
    await message.answer(
        "✅ Ism familiya yangilandi.",
        reply_markup=profile_keyboard()
    )
# =========================================================
# XP RATING
# =========================================================

@dp.message(F.text == "🔥 XP Reytingi")
async def xp_rating(message: Message):
    rows = db_execute(
        """
        SELECT
            full_name,
            total_score
        FROM users
        WHERE approved = 1
        ORDER BY total_score DESC
        LIMIT 100
        """,
        fetchall=True
    )

    if not rows:
        await message.answer("🏆 Hozircha reyting mavjud emas.")
        return

    text = "🏆 TOP 100 XP Reyting\n\n"
    medals = ["🥇", "🥈", "🥉"]

    for i, row in enumerate(rows, start=1):
        medal = medals[i - 1] if i <= 3 else f"{i}."
        name = row[0] or "Foydalanuvchi"
        score = row[1] or 0
        text += f"{medal} {name} — {score} XP\n"

    await message.answer(text)
# =========================================================
# VIZU CERTIFICATE HANDLERS
# =========================================================

@dp.message(
    F.text.in_([
        "🏅 VIZU-A1",
        "🏅 VIZU-A2",
        "🏅 VIZU-B1",
        "🏅 VIZU-B2",
        "🏅 VIZU-C1"
    ])
)
async def vizu_certificate_level_handler(
    message: Message
):

    certificate = message.text.replace(
        "🏅 ",
        ""
    )
    # =====================================
    # ONLY A1 AVAILABLE
    # =====================================

    if certificate != "VIZU-A1":

        await message.answer(

            f"🚧 {certificate}\n\n"

            f"⏳ Tez orada ishga tushiriladi.\n\n"

            f"📚 Hozircha faqat VIZU-A1 mavjud."

        )

        return
    # =====================================
    # ADMIN BYPASS
    # =====================================

    if message.from_user.id == ADMIN_ID:

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🚀 Mock Testni Boshlash",
                        callback_data=f"startvizu:{certificate}"
                    )
                ]
            ]
        )

        await message.answer(

            f"🏅 {certificate}\n\n"

            f"👨‍💼 Admin rejimi\n\n"

            f"🚀 Mock Testni boshlashingiz mumkin.",

            reply_markup=keyboard

        )

        return

    access_column = (
        certificate.lower()
        .replace("-", "_")
        + "_access"
    )

    row = db_execute(
        f"""
        SELECT {access_column}
        FROM users
        WHERE user_id = %s
        """,
        (message.from_user.id,),
        fetchone=True
    )

    has_access = (
        row
        and
        row[0] == 1
    )

    # =====================================
    # ACCESS BOR
    # =====================================

    if has_access:

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🚀 Mock Testni Boshlash",
                        callback_data=f"startvizu:{certificate}"
                    )
                ]
            ]
        )

        await message.answer(

            f"🏅 {certificate}\n\n"

            f"✅ Sizda ruxsat mavjud.\n\n"

            f"🚀 Mock Testni boshlashingiz mumkin.",

            reply_markup=keyboard

        )

    else:

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💳 To'lov qilish",
                        callback_data=f"vizupay:{certificate}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🎟 Golden Ticket",
                        callback_data=f"vizuticket:{certificate}"
                    )
                ]
            ]
        )

        await message.answer(

            f"🏅 {certificate}\n\n"

            f"❌ Sizda ruxsat mavjud emas.\n\n"

            f"💳 To'lov qiling yoki Golden Ticket yuboring.",

            reply_markup=keyboard

        )
    # =====================================
    # ACCESS OPEN
    # =====================================

    if has_access:

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🚀 Mock Testni Boshlash",
                        callback_data=f"startvizu:{certificate}"
                    )
                ]
            ]
        )

        await message.answer(

            f"🏅 {certificate}\n\n"

            f"✅ Sizning to'lovingiz tasdiqlangan.\n\n"

            f"🚀 Mock Testni boshlashingiz mumkin.",

            reply_markup=keyboard

        )

        return

    # =====================================
    # PAYMENT MENU
    # =====================================

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 To'lov Qilish",
                    callback_data=f"vizupay:{certificate}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎟 Golden Ticket",
                    callback_data=f"vizuticket:{certificate}"
                )
            ]
        ]
    )

    await message.answer(

        f"🏅 {certificate} Mock Test\n\n"

        f"📚 Lesen\n"
        f"🎧 Hören\n"
        f"✍️ Schreiben\n"
        f"🗣 Sprechen\n\n"

        f"💰 Imtihon narxi: 20 000 so'm\n\n"

        f"🎟 Golden Ticket egalari "
        f"imtihonni bepul topshirishlari mumkin.\n\n"

        f"👇 Davom etish usulini tanlang:",

        reply_markup=keyboard
    )
# =========================================================
# VIZU PAYMENT START
# =========================================================

@dp.callback_query(F.data.startswith("vizupay:"))
async def vizu_payment_start(
    callback: CallbackQuery,
    state: FSMContext
):

    level = callback.data.split(":")[1]

    await state.set_state(
        VizuCertificateState.waiting_for_payment_check
    )

    await state.update_data(
        certificate_level=level
    )

    await callback.message.answer(

        f"🏅 {level} Mock Test\n\n"

        f"💰 To'lov summasi: 20 000 so'm\n\n"

        f"💳 Karta raqami:\n"
        f"`9860 3501 4490 7192`\n\n"

        f"👤 Karta egasi:\n"
        f"Zayniddinkhuja Makhmudov\n\n"

        f"✅ To'lovni amalga oshirgach,\n"
        f"to'lov chekini rasm ko'rinishida yuboring.\n\n"

        f"⏳ Chek admin tomonidan tekshiriladi.",

        parse_mode="Markdown"

    )

    await callback.answer()
# =========================================================
# VIZU GOLDEN TICKET
# =========================================================

@dp.callback_query(F.data.startswith("vizuticket:"))
async def vizu_ticket_request(
    callback: CallbackQuery,
    state: FSMContext
):

    level = callback.data.split(":")[1]

    await state.update_data(
        certificate_level=level
    )

    await state.set_state(
        VizuCertificateState.waiting_for_ticket_photo
    )

    await callback.message.answer(

        "🎟 Golden Ticket\n\n"

        "Golden Ticket faqat oldin VIZU Academy video kurslarini "
        "xarid qilgan talabalarga admin tomonidan beriladi.\n\n"

        "Agar sizda Golden Ticket mavjud bo'lsa,\n"
        "uning rasmini yuboring.\n\n"

        "Agar sizda Golden Ticket bo'lmasa:\n"
        "@Mahmudow_Z bilan bog'laning.\n\n"

        "📸 Golden Ticket rasmini yuboring."

    )

    await callback.answer()
# =========================================================
# VIZU PAYMENT CHECK
# =========================================================

@dp.message(
    VizuCertificateState.waiting_for_payment_check,
    F.photo
)
async def vizu_payment_check(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    level = data.get(
        "certificate_level"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data=f"approvevizu:{message.from_user.id}:{level}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Rad etish",
                    callback_data=f"rejectvizu:{message.from_user.id}:{level}"
                )
            ]
        ]
    )

    await bot.send_photo(

        ADMIN_ID,

        photo=message.photo[-1].file_id,

        caption=(

            f"🏅 VIZU TO'LOV SO'ROVI\n\n"

            f"👤 {message.from_user.full_name}\n"

            f"🆔 {message.from_user.id}\n\n"

            f"🏅 Sertifikat: {level}\n"

            f"💰 20 000 so'm"

        ),

        reply_markup=keyboard

    )

    await message.answer(

        "✅ Chek adminga yuborildi.\n\n"

        "⏳ Tasdiqlanishini kuting."

    )

    await state.clear()

# =========================================================
# VIZU APPROVE / REJECT
# =========================================================

@dp.callback_query(
    F.data.startswith(("approvevizu:", "approveticket:"))
)
async def approve_handler(
    callback: CallbackQuery
):

    if callback.from_user.id != ADMIN_ID:
        return

    action, user_id, level = callback.data.split(":")

    user_id = int(user_id)

    is_ticket = (
        action == "approveticket"
    )

    access_column = (
        level.lower()
        .replace("-", "_")
        + "_access"
    )

    db_execute(
        f"""
        UPDATE users
        SET {access_column} = 1
        WHERE user_id = %s
        """,
        (user_id,)
    )

    db_execute(
        """
        INSERT INTO vizu_requests (
            user_id,
            level,
            status,
            approved_by
        )
        VALUES (%s, %s, 'approved', %s)
        """,
        (
            user_id,
            level,
            callback.from_user.id
        )
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Mock Testni Boshlash",
                    callback_data=f"startvizu:{level}"
                )
            ]
        ]
    )

    if is_ticket:

        text = (
            "🎟 Golden Ticket tasdiqlandi.\n\n"
            f"🏅 {level} Mock Test ochildi.\n\n"
            "🚀 Endi testni boshlashingiz mumkin."
        )

    else:

        text = (
            f"🎉 {level} Mock Test tasdiqlandi.\n\n"
            "✅ Endi siz imtihonni topshirishingiz mumkin."
        )

    try:

        await bot.send_message(
            user_id,
            text,
            reply_markup=keyboard
        )

    except Exception:
        pass

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await callback.answer(
        "✅ Tasdiqlandi"
    )


@dp.callback_query(
    F.data.startswith(("rejectvizu:", "rejectticket:"))
)
async def reject_handler(
    callback: CallbackQuery
):

    if callback.from_user.id != ADMIN_ID:
        return

    action, user_id, level = callback.data.split(":")

    user_id = int(user_id)

    is_ticket = (
        action == "approveticket"
    )

    if is_ticket:

        text = (
            f"❌ {level} uchun Golden Ticket "
            f"so'rovi rad etildi."
        )

    else:

        text = (
            f"❌ {level} uchun yuborilgan "
            f"to'lov tasdiqlanmadi.\n\n"
            f"Iltimos chekni qayta yuboring."
        )

    try:

        await bot.send_message(
            user_id,
            text
        )

    except Exception:
        pass

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await callback.answer(
        "❌ Rad etildi"
    )
# =========================================================
# GOLDEN TICKET PHOTO
# =========================================================

@dp.message(
    VizuCertificateState.waiting_for_ticket_photo,
    F.photo
)
async def process_golden_ticket(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    level = data.get(
        "certificate_level"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Golden Ticket Tasdiqlash",
                    callback_data=f"approveticket:{message.from_user.id}:{level}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Rad Etish",
                    callback_data=f"rejectticket:{message.from_user.id}:{level}"
                )
            ]
        ]
    )

    await bot.send_photo(

        ADMIN_ID,

        photo=message.photo[-1].file_id,

        caption=(

            f"🎟 GOLDEN TICKET SO'ROVI\n\n"

            f"👤 Ism: {message.from_user.full_name}\n"

            f"🆔 ID: {message.from_user.id}\n\n"

            f"🏅 Sertifikat: {level}\n\n"

            f"📸 Foydalanuvchi Golden Ticket rasmini yubordi."

        ),

        reply_markup=keyboard

    )

    await message.answer(

        "✅ Golden Ticket adminga yuborildi.\n\n"

        "⏳ Tasdiqlanishini kuting."

    )

    await state.clear()
# =========================================================
# START VIZU MOCK TEST
# =========================================================

@dp.callback_query(
    F.data.startswith("startvizu:")
)
async def start_vizu_test(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    level = callback.data.split(":")[1]

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Lesen")],
            [KeyboardButton(text="🎧 Hören")],
            [KeyboardButton(text="✍️ Schreiben")],
            [KeyboardButton(text="🗣 Sprechen")],
            [KeyboardButton(text="🏅 Zertifikat")],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )

    # =====================================
    # ADMIN BYPASS
    # =====================================

    if user_id == ADMIN_ID:

        vizu_mock_deadlines[user_id] = (
            datetime.now() +
            timedelta(minutes=80)
        )

        await callback.message.answer(

            f"🏅 {level} Mock Test\n\n"

            f"👨‍💼 Admin rejimi\n\n"

            f"⏱ Umumiy vaqt: 80 daqiqa\n\n"

            f"📚 Kerakli bo'limni tanlang:",

            reply_markup=keyboard

        )

        await callback.answer()

        return
    # =====================================
    # CERTIFICATE CHECK
    # =====================================

    certificate = db_execute(

        """
        SELECT created_at
        FROM certificates
        WHERE user_id = %s
        """,

        (
            user_id,
        ),

        fetchone=True

    )

    if certificate:

        await callback.message.answer(

            "🏅 Siz ushbu Mock Testni allaqachon topshirgansiz.\n\n"

            "📄 Sertifikatni quyidagi bo'limdan olishingiz mumkin:\n\n"

            "👤 Mening Profilim\n"
            "🏅 Mening Sertifikatlarim"

        )

        await callback.answer()

        return

    # =====================================
    # SAVE ATTEMPT
    # =====================================

    db_execute(

        """
        INSERT INTO vizu_attempts
        (
            user_id,
            level
        )
        VALUES
        (
            %s,
            %s
        )
        """,

        (
            user_id,
            level
        )

    )

    vizu_mock_deadlines[user_id] = (
        datetime.now() +
        timedelta(minutes=80)
    )

    await callback.message.answer(

        f"🏅 {level} Mock Test\n\n"

        f"⏱ Umumiy vaqt: 80 daqiqa\n\n"

        f"📚 Kerakli bo'limni tanlang:",

        reply_markup=keyboard

    )

    await callback.answer()
    # =====================================
    # START 80 MIN TIMER
    # =====================================

    vizu_mock_deadlines[user_id] = (

        datetime.now()

        +

        timedelta(
            minutes=80
        )

    )

    # =====================================
    # OPEN MOCK MENU
    # =====================================

    await callback.message.answer(

        f"🏅 {level} Mock Test\n\n"

        f"⏱ Umumiy vaqt: 80 daqiqa\n\n"

        f"📚 Lesen — 25 daqiqa\n"
        f"🎧 Hören — 20 daqiqa\n"
        f"✍️ Schreiben — 20 daqiqa\n"
        f"🗣 Sprechen — 15 daqiqa\n\n"

        f"⚠️ 80 daqiqa tugagach "
        f"test avtomatik yopiladi.\n\n"

        f"📚 Kerakli bo'limni tanlang:",

        reply_markup=keyboard

    )

    await callback.answer()
# =========================================================
# OPEN LESEN
# =========================================================

@dp.message(F.text == "📚 Lesen")
async def open_lesen(message: Message):

    user_id = message.from_user.id

    row = db_execute(
        """
        SELECT score
        FROM vizu_lesen_results
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    # =====================================
    # AGAR TOPSHIRILGAN BO'LSA
    # =====================================

    if row:

        score = row[0]

        percent = round(
            score * 100 / 25
        )

        await message.answer(

            f"📚 LESEN NATIJASI\n\n"

            f"🏅 Ball: {score}/25\n"

            f"📊 Natija: {percent}%\n\n"

            f"✅ Lesen yakunlangan.\n"

            f"❌ Qayta ishlash mumkin emas."

        )

        return

    # =====================================
    # AGAR TOPSHIRILMAGAN BO'LSA
    # =====================================

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Testni Boshlash",
                    callback_data="lesen_start"
                )
            ]
        ]
    )

    photo = FSInputFile(
        "VIZU-A1/Lesen-photo/lesen-intro.png"
    )

    await message.answer_photo(
        photo=photo,
        caption=(
            "📚 VIZU-A1 Lesen\n\n"
            "⏱ Davomiyligi: 25 daqiqa\n\n"
            "📖 Test 3 ta qismdan iborat.\n\n"
            "🚀 Tayyor bo'lsangiz boshlang."
        ),
        reply_markup=keyboard
    )
# =========================================================
# CHECK MOCK TIMER
# =========================================================

async def check_mock_timer(
    message
):

    user_id = message.from_user.id

    deadline = vizu_mock_deadlines.get(
        user_id
    )

    if not deadline:
        return True

    if datetime.now() > deadline:

        await message.answer(

            "⏰ Mock Test vaqti tugadi.\n\n"

            "❌ Test yakunlandi.\n\n"

            "🏅 Natijalar saqlanadi."

        )

        return False

    return True
# =========================================================
# START LESEN
# =========================================================

@dp.callback_query(
    F.data == "lesen_start"
)
async def start_lesen(
    callback: CallbackQuery,
    state: FSMContext
):

    # =====================================
    # MOCK TIMER CHECK
    # =====================================

    if not await check_mock_timer(
        callback.message
    ):
        await callback.answer()
        return

    user_id = callback.from_user.id

    row = db_execute(
        """
        SELECT *
        FROM vizu_lesen_results
        WHERE user_id = %s
        LIMIT 1
        """,
        (user_id,),
        fetchone=True
    )

    if row:

        score = row[1]

        await callback.message.answer(

            f"📚 LESEN NATIJASI\n\n"

            f"🏅 Ball: {score}/25\n\n"

            f"✅ Lesen bo'limi yakunlangan.\n"

            f"❌ Qayta topshirish mumkin emas."

        )

        await callback.answer()

        return

    vizu_lesen_progress[user_id] = {

        "index": 0,

        "score": 0

    }

    await state.set_state(
        VizuLesenState.solving
    )

    await send_lesen_question(
        callback.message,
        user_id
    )

    await callback.answer()
# =========================================================
# LESEN IMAGE
# =========================================================

def get_lesen_image(task):

    task = int(task)

    if task <= 2:
        return "VIZU-A1/Lesen-photo/lesen-teil1.1.png"

    elif task <= 5:
        return "VIZU-A1/Lesen-photo/lesen-teil1.2.png"

    elif task <= 11:
        return "VIZU-A1/Lesen-photo/lesen-teil2.png"

    elif task <= 13:
        return "VIZU-A1/Lesen-photo/lesen-teil3.1.png"

    else:
        return "VIZU-A1/Lesen-photo/lesen-teil3.2.png"
# =========================================================
# SEND LESEN QUESTION
# =========================================================

async def send_lesen_question(
    message,
    user_id
):

    progress = vizu_lesen_progress[user_id]

    index = progress["index"]

    total_questions = len(
        vizu_lesen_questions
    )

    # =====================================
    # FINISH TEST
    # =====================================

    if index >= total_questions:

        score = progress["score"]

        final_score = round(
            score * 25 /
            total_questions
        ) if total_questions > 0 else 0

        db_execute(
            """
            INSERT INTO
            vizu_lesen_results
            (
                user_id,
                score
            )
            VALUES
            (
                %s,
                %s
            )
            ON CONFLICT (user_id)
            DO UPDATE SET
                score = EXCLUDED.score,
                completed_at = NOW()
            """,
            (
                user_id,
                final_score
            )
        )

        await message.answer(

            f"📚 LESEN YAKUNLANDI\n\n"

            f"✅ To'g'ri javoblar: "
            f"{score}/{total_questions}\n"

            f"❌ Noto'g'ri javoblar: "
            f"{total_questions - score}\n\n"

            f"🏅 Ball: {final_score}/25"

        )

        vizu_lesen_progress.pop(
            user_id,
            None
        )

        return

    row = vizu_lesen_questions[index]

    task = row["task"]

    question = row["question"]

    image_path = get_lesen_image(task)

    # =====================================
    # TEIL 2
    # =====================================

    if 6 <= int(task) <= 11:

        options = [
            "6",
            "7",
            "8",
            "9",
            "10",
            "11"
        ]

        random.shuffle(
            options
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=opt,
                        callback_data=f"lesen:{opt}"
                    )
                ]
                for opt in options
            ]
        )

    # =====================================
    # TEIL 1 + TEIL 3
    # =====================================

    else:

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Richtig",
                        callback_data="lesen:Richtig"
                    ),
                    InlineKeyboardButton(
                        text="❌ Falsch",
                        callback_data="lesen:Falsch"
                    )
                ]
            ]
        )

    await message.answer_photo(

        photo=FSInputFile(
            image_path
        ),

        caption=(

            f"📚 A1 Lesen\n\n"

            f"📝 Savol {task}/{total_questions}\n\n"

            f"{question}"

        ),

        reply_markup=keyboard

    )
# =========================================================
# LESEN ANSWER
# =========================================================

@dp.callback_query(
    VizuLesenState.solving,
    F.data.startswith("lesen:")
)
async def lesen_answer(
    callback: CallbackQuery,
    state: FSMContext
):

    user_id = callback.from_user.id

    progress = vizu_lesen_progress.get(
        user_id
    )

    if not progress:
        await callback.answer()
        return

    index = progress["index"]

    row = vizu_lesen_questions[index]

    user_answer = callback.data.split(":")[1]

    correct_answer = row["correct"]

    if user_answer == correct_answer:

        progress["score"] += 1

    progress["index"] += 1

    await callback.answer()

    await send_lesen_question(
        callback.message,
        user_id
    )
# =========================================================
# OPEN HOREN
# =========================================================

@dp.message(F.text == "🎧 Hören")
async def open_horen(message: Message):

    user_id = message.from_user.id

    row = db_execute(
        """
        SELECT score
        FROM vizu_horen_results
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    # =====================================
    # AGAR TOPSHIRILGAN BO'LSA
    # =====================================

    if row:

        score = row[0]

        percent = round(
            score * 100 / 25
        )

        await message.answer(

            f"🎧 HÖREN NATIJASI\n\n"

            f"🏅 Ball: {score}/25\n"

            f"📊 Natija: {percent}%\n\n"

            f"✅ Hören yakunlangan.\n"

            f"❌ Qayta ishlash mumkin emas."

        )

        return

    # =====================================
    # AGAR TOPSHIRILMAGAN BO'LSA
    # =====================================

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Testni Boshlash",
                    callback_data="horen_start"
                )
            ]
        ]
    )

    photo = FSInputFile(
        "VIZU-A1/Hören-photo/hören-intro.png"
    )

    await message.answer_photo(
        photo=photo,
        caption=(

            "🎧 A1 Hören\n\n"

            "⏱ Davomiyligi: 20 daqiqa\n\n"

            "🚀 Tayyor bo'lsangiz boshlang."

        ),
        reply_markup=keyboard
    )
# =========================================================
# START HOREN
# =========================================================

@dp.callback_query(
    F.data == "horen_start",
    StateFilter("*")
)
async def start_horen(
    callback: CallbackQuery,
    state: FSMContext
):

    # =====================================
    # MOCK TIMER CHECK
    # =====================================

    if not await check_mock_timer(
        callback.message
    ):
        await callback.answer()
        return

    user_id = callback.from_user.id

    await state.clear()

    # =====================================
    # ADMIN BYPASS
    # =====================================

    if user_id == ADMIN_ID:

        vizu_horen_progress[user_id] = {

            "index": 0,
            "score": 0

        }

        await state.set_state(
            VizuHorenState.solving
        )

        await callback.answer()

        await send_horen_question(
            callback.message,
            user_id
        )

        return

    # =====================================
    # CHECK RESULT
    # =====================================

    row = db_execute(
        """
        SELECT score
        FROM vizu_horen_results
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    if row:

        score = row[0]

        await callback.message.answer(

            f"🎧 HÖREN NATIJASI\n\n"

            f"🏅 Ball: {score}/25\n\n"

            f"✅ Hören bo'limi yakunlangan.\n"

            f"❌ Qayta topshirish mumkin emas."

        )

        await callback.answer()

        return

    # =====================================
    # START TEST
    # =====================================

    vizu_horen_progress[user_id] = {

        "index": 0,
        "score": 0

    }

    await state.set_state(
        VizuHorenState.solving
    )

    await callback.answer()

    await send_horen_question(
        callback.message,
        user_id
    )
# =========================================================
# HOREN AUDIO & IMAGE HELPERS
# =========================================================

def get_horen_audio(task):
    task = int(task)
    if task <= 6: return "VIZU-A1/Hören-audio/hören-teil1.mp3"
    elif task <= 10: return "VIZU-A1/Hören-audio/hören-teil2.mp3"
    else: return "VIZU-A1/Hören-audio/hören-teil3.mp3"

def get_horen_image(task):
    task = int(task)
    if task <= 3: return "VIZU-A1/Hören-photo/hören-teil1.png"
    elif task <= 6: return "VIZU-A1/Hören-photo/hören-teil1.2.png"
    elif task <= 10: return "VIZU-A1/Hören-photo/hören-teil2.png"
    else: return "VIZU-A1/Hören-photo/hören-teil3.png"
# =========================================================
# SEND HOREN QUESTION
# =========================================================

async def send_horen_question(
    message,
    user_id
):

    progress = vizu_horen_progress.get(
        user_id
    )

    if not progress:
        return

    index = progress["index"]

    total_questions = len(
        vizu_horen_questions
    )

    # =====================================
    # FINISH TEST
    # =====================================

    if index >= total_questions:

        correct_answers = progress["score"]

        final_score = round(
            correct_answers * 25 /
            total_questions
        ) if total_questions > 0 else 0

        db_execute(
            """
            INSERT INTO
            vizu_horen_results
            (
                user_id,
                score
            )
            VALUES
            (
                %s,
                %s
            )
            ON CONFLICT (user_id)
            DO UPDATE SET
                score = EXCLUDED.score,
                completed_at = NOW()
            """,
            (
                user_id,
                final_score
            )
        )

        await message.answer(

            f"🎧 HÖREN YAKUNLANDI\n\n"

            f"✅ To'g'ri javoblar: "
            f"{correct_answers}/{total_questions}\n"

            f"❌ Noto'g'ri javoblar: "
            f"{total_questions - correct_answers}\n\n"

            f"🏅 Ball: {final_score}/25"

        )

        vizu_horen_progress.pop(
            user_id,
            None
        )

        return

    row = vizu_horen_questions[index]

    task = row["task"]

    question = row["question"]

    # =====================================
    # AUDIO FROM CHANNEL
    # =====================================

    try:

        if int(task) <= 6:

            await bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=-1003916093529,
                message_id=6
            )

        elif int(task) <= 10:

            await bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=-1003916093529,
                message_id=7
            )

        else:

            await bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=-1003916093529,
                message_id=8
            )

    except Exception as e:

        logger.error(
            f"HOREN AUDIO ERROR: {e}"
        )

    # =====================================
    # KEYBOARD
    # =====================================

    if 7 <= int(task) <= 10:

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Richtig",
                        callback_data="horen:Richtig"
                    ),
                    InlineKeyboardButton(
                        text="❌ Falsch",
                        callback_data="horen:Falsch"
                    )
                ]
            ]
        )

    else:

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="A",
                        callback_data="horen:a"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="B",
                        callback_data="horen:b"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="C",
                        callback_data="horen:c"
                    )
                ]
            ]
        )

    await message.answer_photo(

        photo=FSInputFile(
            get_horen_image(task)
        ),

        caption=(

            f"🎧 A1 Hören\n\n"

            f"📝 Savol {task}/{total_questions}\n\n"

            f"{question}"

        ),

        reply_markup=keyboard

    )
# =========================================================
# HOREN ANSWER
# =========================================================

@dp.callback_query(VizuHorenState.solving, F.data.startswith("horen:"))
async def horen_answer(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    progress = vizu_horen_progress.get(user_id)

    if not progress: return

    index = progress["index"]
    row = vizu_horen_questions[index]
    
    user_answer = callback.data.split(":")[1]
    if user_answer.lower() == row["correct"].lower():
        progress["score"] += 1
        await callback.answer("✅")
    else:
        await callback.answer(f"❌ {row['correct'].upper()}", show_alert=True)

    progress["index"] += 1
    if progress["index"] >= len(vizu_horen_questions):
        await state.clear()

    await send_horen_question(callback.message, user_id)
# =========================================================
# OPEN SCHREIBEN
# =========================================================

@dp.message(
    F.text == "✍️ Schreiben"
)
async def open_schreiben(
    message: Message
):

    user_id = message.from_user.id

    row = db_execute(
        """
        SELECT score
        FROM vizu_schreiben_results
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    # =====================================
    # AGAR TOPSHIRILGAN BO'LSA
    # =====================================

    if row:

        score = row[0]

        await message.answer(

            f"✍️ SCHREIBEN NATIJASI\n\n"

            f"🏅 Ball: {score}/25\n\n"

            f"✅ Schreiben yakunlangan.\n"

            f"❌ Qayta topshirish mumkin emas."

        )

        return

    # =====================================
    # AGAR TOPSHIRILMAGAN BO'LSA
    # =====================================

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Boshlash",
                    callback_data="schreiben_start"
                )
            ]
        ]
    )

    await message.answer_photo(

        photo=FSInputFile(
            "VIZU-A1/schreiben-photo/schreiben-intro.png"
        ),

        caption=(

            "✍️ A1 Schreiben\n\n"

            "⏱ Davomiyligi: 20 daqiqa\n\n"

            "📝 2 ta vazifa mavjud."

        ),

        reply_markup=keyboard

    )

# =========================================================
# START SCHREIBEN
# =========================================================

@dp.callback_query(
    F.data == "schreiben_start"
)
async def start_schreiben(
    callback: CallbackQuery,
    state: FSMContext
):

    # =====================================
    # MOCK TIMER CHECK
    # =====================================

    if not await check_mock_timer(
        callback.message
    ):
        await callback.answer()
        return

    user_id = callback.from_user.id

    row = db_execute(
        """
        SELECT score
        FROM vizu_schreiben_results
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    # =====================================
    # ALREADY COMPLETED
    # =====================================

    if row:

        score = row[0]

        await callback.message.answer(

            f"✍️ SCHREIBEN NATIJASI\n\n"

            f"🏅 Ball: {score}/25\n\n"

            f"✅ Schreiben bo'limi yakunlangan.\n"

            f"❌ Qayta topshirish mumkin emas."

        )

        await callback.answer()

        return

    # =====================================
    # START TEST
    # =====================================

    await state.set_state(
        VizuSchreibenState.teil1
    )

    await callback.message.answer_photo(

        photo=FSInputFile(
            "VIZU-A1/schreiben-photo/schreiben-teil1.png"
        ),

        caption=(

            "✍️ Schreiben Teil 1\n\n"

            "📤 Javobingizni yuboring."

        )

    )

    await callback.answer()
# =========================================================
# SCHREIBEN TEIL 1
# =========================================================

@dp.message(
    VizuSchreibenState.teil1
)
async def schreiben_teil1(
    message: Message,
    state: FSMContext
):

    # Teil 1 javobini admin kanalga yuborish

    await bot.send_message(

        ADMIN_CHANNEL_ID,

        f"✍️ SCHREIBEN TEIL 1\n\n"

        f"👤 {message.from_user.full_name}\n"

        f"🆔 {message.from_user.id}"

    )

    if message.photo or message.document:

        await bot.forward_message(
            chat_id=ADMIN_CHANNEL_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )

    elif message.text:

        await bot.send_message(
            ADMIN_CHANNEL_ID,
            f"📝 TEIL 1 JAVOB:\n\n{message.text}"
        )

    await state.set_state(
        VizuSchreibenState.teil2
    )

    await message.answer_photo(

        photo=FSInputFile(
            "VIZU-A1/schreiben-photo/schreiben-teil2.png"
        ),

        caption=(
            "✍️ Schreiben Teil 2\n\n"
            "📤 Javobingizni yuboring."
        )

    )
# =========================================================
# SCHREIBEN TEIL 2
# =========================================================

@dp.message(
    VizuSchreibenState.teil2
)
async def schreiben_teil2(
    message: Message,
    state: FSMContext
):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Ball Berish",
                    callback_data=
                    f"schreiben_rate:{message.from_user.id}"
                )
            ]
        ]
    )

    try:

        await bot.send_message(

            ADMIN_CHANNEL_ID,

            f"✍️ SCHREIBEN\n\n"

            f"👤 {message.from_user.full_name}\n"

            f"🆔 {message.from_user.id}\n\n"

            f"📌 Teil 1 va Teil 2 topshirildi.",

            reply_markup=keyboard

        )

        # Agar foydalanuvchi rasm yuborgan bo'lsa

        if message.photo:

            await bot.forward_message(

                chat_id=ADMIN_CHANNEL_ID,

                from_chat_id=message.chat.id,

                message_id=message.message_id

            )

        # Agar document yuborgan bo'lsa

        elif message.document:

            await bot.forward_message(

                chat_id=ADMIN_CHANNEL_ID,

                from_chat_id=message.chat.id,

                message_id=message.message_id

            )

        # Agar oddiy matn yuborgan bo'lsa

        elif message.text:

            await bot.send_message(

                ADMIN_CHANNEL_ID,

                f"📝 JAVOB:\n\n{message.text}"

            )

    except Exception as e:

        logger.error(
            f"SCHREIBEN SEND ERROR: {e}"
        )

        await message.answer(
            "❌ Admin kanalga yuborishda xatolik."
        )

        return

    await message.answer(

        "✅ Schreiben topshirildi.\n\n"

        "⏳ Admin tekshirgandan so'ng natija chiqariladi."

    )

    await state.clear()
# =========================================================
# SCHREIBEN RATE BUTTON
# =========================================================

@dp.callback_query(
    F.data.startswith("schreiben_rate:")
)
async def schreiben_rate_button(
    callback: CallbackQuery
):

    if callback.from_user.id != ADMIN_ID:
        return

    user_id = callback.data.split(":")[1]

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=str(i),
                    callback_data=f"schreiben_score:{user_id}:{i}"
                )
                for i in range(10, 18)
            ],
            [
                InlineKeyboardButton(
                    text=str(i),
                    callback_data=f"schreiben_score:{user_id}:{i}"
                )
                for i in range(18, 26)
            ]
        ]
    )

    await callback.message.answer(

        "🏅 Schreiben ballini tanlang:",

        reply_markup=keyboard

    )

    await callback.answer()

# =========================================================
# SCHREIBEN SAVE SCORE
# =========================================================

@dp.callback_query(
    F.data.startswith("schreiben_score:")
)
async def schreiben_save_score(
    callback: CallbackQuery
):

    if callback.from_user.id != ADMIN_ID:
        return

    _, user_id, score = callback.data.split(":")

    user_id = int(user_id)
    score = int(score)

    db_execute(
        """
        INSERT INTO
        vizu_schreiben_results
        (
            user_id,
            score
        )
        VALUES
        (
            %s,
            %s
        )
        ON CONFLICT (user_id)
        DO UPDATE SET
            score = EXCLUDED.score,
            completed_at = NOW()
        """,
        (
            user_id,
            score
        )
    )

    try:

        await bot.send_message(

            user_id,

            f"✍️ Schreiben baholandi.\n\n"

            f"🏅 Ball: {score}/25"

        )

    except Exception as e:

        logger.error(
            f"SCHREIBEN RESULT ERROR: {e}"
        )

    await callback.message.answer(

        f"✅ Ball saqlandi.\n\n"

        f"👤 User: {user_id}\n"

        f"🏅 Ball: {score}/25"

    )

    await callback.answer(
        "✅ Ball saqlandi"
    )

# =========================================================
# OPEN SPRECHEN
# =========================================================

@dp.message(
    F.text == "🗣 Sprechen"
)
async def open_sprechen(
    message: Message
):

    user_id = message.from_user.id

    row = db_execute(
        """
        SELECT score
        FROM vizu_sprechen_results
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    if row:

        score = row[0]

        await message.answer(

            f"🗣 SPRECHEN NATIJASI\n\n"

            f"🏅 Ball: {score}/25\n\n"

            f"❌ Qayta topshirish mumkin emas."

        )

        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Boshlash",
                    callback_data="sprechen_start"
                )
            ]
        ]
    )

    await message.answer_photo(

        photo=FSInputFile(
            "VIZU-A1/sprechen-photo/sprechen-intro.png"
        ),

        caption=(

            "🗣 A1 Sprechen\n\n"

            "⏱ Davomiyligi: 15 daqiqa\n\n"

            "📌 5 ta topshiriq mavjud."

        ),

        reply_markup=keyboard

    )
# =========================================================
# START SPRECHEN
# =========================================================

@dp.callback_query(
    F.data == "sprechen_start"
)
async def start_sprechen(
    callback: CallbackQuery,
    state: FSMContext
):

    # =====================================
    # MOCK TIMER CHECK
    # =====================================

    if not await check_mock_timer(
        callback.message
    ):
        await callback.answer()
        return

    user_id = callback.from_user.id

    row = db_execute(
        """
        SELECT score
        FROM vizu_sprechen_results
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    # =====================================
    # ALREADY COMPLETED
    # =====================================

    if row:

        score = row[0]

        await callback.message.answer(

            f"🗣 SPRECHEN NATIJASI\n\n"

            f"🏅 Ball: {score}/25\n\n"

            f"✅ Sprechen bo'limi yakunlangan.\n"

            f"❌ Qayta topshirish mumkin emas."

        )

        await callback.answer()

        return

    # =====================================
    # START TEST
    # =====================================

    await state.set_state(
        VizuSprechenState.teil1
    )

    await callback.message.answer_photo(

        photo=FSInputFile(
            "VIZU-A1/sprechen-photo/sprechen-teil1.png"
        ),

        caption=(

            "🗣 Sprechen Teil 1\n\n"

            "🇩🇪 Stellen Sie sich vor.\n\n"

            "📌 Name\n"
            "📌 Alter\n"
            "📌 Land\n"
            "📌 Wohnort\n"
            "📌 Sprachen\n"
            "📌 Beruf\n"
            "📌 Hobby\n\n"

            "🎤 1 daqiqalik audio yuboring."

        )

    )

    await callback.answer()
# =========================================================
# SPRECHEN TEIL 1
# =========================================================

@dp.message(
    VizuSprechenState.teil1
)
async def sprechen_teil1(
    message: Message,
    state: FSMContext
):

    if not await check_mock_timer(message):
        return

    if not (
        message.voice
        or message.audio
        or message.video_note
    ):
        await message.answer(
            "🎤 Iltimos audio yuboring."
        )
        return

    await state.update_data(
        teil1_message_id=message.message_id
    )

    await state.set_state(
        VizuSprechenState.teil21
    )

    await message.answer_photo(
        photo=FSInputFile(
            "VIZU-A1/sprechen-photo/sprechen-teil2.1.png"
        ),
        caption=(
            "🗣 Sprechen Teil 2.1\n\n"
            "🇩🇪 Bilden Sie Fragen mit den Wörtern.\n\n"
            "🎤 Barcha savollarni bitta audio qilib yuboring."
        )
    )


# =========================================================
# SPRECHEN TEIL 2.1
# =========================================================

@dp.message(
    VizuSprechenState.teil21
)
async def sprechen_teil21(
    message: Message,
    state: FSMContext
):

    if not await check_mock_timer(message):
        return

    if not (
        message.voice
        or message.audio
        or message.video_note
    ):
        await message.answer(
            "🎤 Iltimos audio yuboring."
        )
        return

    await state.update_data(
        teil21_message_id=message.message_id
    )

    await state.set_state(
        VizuSprechenState.teil22
    )

    await message.answer_photo(
        photo=FSInputFile(
            "VIZU-A1/sprechen-photo/sprechen-teil2.2.png"
        ),
        caption=(
            "🗣 Sprechen Teil 2.2\n\n"
            "🇩🇪 Beantworten Sie die Fragen.\n\n"
            "🎤 Barcha javoblarni bitta audio qilib yuboring."
        )
    )


# =========================================================
# SPRECHEN TEIL 2.2
# =========================================================

@dp.message(
    VizuSprechenState.teil22
)
async def sprechen_teil22(
    message: Message,
    state: FSMContext
):

    if not await check_mock_timer(message):
        return

    if not (
        message.voice
        or message.audio
        or message.video_note
    ):
        await message.answer(
            "🎤 Iltimos audio yuboring."
        )
        return

    await state.update_data(
        teil22_message_id=message.message_id
    )

    await state.set_state(
        VizuSprechenState.teil31
    )

    await message.answer_photo(
        photo=FSInputFile(
            "VIZU-A1/sprechen-photo/sprechen-teil3.1.png"
        ),
        caption=(
            "🗣 Sprechen Teil 3.1\n\n"
            "🇩🇪 Bilden Sie Bitten.\n\n"
            "💡 Bitte können Sie mir Salz geben?\n\n"
            "🎤 Bitta audio yuboring."
        )
    )


# =========================================================
# SPRECHEN TEIL 3.1
# =========================================================

@dp.message(
    VizuSprechenState.teil31
)
async def sprechen_teil31(
    message: Message,
    state: FSMContext
):

    if not await check_mock_timer(message):
        return

    if not (
        message.voice
        or message.audio
        or message.video_note
    ):
        await message.answer(
            "🎤 Iltimos audio yuboring."
        )
        return

    await state.update_data(
        teil31_message_id=message.message_id
    )

    await state.set_state(
        VizuSprechenState.teil32
    )

    await message.answer_photo(
        photo=FSInputFile(
            "VIZU-A1/sprechen-photo/sprechen-teil3.2.png"
        ),
        caption=(
            "🗣 Sprechen Teil 3.2\n\n"
            "🇩🇪 Reagieren Sie auf die Bitten.\n\n"
            "💡 Ja, gern.\n"
            "💡 Nein, leider nicht.\n\n"
            "🎤 Bitta audio yuboring."
        )
    )
# =========================================================
# SPRECHEN TEIL 3.2
# =========================================================

@dp.message(
    VizuSprechenState.teil32
)
async def sprechen_teil32(
    message: Message,
    state: FSMContext
):

    if not await check_mock_timer(
        message
    ):
        return

    if not (
        message.voice
        or message.audio
        or message.video_note
    ):
        await message.answer(
            "🎤 Iltimos audio yuboring."
        )
        return

    await state.update_data(
        teil32_message_id=message.message_id
    )

    data = await state.get_data()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Ball Berish",
                    callback_data=
                    f"sprechen_rate:{message.from_user.id}"
                )
            ]
        ]
    )

    try:

        await bot.send_message(

            ADMIN_CHANNEL_ID,

            f"🗣 SPRECHEN\n\n"

            f"👤 {message.from_user.full_name}\n"

            f"🆔 {message.from_user.id}\n\n"

            f"📌 Barcha Teil javoblari yuborildi.",

            reply_markup=keyboard

        )

        for msg_id in [

            data.get("teil1_message_id"),
            data.get("teil21_message_id"),
            data.get("teil22_message_id"),
            data.get("teil31_message_id"),
            data.get("teil32_message_id")

        ]:

            if not msg_id:
                continue

            await bot.forward_message(

                chat_id=ADMIN_CHANNEL_ID,

                from_chat_id=message.chat.id,

                message_id=msg_id

            )

    except Exception as e:

        logger.error(
            f"SPRECHEN SEND ERROR: {e}"
        )

        await message.answer(

            "❌ Admin kanalga yuborilmadi.\n\n"

            f"Xatolik: {e}"

        )

        return

    await message.answer(

        "✅ Sprechen topshirildi.\n\n"

        "📨 Barcha javoblaringiz adminga yuborildi.\n\n"

        "⏳ Baholash kutilmoqda.\n\n"

        "🏅 Ball qo'yilgandan so'ng sizga xabar yuboriladi."

    )

    await state.clear()
# =========================================================
# SPRECHEN RATE BUTTON
# =========================================================

@dp.callback_query(
    F.data.startswith("sprechen_rate:")
)
async def sprechen_rate_button(
    callback: CallbackQuery
):

    if callback.message.chat.id != ADMIN_CHANNEL_ID:
        return

    if callback.from_user.id != ADMIN_ID:
        return

    user_id = callback.data.split(":")[1]

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=str(i),
                    callback_data=
                    f"sprechen_score:{user_id}:{i}"
                )
                for i in range(10, 18)
            ],
            [
                InlineKeyboardButton(
                    text=str(i),
                    callback_data=
                    f"sprechen_score:{user_id}:{i}"
                )
                for i in range(18, 26)
            ]
        ]
    )

    await callback.message.answer(

        "🏅 Sprechen ballini tanlang:",

        reply_markup=keyboard

    )

    await callback.answer()
# =========================================================
# SPRECHEN SAVE SCORE
# =========================================================

@dp.callback_query(
    F.data.startswith("sprechen_score:")
)
async def sprechen_save_score(
    callback: CallbackQuery
):

    if callback.message.chat.id != ADMIN_CHANNEL_ID:
        return

    if callback.from_user.id != ADMIN_ID:
        return

    _, user_id, score = callback.data.split(":")

    user_id = int(user_id)

    score = int(score)

    db_execute(
        """
        INSERT INTO
        vizu_sprechen_results
        (
            user_id,
            score
        )
        VALUES
        (
            %s,
            %s
        )
        ON CONFLICT (user_id)
        DO UPDATE SET
            score = EXCLUDED.score,
            completed_at = NOW()
        """,
        (
            user_id,
            score
        )
    )

    try:

        await bot.send_message(

            user_id,

            f"🗣 Sprechen baholandi.\n\n"

            f"🏅 Ball: {score}/25"

        )

    except Exception as e:

        logger.error(
            f"SPRECHEN RESULT ERROR: {e}"
        )

    await callback.message.answer(

        f"✅ Ball saqlandi.\n\n"

        f"👤 User: {user_id}\n"

        f"🏅 Ball: {score}/25"

    )

    await callback.answer(
        "✅ Ball saqlandi"
    )
# =========================================================
# ZERTIFIKAT
# =========================================================

@dp.message(
    F.text == "🏅 Zertifikat"
)
async def get_certificate(
    message: Message
):

    user_id = message.from_user.id

    lesen = db_execute(
        """
        SELECT score
        FROM vizu_lesen_results
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    horen = db_execute(
        """
        SELECT score
        FROM vizu_horen_results
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    schreiben = db_execute(
        """
        SELECT score
        FROM vizu_schreiben_results
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    sprechen = db_execute(
        """
        SELECT score
        FROM vizu_sprechen_results
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    if not all([
        lesen,
        horen,
        schreiben,
        sprechen
    ]):

        await message.answer(

            "❌ Sertifikat olish uchun barcha bo'limlarni yakunlang.\n\n"

            "📚 Lesen\n"
            "🎧 Hören\n"
            "✍️ Schreiben\n"
            "🗣 Sprechen"

        )

        return

    lesen_score = int(lesen[0])
    horen_score = int(horen[0])
    schreiben_score = int(schreiben[0])
    sprechen_score = int(sprechen[0])

    total_score = (
        lesen_score +
        horen_score +
        schreiben_score +
        sprechen_score
    )

    certificate_path = generate_vizu_certificate(

        user_id=user_id,

        full_name=message.from_user.full_name,

        lesen=lesen_score,

        horen=horen_score,

        schreiben=schreiben_score,

        sprechen=sprechen_score

    )

    if not certificate_path:

        await message.answer(
            "❌ Sertifikat yaratishda xatolik yuz berdi."
        )

        return

    status = (
        "✅ BESTANDEN"
        if total_score >= 60
        else "❌ NICHT BESTANDEN"
    )
    # =====================================
    # SEND PDF TO USER
    # =====================================

    await message.answer_document(

        document=FSInputFile(
            certificate_path
        ),

        caption=(

            "🏅 VIZU A1 MOCK TEST\n\n"

            f"📚 Lesen: {lesen_score}/25\n"
            f"🎧 Hören: {horen_score}/25\n"
            f"✍️ Schreiben: {schreiben_score}/25\n"
            f"🗣 Sprechen: {sprechen_score}/25\n\n"

            f"🏆 Gesamt: {total_score}/100\n\n"

            f"{status}"

        )

    )
    # =====================================
    # SAVE CERTIFICATE
    # =====================================

    db_execute(

        """
        INSERT INTO certificates
        (
            user_id,
            total_score
        )
        VALUES
        (
            %s,
            %s
        )

        ON CONFLICT (user_id)

        DO UPDATE SET

            total_score = EXCLUDED.total_score,

            created_at = NOW()
        """,

        (
            user_id,
            total_score
        )

    )
    # =====================================
    # SEND PDF TO ADMIN CHANNEL
    # =====================================

    try:

        await bot.send_document(

            chat_id=ADMIN_CHANNEL_ID,

            document=FSInputFile(
                certificate_path
            ),

            caption=(

                "🏅 YANGI SERTIFIKAT\n\n"

                f"👤 {message.from_user.full_name}\n"

                f"🆔 {user_id}\n\n"

                f"📚 Lesen: {lesen_score}/25\n"

                f"🎧 Hören: {horen_score}/25\n"

                f"✍️ Schreiben: {schreiben_score}/25\n"

                f"🗣 Sprechen: {sprechen_score}/25\n\n"

                f"🏆 Gesamt: {total_score}/100\n\n"

                f"{status}"

            )

        )

    except Exception as e:

        logger.error(
            f"CERTIFICATE ADMIN SEND ERROR: {e}"
        )
        await message.answer(

        "🏠 Asosiy menyuga qaytdingiz.",

        reply_markup=main_menu

    )
# =========================================================
# CERTIFICATE GRADE
# =========================================================

def get_certificate_grade(score):

    if score >= 22:
        return "Sehr gut"

    elif score >= 19:
        return "Gut"

    elif score >= 16:
        return "Befriedigend"

    elif score >= 10:
        return "Ausreichend"

    return "Nicht bestanden"
# =========================================================
# GENERATE VIZU CERTIFICATE
# =========================================================

def generate_vizu_certificate(
    user_id,
    full_name,
    lesen,
    horen,
    schreiben,
    sprechen
):

    try:

        total = (
            lesen +
            horen +
            schreiben +
            sprechen
        )

        certificate_id = (
            f"VIZU-A1-{str(user_id)[-6:]}"
        )

        horen_grade = get_certificate_grade(
            horen
        )

        lesen_grade = get_certificate_grade(
            lesen
        )

        schreiben_grade = get_certificate_grade(
            schreiben
        )

        sprechen_grade = get_certificate_grade(
            sprechen
        )

        total_grade = get_certificate_grade(
            round(total / 4)
        )

        os.makedirs(
            "certificates",
            exist_ok=True
        )

        pdf_path = (
            f"certificates/{user_id}.pdf"
        )

        doc = SimpleDocTemplate(
            pdf_path,
            topMargin=0,
            bottomMargin=0,
            leftMargin=40,
            rightMargin=40
        )

        styles = getSampleStyleSheet()

        elements = []

        # =====================================
        # HEADER
        # =====================================

        elements.append(

            RLImage(

                "VIZU-A1/top_header.png",

                width=520,

                height=250

            )

        )

        elements.append(
            Spacer(1, 20)
        )

        # =====================================
        # NAME
        # =====================================

        elements.append(

            Paragraph(

                f"<para align='center'><b>{full_name}</b></para>",

                styles["Title"]

            )

        )

        elements.append(
            Spacer(1, 20)
        )

        # =====================================
        # TABLE
        # =====================================

        table_data = [

            [
                "Teil",
                "Punkte",
                "Bewertung"
            ],

            [
                "Hören",
                f"{horen}/25",
                horen_grade
            ],

            [
                "Lesen",
                f"{lesen}/25",
                lesen_grade
            ],

            [
                "Schreiben",
                f"{schreiben}/25",
                schreiben_grade
            ],

            [
                "Sprechen",
                f"{sprechen}/25",
                sprechen_grade
            ],

            [
                "Gesamt",
                f"{total}/100",
                total_grade
            ]

        ]

        table = Table(

            table_data,

            colWidths=[
                130,
                120,
                180
            ]

        )

        table.setStyle(

            TableStyle([

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.black
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER"
                )

            ])

        )

        elements.append(
            table
        )

        elements.append(
            Spacer(1, 20)
        )

        # =====================================
        # CERTIFICATE INFO
        # =====================================

        elements.append(

            Paragraph(

                f"<b>Zertifikat-ID:</b> {certificate_id}",

                styles["Normal"]

            )

        )

        elements.append(

            Paragraph(

                f"<b>Datum:</b> "
                f"{datetime.now().strftime('%d.%m.%Y')}",

                styles["Normal"]

            )

        )

        elements.append(
            Spacer(1, 20)
        )

        # =====================================
        # FOOTER
        # =====================================

        elements.append(

            RLImage(

                "VIZU-A1/bottom_footer.png",

                width=520,

                height=260

            )

        )

        doc.build(
            elements
        )

        logger.info(
            f"Certificate created: {pdf_path}"
        )

        return pdf_path

    except Exception as e:

        logger.error(
            f"CERTIFICATE ERROR: {e}"
        )

        return None

# =========================
# SAMPLE LESSON
# =========================

@dp.message(F.text == "🎬 Bepul Namuna Darslar")
async def sample_lesson(message: Message):
    await message.answer(
        "🎬 Bepul Namuna Dars:\n"
        "https://t.me/+yUxu7EOWyd82ODhi"
    )

# =========================
# BACK
# =========================

@dp.message(F.text == "⬅️ Orqaga")
async def go_back(message: Message):
    artikel_users.pop(message.from_user.id, None)
    await message.answer(
        "🏠 Asosiy Menu",
        reply_markup=main_menu
    )
# =========================================================
# BACK TO WORD GAME LEVELS
# =========================================================

@dp.message(F.text == "⬅️ Darajalar")
async def back_to_levels(message: Message):

    await message.answer(
        "🎮 So'z O'yini",
        reply_markup=await build_level_menu(
            message.from_user.id
        )
    )
# =========================
# COURSE HANDLER
# =========================

async def send_course_info(message: Message, course: str):
    info = COURSE_INFO.get(course)
    if not info:
        await message.answer("❌ Kurs haqida ma'lumot topilmadi.")
        return

    text = (
        f"🎉 Hozirda barcha kurslar 50% CHEGIRMADA!\n\n"
        f"{course} Video Darslari\n\n"
        f"📚 {info['lessons']} dars\n\n"
        f"❌ Eski narx: {info['old_price']}\n"
        f"🔥 Chegirmadagi narx: {info['price']}\n\n"
        f"💳 To'lov:\n"
        f"9860 3501 4490 7192\n\n"
        f"👤 Zayniddinkhuja Makhmudov\n\n"
        f"📩 To'lovdan keyin chekni (rasm shaklida) shu botga yuboring.\n"
        f"Admin tasdiqlaydi va kurs havolasini yuboradi."
    )

    db_execute(
        "UPDATE users SET course = %s WHERE user_id = %s",
        (course, message.from_user.id)
    )

    await message.answer(text)

@dp.message(F.text == "🇩🇪 A1")
async def course_a1(message: Message):
    await send_course_info(message, "🇩🇪 A1")

@dp.message(F.text == "🇩🇪 A2")
async def course_a2(message: Message):
    await send_course_info(message, "🇩🇪 A2")

@dp.message(F.text == "🇩🇪 B1")
async def course_b1(message: Message):
    await send_course_info(message, "🇩🇪 B1")

@dp.message(F.text == "🔥 A1-B1")
async def course_a1b1(message: Message):
    await send_course_info(message, "🔥 A1-B1")

@dp.message(F.text == "🔥 A1-C1")
async def course_a1c1(message: Message):
    await send_course_info(message, "🔥 A1-C1")

# =========================
# CHECK PHOTO (payment receipt)
# =========================

# Faqat FSM holatida bo'lmagan (hech qanday state'siz) rasm yuborilganda ishlashi ta'minlandi
@dp.message(F.photo, StateFilter(None))
async def check_photo(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # Foydalanuvchi kurs tanlaganligini tekshiramiz
    row = db_execute(
        "SELECT course FROM users WHERE user_id = %s",
        (user_id,),
        fetchone=True
    )

    if not row or not row[0]:
        await message.answer("❌ Avval sotib olmoqchi bo'lgan kursingizni menyudan tanlang.")
        return

    # To'lov cheki rasmini xavfsiz saqlash
    await state.update_data(photo=message.photo[-1].file_id)

    await message.answer("👤 Ism va familiyangizni yuboring:")
    await state.set_state(RegisterState.waiting_for_name)


@dp.message(RegisterState.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    full_name = message.text.strip()
    words = full_name.split()

    if len(words) < 2 or any(len(w) < 2 for w in words):
        await message.answer("❌ Iltimos, ism va familiyangizni to'liq kiriting (Faqat harflardan iborat bo'lsin):")
        return

    await state.update_data(full_name=full_name)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📱 Telefon Raqamni Yuborish",
                    request_contact=True
                )
            ]
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "📱 Telefon raqamingizni quyidagi tugmani bosib yuboring yoki qo'lda kiriting:",
        reply_markup=keyboard
    )
    await state.set_state(RegisterState.waiting_for_phone)


@dp.message(RegisterState.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext):
    if message.contact:
        phone = message.contact.phone_number
    else:
        # Qo'lda yozilgan raqamdan ortiqcha simvollarni tozalash va tekshirish
        phone = "".join(filter(str.isdigit, message.text.strip()))
        if len(phone) < 9:
            await message.answer(
                "❌ Telefon raqami noto'g'ri formatda shakllantirildi.\n"
                "Iltimos, qaytadan to'g'ri raqam kiriting:"
            )
            return

    data = await state.get_data()
    photo = data["photo"]
    full_name = data["full_name"]
    user = message.from_user

    # Tanlangan kursni bazadan qayta tekshirish
    row = db_execute(
        "SELECT course FROM users WHERE user_id = %s",
        (user.id,),
        fetchone=True
    )
    course = row[0] if row and row[0] else "Kurs tanlanmagan"

    # Foydalanuvchi ma'lumotlarini yangilash
    db_execute(
        "UPDATE users SET full_name = %s, phone = %s WHERE user_id = %s",
        (full_name, phone, user.id),
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approve", callback_data=f"approve:{user.id}"),
                InlineKeyboardButton(text="❌ Reject", callback_data=f"reject:{user.id}")
            ]
        ]
    )

    username_str = f"@{user.username}" if user.username else "Mavjud emas"
    caption = (
        f"💳 <b>Yangi xaridor xabari!</b>\n\n"
        f"👤 Ism: {full_name}\n"
        f"📱 Telefon: {phone}\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📚 Kurs: <b>{course}</b>\n"
        f"🌐 Username: {username_str}"
    )

    try:
        await bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo,
            caption=caption,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Adminga to'lov chekini yuborishda xatolik yuz berdi: {e}")

    await message.answer(
        "✅ Ma'lumotlaringiz va to'lov chekingiz adminga muvaffaqiyatli yuborildi!\n\n"
        "⏳ Tasdiqlanishini kuting va darslarni o'rganishda davom eting.",
        reply_markup=main_menu,
    )

    await state.clear()
# =========================================================
# APPROVE / REJECT LOGIC
# =========================================================

@dp.callback_query(F.data.startswith("approve:"))
async def approve_user(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "❌ Sizda ruxsat yo'q!",
            show_alert=True
        )
        return

    try:
        user_id = int(
            callback.data.split(":")[1]
        )
    except (IndexError, ValueError):
        await callback.answer(
            "❌ Xatolik yuz berdi."
        )
        return

    db_execute(
        """
        UPDATE users
        SET approved = 1
        WHERE user_id = %s
        """,
        (user_id,)
    )

    row = db_execute(
        """
        SELECT course, full_name
        FROM users
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    if not row:

        await callback.answer(
            "❌ Foydalanuvchi topilmadi!"
        )
        return

    course = row[0] or "Noma'lum kurs"
    full_name = row[1] or "Talaba"

    course_link = COURSE_LINKS.get(course)
    group_link = GROUP_LINKS.get(course)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎥 Kurs Kanali",
                    url=course_link
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 Savollar Guruhi",
                    url=group_link
                )
            ]
        ]
    )

    try:

        await bot.send_message(
            chat_id=user_id,
            text=(
                f"🎉 Assalomu alaykum, {full_name}!\n\n"
                f"✅ To'lovingiz muvaffaqiyatli tasdiqlandi.\n\n"
                f"📚 Kurs: {course}\n\n"
                f"👇 Quyidagi tugmalar orqali kursga qo‘shiling."
            ),
            reply_markup=keyboard
        )

    except Exception as e:

        logger.error(
            f"Foydalanuvchiga xabar yuborishda xatolik: {e}"
        )

    # =====================================================
    # SEND TO BUYERS CHANNEL
    # =====================================================

    try:

        await bot.send_message(

            -1003916093529,

            f"💳 Yangi Xaridor\n\n"
            f"👤 Ism: {full_name}\n"
            f"🆔 ID: {user_id}\n"
            f"📚 Kurs: {course}\n\n"
            f"✅ To'lov tasdiqlandi"

        )

    except Exception as e:

        logger.error(
            f"Kanalga yuborishda xatolik: {e}"
        )

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await callback.message.answer(
        f"✅ Foydalanuvchi tasdiqlandi!\n\n"
        f"👤 {full_name}\n"
        f"📚 {course}"
    )

    await callback.answer(
        "✅ Muvaffaqiyatli tasdiqlandi"
    )
# =========================
# LESSONS HOME
# =========================

@dp.message(F.text == "🎓 Darslarni O'rganish")
async def lessons_home(message: Message):
    user_id = message.from_user.id

    # ADMIN FULL ACCESS
    if user_id == ADMIN_ID:
        await message.answer(
            "🎓 Darslarni O'rganish\n\n"
            "Darajani tanlang:",
            reply_markup=build_lessons_menu(["A1", "A2", "B1", "B2", "C1"])
        )
        return

    row = db_execute(
        """
        SELECT
            approved,
            course
        FROM users
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    if not row:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return

    approved = row[0]
    course = row[1]

    if approved != 1:
        await message.answer("🔒 Avval kurs sotib oling.")
        return

    levels = get_available_levels(course)

    if not levels:
        await message.answer("❌ Kurs ma'lumoti topilmadi.")
        return

    await message.answer(
        "🎓 Darslarni O'rganish\n\n"
        "Darajani tanlang:",
        reply_markup=build_lessons_menu(levels)
    )
# =========================================================
# LEVEL HANDLERS
# =========================================================

@dp.message(
    F.text.in_(
        {
            "📘 A1",
            "📘 A2",
            "📘 B1",
            "📘 B2",
            "📘 C1"
        }
    )
)
async def level_lessons(
    message: Message
):

    level = (
        message.text
        .replace("📘 ", "")
        .strip()
    )

    user_id = (
        message.from_user.id
    )

    # ACTIVE LEVEL SAVE
    selected_levels[
        user_id
    ] = level

    unlocked = get_unlocked_lesson(
        user_id,
        level
    )

    exam_passed = (
        is_final_exam_passed(
            user_id,
            level
        )
    )

    await message.answer(

        f"🇩🇪 {level} Darajasi\n\n"
        f"Darsni tanlang:",

        reply_markup=
        build_level_lessons_menu(
            level,
            unlocked,
            exam_passed
        )
    )
# =========================
# AI TEACHER
# =========================

@dp.message(F.text == "🤖 AI Teacher")
async def ai_teacher_menu(message: Message):
    await message.answer(
        "🤖 AI Teacher\n\n"
        "🚧 Tez orada ishga tushadi."
    )
# =========================================================
# REGISTER STATES
# =========================================================

class RegisterStates(StatesGroup):
    waiting_full_name = State()

# =========================================================
# LEVEL CONFIG
# =========================================================
LEVEL_CONFIG = {
    "A1": {
        "file": "A1-words.csv",
        "blocks": 10,
        "size": 100,
        "required": 600
    },
    "A2": {
        "file": "A2-words.csv",
        "blocks": 10,
        "size": 100,
        "required": 600
    },
    "B1": {
        "file": "B1-words.csv",
        "blocks": 10,
        "size": 100,
        "required": 600
    },
    "B2": {
        "file": "B2-words.csv",
        "blocks": 15,
        "size": 100,
        "required": 900
    },
    "C1": {
        "file": "C1-words.csv",
        "blocks": 11,
        "size": 100,
        "required": 600,
    }
}

LEVEL_ORDER = ["A1", "A2", "B1", "B2", "C1"]

# =========================================================
# LOAD CSV
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = BASE_DIR

def load_level_csv(level, filename):
    data = []

    # =====================================================
    # FILE CHECK
    # =====================================================
    if not os.path.exists(filename):
        logger.warning(f"{filename} topilmadi")
        # Sinxron funksiyadan asinxron xabarni xavfsiz yuborish
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(bot.send_message(ADMIN_ID, f"⚠️ CSV topilmadi:\n{filename}"))
        return

    # =====================================================
    # LOAD FILE
    # =====================================================
    try:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # HEADER SKIP

            for row in reader:
                try:
                    if len(row) < 5:
                        continue

                    item = {
                        "id": int(row[0]),
                        "german": row[1].strip(),
                        "correct": row[2].strip(),
                        "wrong1": row[3].strip(),
                        "wrong2": row[4].strip(),
                    }
                    data.append(item)
                except Exception as e:
                    logger.error(f"CSV row error in {level}: {e}")
    except Exception as e:
        logger.error(f"CSV load error for {level}: {e}")
        return

    # =====================================================
    # SAVE DATA
    # =====================================================
    QUIZ_DATA[level] = data
    logger.info(f"{level}: {len(data)} loaded ✅")


# =========================================================
# LOAD ALL QUIZZES
# =========================================================

def load_all_quizzes():
    QUIZ_DATA.clear()
    for level, config in LEVEL_CONFIG.items():
        try:
            load_level_csv(level, config["file"])
        except Exception as e:
            logger.error(f"{level} load failed: {e}")
    logger.info("All quizzes loaded ✅")

# =========================================================
# UNIVERSAL CSV LOADER
# Grammatik.csv
# Lesen.csv
# Hören.csv
# =========================================================

def load_tasks(
    filename,
    level,
    lesson,
    teil=None
):

    data = []

    filepath = os.path.join(
        "A1-C1-Level",
        filename
    )

    if not os.path.exists(filepath):

        logger.error(
            f"CSV FILE NOT FOUND: {filepath}"
        )

        return []

    try:

        with open(
            filepath,
            "r",
            encoding="utf-8"
        ) as f:

            reader = csv.DictReader(f)

            for row in reader:

                try:

                    if (
                        not row.get("level")
                        or not row.get("lesson")
                        or not row.get("task_id")
                    ):
                        continue

                    if (
                        row["level"].strip()
                        != level
                    ):
                        continue

                    if (
                        int(row["lesson"])
                        != lesson
                    ):
                        continue

                    if (
                        teil is not None
                        and
                        int(row["teil"])
                        != teil
                    ):
                        continue

                    data.append({

                        "task_id":
                            int(
                                row["task_id"]
                            ),

                        "question":
                            row.get(
                                "question",
                                ""
                            ).strip(),

                        "correct":
                            row.get(
                                "correct",
                                ""
                            ).strip(),

                        "wrong1":
                            row.get(
                                "wrong1",
                                ""
                            ).strip(),

                        "wrong2":
                            row.get(
                                "wrong2",
                                ""
                            ).strip(),

                        "type":
                            row.get(
                                "type",
                                "test"
                            ).strip()
                    })

                except Exception as e:

                    logger.error(
                        f"CSV ROW ERROR: {e}"
                    )

    except Exception as e:

        logger.error(
            f"CSV LOAD ERROR: {e}"
        )

    return data


# =========================================================
# GRAMMATIK LOADER
# =========================================================

def load_grammatik(
    level,
    lesson,
    teil=None
):
    return load_tasks(
        "Grammatik.csv",
        level,
        lesson,
        teil
    )


# =========================================================
# LESEN LOADER
# =========================================================

def load_lesen(
    level,
    lesson,
    teil=None
):
    return load_tasks(
        "Lesen.csv",
        level,
        lesson,
        teil
    )
# =========================================================
# GET LESEN IMAGE
# =========================================================

def get_lesen_image(
    level,
    lesson
):

    folder = os.path.join(
        BASE_DIR,
        "A1-C1-Level",
        "lesen_photo"
    )

    candidates = [

        f"{level}-{lesson}-lesen.png",

        f"{level}-{lesson}.1-lesen.png"
    ]

    for filename in candidates:

        filepath = os.path.join(
            folder,
            filename
        )

        if os.path.exists(
            filepath
        ):
            return filepath

    return None

# =========================================================
# HÖREN LOADER
# =========================================================

def load_horen(
    level,
    lesson,
    teil=None
):
    return load_tasks(
        "Horen.csv",
        level,
        lesson,
        teil
    )

# =========================================================
# LOAD VIZU LESEN
# =========================================================

def load_vizu_lesen():

    global vizu_lesen_questions

    csv_path = "VIZU-A1/A1-Lesenmock.csv"

    if not os.path.exists(csv_path):

        logger.warning(
            "A1-Lesenmock.csv not found."
        )

        return

    try:

        with open(
            csv_path,
            "r",
            encoding="utf-8"
        ) as f:

            reader = csv.DictReader(f)

            vizu_lesen_questions = list(reader)

        logger.info(
            f"VIZU Lesen loaded: "
            f"{len(vizu_lesen_questions)} questions"
        )

    except Exception as e:

        logger.error(
            f"VIZU Lesen load error: {e}"
        )

# =========================================================
# LOAD VIZU HOREN
# =========================================================
def load_vizu_horen():
    global vizu_horen_questions
    
    csv_path = "VIZU-A1/A1-Hörenmock.csv"
    
    # FAYL YO'LINI TEKSHIRISH
    logger.info(f"HÖREN CSV PATH: {os.path.abspath(csv_path)}")
    logger.info(f"HÖREN CSV EXISTS: {os.path.exists(csv_path)}")
    
    # PAPKA ICHINI KO'RSATISH
    folder = "VIZU-A1"
    if os.path.exists(folder):
        files = os.listdir(folder)
        logger.info(f"VIZU-A1 FOLDER FILES: {files}")
    else:
        logger.error(f"VIZU-A1 PAPKASI TOPILMADI!")
        return

    if not os.path.exists(csv_path):
        logger.error(f"HÖREN CSV TOPILMADI: {csv_path}")
        return

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            vizu_horen_questions = list(reader)

        logger.info(
            f"VIZU Hören loaded: {len(vizu_horen_questions)} questions ✅"
        )
        
        # Birinchi qatorni tekshirish
        if vizu_horen_questions:
            logger.info(f"HÖREN FIRST ROW KEYS: {list(vizu_horen_questions[0].keys())}")
            logger.info(f"HÖREN FIRST ROW: {vizu_horen_questions[0]}")

    except Exception as e:
        logger.error(f"VIZU Hören load error: {e}")
# =========================================================
# DAILY RESET
# =========================================================

def reset_daily_scores():
    today = date.today()
    try:
        db_execute(
            """
            UPDATE users
            SET
                daily_score = 0,
                last_daily_reset = %s
            WHERE
                last_daily_reset IS NULL
                OR last_daily_reset < %s
            """,
            (today, today)
        )
        logger.info("Daily scores successfully reset ✅")
    except Exception as e:
        logger.error(f"Error resetting daily scores: {e}")
# =========================================================
# QUIZ MENU
# =========================================================

async def build_level_menu(user_id):
    result = db_execute(
        """
        SELECT unlocked_level
        FROM users
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    unlocked = result[0] if result and result[0] else "A1"

    # LEVEL_ORDER ichida borligini xavfsiz tekshirish (ValueError oldini olish)
    if unlocked in LEVEL_ORDER:
        unlocked_index = LEVEL_ORDER.index(unlocked)
    else:
        unlocked_index = 0

    rows = []
    current = []
# =====================================================
    # LEVELS
    # =====================================================
    rows = []
    current = []

    for level in LEVEL_ORDER:
        current.append(KeyboardButton(text=f"🎯 {level}"))

        # 2 ta tugmadan keyin qatorni yangilash
        if len(current) == 2:
            rows.append(current)
            current = []

    # Qolgan tugmalarni qo'shish
    if current:
        rows.append(current)

    # =====================================================
    # RANKING
    # =====================================================
    rows.append([KeyboardButton(text="🏆 Reytinglar")])

    # =====================================================
    # CERTIFICATE
    # =====================================================
    rows.append([KeyboardButton(text="🏅 W-Zertifikat")])

    # =====================================================
    # BACK
    # =====================================================
    rows.append([KeyboardButton(text="⬅️ Orqaga")])

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True
    )
# =========================================================
# 1. CONFIGURATION & HELPERS
# =========================================================

GOLD_COLOR = colors.HexColor("#D4AF37")
SILVER_COLOR = colors.HexColor("#C0C0C0")
BRONZE_COLOR = colors.HexColor("#CD7F32")

# =========================================================
# CERTIFICATE HELPERS
# =========================================================

def is_level_completed(user_id, level):
    """
    Sertifikat uchun faqat tanlangan daraja tekshiriladi.
    Oldingi yoki keyingi darajalar hisobga olinmaydi.
    """
    config = LEVEL_CONFIG.get(level)

    if not config:
        return False

    total_blocks = config["blocks"]

    for block in range(1, total_blocks + 1):
        row = db_execute(
            """
            SELECT best_score
            FROM quiz_progress
            WHERE user_id = %s
            AND level = %s
            AND block_number = %s
            """,
            (user_id, level, block),
            fetchone=True
        )

        # blok ishlanmagan
        if not row:
            return False

        # blokdan kamida 60 ball
        if (row[0] or 0) < 60:
            return False

    return True


def get_level_percent(user_id, level):
    """
    Tanlangan darajaning umumiy foizini hisoblaydi.
    """
    result = db_execute(
        """
        SELECT COALESCE(SUM(best_score), 0)
        FROM quiz_progress
        WHERE user_id = %s
        AND level = %s
        """,
        (user_id, level),
        fetchone=True
    )

    total_score = result[0] if result else 0
    config = LEVEL_CONFIG.get(level)

    if not config:
        return 0, 0

    max_score = config["blocks"] * 100
    percent = round((total_score / max_score) * 100, 1)

    return percent, total_score


def get_certificate_rank(percent):
    """
    Sertifikat darajasi
    """
    if percent >= 85:
        return "GOLD"
    if percent >= 70:
        return "SILVER"
    if percent >= 60:
        return "BRONZE"
    return None


def get_existing_certificate(user_id, level):
    """
    Shu daraja uchun avval sertifikat olinganmi
    """
    return db_execute(
        """
        SELECT cert_id
        FROM w_certificates
        WHERE user_id = %s
        AND level = %s
        """,
        (user_id, level),
        fetchone=True
    )


def generate_certificate_id(level):
    """
    Sertifikat ID
    """
    return f"VIZU-{level}-{uuid.uuid4().hex[:8].upper()}"
def save_certificate(user_id, level, rank, cert_id, percent, score):
    db_execute(
        """
        INSERT INTO w_certificates
        (
            user_id,
            level,
            rank,
            cert_id,
            percent,
            score
        )
        VALUES
        (
            %s, %s, %s, %s, %s, %s
        )

        ON CONFLICT (user_id, level)

        DO UPDATE SET
            rank = EXCLUDED.rank,
            cert_id = EXCLUDED.cert_id,
            percent = EXCLUDED.percent,
            score = EXCLUDED.score,
            created_at = NOW()
        """,
        (
            user_id,
            level,
            rank,
            cert_id,
            percent,
            score
        )
    )
# =========================================================
# 2. W-ZERTIFIKAT GENERATOR (A4 VERTICAL)
# =========================================================

async def create_pdf_certificate(user_id, full_name, level, rank, percent, score, cert_id):
    os.makedirs("generated", exist_ok=True)
    pdf_path = f"generated/{cert_id}.pdf"
    
    level_folder = f"{level.lower()}-level"
    header_img = f"certificates/{level_folder}/{level.lower()}-{rank.lower()}-header.png"
    footer_img = f"certificates/{level_folder}/{level.lower()}-{rank.lower()}-footer.png"
    
    # A4 VERTICAL (Portrait)
    pdf = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    
    def draw_responsive_image(img_path, y_pos, target_width_ratio=0.9):
        if os.path.exists(img_path):
            img = Image.open(img_path)
            img_w, img_h = img.size
            scale = (width * target_width_ratio) / img_w
            new_w, new_h = img_w * scale, img_h * scale
            pdf.drawImage(
                ImageReader(img_path),
                (width - new_w) / 2, y_pos,
                width=new_w, height=new_h,
                preserveAspectRatio=True, mask="auto"
            )
            return new_h
        return 0

    # Header va Footer chizish
    header_h = draw_responsive_image(header_img, height - 250)
    draw_responsive_image(footer_img, 50)

    # Matnlarni chizish
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawCentredString(width / 2, 550, full_name)
    
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(width / 2, 510, f"hat das Niveau {level}")
    pdf.drawCentredString(width / 2, 485, "erfolgreich abgeschlossen.")

    # Jadval rangini tanlash
    rank_colors = {"GOLD": GOLD_COLOR, "SILVER": SILVER_COLOR}
    main_color = rank_colors.get(rank.upper(), BRONZE_COLOR)

    data = [
        ["ID", cert_id],
        ["Datum", datetime.now().strftime("%d.%m.%Y")],
        ["Ergebnis", f"{percent}%"],
        ["Rang", rank]
    ]

    table = Table(data, colWidths=[120, 250])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 14),
        ("TEXTCOLOR", (0, 0), (0, -1), main_color),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))

    table.wrapOn(pdf, width, height)
    table.drawOn(pdf, width / 2 - 185, 350)
    
    pdf.save()
    return pdf_path

# =========================================================
# 3. TELEGRAM HANDLERS
# =========================================================

@dp.message(F.text == "🏅 W-Zertifikat")
async def certificate_menu(message: Message):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🏅 A1 W-Zertifikat"), KeyboardButton(text="🏅 A2 W-Zertifikat")],
        [KeyboardButton(text="🏅 B1 W-Zertifikat"), KeyboardButton(text="🏅 B2 W-Zertifikat")],
        [KeyboardButton(text="🏅 C1 W-Zertifikat")],
        [KeyboardButton(text="⬅️ Orqaga")]
    ], resize_keyboard=True)
    await message.answer("🏅 Sertifikat darajasini tanlang:", reply_markup=kb)

@dp.message(F.text.contains("W-Zertifikat"))
async def generate_certificate(message: Message):
    if message.text == "🏅 W-Zertifikat": return
    
    level = message.text.replace("🏅 ", "").replace(" W-Zertifikat", "")
    uid = message.from_user.id
    
    if not is_level_completed(uid, level):
        return await message.answer(f"❌ {level} darajasi hali to'liq yakunlanmagan.")
    
    percent, score = get_level_percent(uid, level)
    
    if percent < 60:
        return await message.answer(f"❌ Uzr, sertifikat olish uchun kamida 60% natija kerak. Sizning natijangiz: {percent}%")
    
    rank = get_certificate_rank(percent)
    user_data = db_execute("SELECT full_name FROM users WHERE user_id = %s", (uid,), fetchone=True)
    full_name = user_data[0] if user_data else message.from_user.full_name
    cert_id = generate_certificate_id(level)
    
    try:
        save_certificate(uid, level, rank, cert_id, percent, score)
        pdf_path = await create_pdf_certificate(uid, full_name, level, rank, percent, score, cert_id)
        await message.answer_document(
            FSInputFile(pdf_path), 
            caption=f"🏅 {level} W-Zertifikat\n🏆 Rank: {rank}\n📊 Natija: {percent}%\n🎫 ID: {cert_id}"
        )
    except Exception as e:
        logger.error(f"Sertifikat yaratishda xatolik: {e}")
        await message.answer("⚠️ Sertifikat yaratishda xatolik yuz berdi.")

# =========================================================
# BLOCK MENU
# =========================================================

def build_block_keyboard(level, user_id):

    config = LEVEL_CONFIG.get(level)

    if not config:

        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="⬅️ Orqaga")]
            ],
            resize_keyboard=True
        )

    rows = []
    current = []

    for i in range(
        1,
        config["blocks"] + 1
    ):

        progress = db_execute(
            """
            SELECT best_score
            FROM quiz_progress
            WHERE user_id = %s
            AND level = %s
            AND block_number = %s
            """,
            (
                user_id,
                level,
                i
            ),
            fetchone=True
        )

        if progress:

            score = progress[0] or 0

            # Blokdagi real savollar soni
            block_size = config["size"]

            percent = round(
                (score / block_size) * 100
            ) if block_size > 0 else 0

            if percent >= 100:

                text = (
                    f"🏆 "
                    f"{level}-{i}-Blok "
                    f"(100%)"
                )

            else:

                text = (
                    f"✅ "
                    f"{level}-{i}-Blok "
                    f"({percent}%)"
                )

        else:

            text = (
                f"📚 "
                f"{level}-{i}-Blok"
            )

        current.append(
            KeyboardButton(text=text)
        )

        if len(current) == 2:

            rows.append(current)

            current = []

    if current:

        rows.append(current)

    rows.append(
        [KeyboardButton(text="⬅️ Darajalar")]
    )

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True
    )

# =========================================================
# OPEN WORD GAME
# =========================================================

@dp.message(F.text == "🎮 So'z O'yini")
async def word_game_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # Eski kutilmagan state holatlarini har ehtimolga qarshi tozalash
    await state.clear()

    # =====================================================
    # CHECK FULL NAME
    # =====================================================
    result = db_execute(
        """
        SELECT full_name
        FROM users
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    full_name = result[0] if result else None

    # =====================================================
    # ASK NAME
    # =====================================================
    if not full_name or full_name in {"Unknown", ""}:
        await message.answer(
            "📝 To'liq ism familiyangizni kiriting.\n\n"
            "Masalan:\n"
            "Zayniddinkhuja Makhmudov"
        )
        await state.set_state(RegisterStates.waiting_full_name)
        return

    # =====================================================
    # OPEN MENU
    # =====================================================
    menu = await build_level_menu(user_id)
    await message.answer(
        "🎮 WortSpiel\n\n"
        "Darajani tanlang:",
        reply_markup=menu
    )

# =========================================================
# SAVE FULL NAME
# =========================================================

@dp.message(RegisterStates.waiting_full_name)
async def save_full_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    full_name = message.text.strip()

    # =====================================================
    # VALIDATION
    # =====================================================
    if len(full_name) < 5:
        await message.answer("❌ Juda qisqa ism. Kamida 5 ta harf bo'lishi kerak.")
        return

    if len(full_name) > 50:
        await message.answer("❌ Juda uzun ism. Maksimal 50 ta harf bo'lishi mumkin.")
        return

    # AT LEAST 2 WORDS
    if len(full_name.split()) < 2:
        await message.answer(
            "❌ Ism va familiyani to'liq kiriting.\n\n"
            "Masalan:\n"
            "Zayniddinkhuja Makhmudov"
        )
        return

    # =====================================================
    # SAVE DATABASE
    # =====================================================
    db_execute(
        """
        UPDATE users
        SET full_name = %s
        WHERE user_id = %s
        """,
        (full_name, user_id)
    )

    await state.clear()

    # =====================================================
    # SUCCESS
    # =====================================================
    await message.answer(
        f"✅ Saqlandi:\n"
        f"{full_name}"
    )

    # =====================================================
    # OPEN QUIZ MENU
    # =====================================================
    menu = await build_level_menu(user_id)
    await message.answer(
        "🎮 WortSpiel\n\n"
        "Darajani tanlang:",
        reply_markup=menu
    )


# =========================================================
# OPEN LEVEL
# =========================================================

@dp.message(F.text.regexp(r"🎯 (A1|A2|B1|B2|C1)"))
async def open_level_handler(message: Message):

    level = (
        message.text
        .replace("🎯 ", "")
        .strip()
    )

    await message.answer(

        f"📚 {level} bloklari",

        reply_markup=
        build_block_keyboard(
            level,
            message.from_user.id
        )
    )

# =========================================================
# CHECK LEVEL UNLOCK
# =========================================================

def check_level_unlock(user_id, current_level):
    # C1 LAST LEVEL
    if current_level == "C1":
        return None

    config = LEVEL_CONFIG.get(current_level)
    if not config:
        return None

    required = config["required"]

    result = db_execute(
        """
        SELECT COALESCE(SUM(best_score), 0)
        FROM quiz_progress
        WHERE user_id = %s AND level = %s
        """,
        (user_id, current_level),
        fetchone=True
    )

    total = result[0] if result else 0

    if total >= required:
        try:
            next_level = LEVEL_ORDER[LEVEL_ORDER.index(current_level) + 1]
            
            db_execute(
                """
                UPDATE users
                SET unlocked_level = %s
                WHERE user_id = %s
                """,
                (next_level, user_id)
            )
            return next_level
        except (ValueError, IndexError) as e:
            logger.error(f"Error determining next level for index: {e}")
            return None

    return None

# =========================================================
# START QUIZ BLOCK
# =========================================================

async def start_quiz_block(
    message: Message,
    level: str,
    block: int,
    force_restart=False,
    user_id=None
):
    if user_id is None:
        user_id = message.from_user.id

    # ACTIVE QUIZ CHECK
    if user_id in quiz_running:
        session = quiz_sessions.get(user_id)

        # STUCK SESSION FIX
        if not session:
            quiz_running.discard(user_id)
            # Eski qotib qolgan holat tozalandi, endi yangi o'yinni boshlashga ruxsat beramiz.
        else:
            await message.answer("⚠️ Sizda hali ham tugallanmagan aktiv test mavjud. Avval uni yakunlang.")
            return

    # Bu joydan boshlab test generatoringiz va savollar zanjiri davom etadi...
# =====================================================
    # USER LEVEL SECURITY
    # =====================================================

    user_data = db_execute(
        "SELECT unlocked_level FROM users WHERE user_id = %s",
        (user_id,),
        fetchone=True
    )
    current_unlocked = user_data[0] if user_data else "A1"

    # Level va current_unlocked ro'yxatda borligini tekshirish
    if level not in LEVEL_ORDER or current_unlocked not in LEVEL_ORDER:
        await message.answer("❌ Xatolik yuz berdi.")
        return

# =====================================================
# BLOCK SECURITY
# =====================================================

    config = LEVEL_CONFIG.get(level)
    if not config or block > config["blocks"]:
        await message.answer("❌ Noto'g'ri blok.")
        return

# =====================================================
# PREVIOUS BLOCK CHECK
# =====================================================

    if block > 1 and not force_restart:
        prev_block = block - 1
        res = db_execute(
            "SELECT best_score FROM quiz_progress WHERE user_id = %s AND level = %s AND block_number = %s",
            (user_id, level, prev_block),
            fetchone=True
        )
        if not res or (res[0] or 0) < 60:
            await message.answer(f"🔒 Avval {prev_block}-Blokdan kamida 60/100 ball to'plang.")
            return

# =====================================================
# LOAD QUESTIONS
# =====================================================

    questions = QUIZ_DATA.get(level, [])
    start_index = (block - 1) * 100
    end_index = 1100 if (level == "C1" and block == 11) else (start_index + 100)

    block_questions = questions[start_index:end_index]
    if not block_questions:
        await message.answer("❌ Blokda savollar topilmadi.")
        return

# =====================================================
# START QUIZ
# =====================================================

    random.shuffle(block_questions)

    # Tozalash
    quiz_running.discard(user_id)
    quiz_sessions.pop(user_id, None)
    
    # Eskisini tozalash
    keys_to_del = [k for k in active_questions if k.startswith(f"{user_id}_")]
    for k in keys_to_del:
        active_questions.pop(k, None)
        answered_users.pop(k, None)

    quiz_running.add(user_id)
    quiz_sessions[user_id] = {
        "level": level,
        "block": block,
        "questions": block_questions,
        "index": 0,
        "score": 0
    }

    await message.answer(f"🚀 {level}-{block}-Blok boshlandi! Savollar: {len(block_questions)}")
    await send_next_question(message.chat.id, user_id)
# =========================================================
# START BLOCK
# =========================================================

@dp.message(
    F.text.regexp(
        r"(📚|✅|🏆)\s?(A1|A2|B1|B2|C1)-(\d+)-Blok"
    )
)
async def start_block(message: Message):

    import re

    match = re.search(
        r"(A1|A2|B1|B2|C1)-(\d+)-Blok",
        message.text
    )

    if not match:
        return

    level = match.group(1)
    block = int(match.group(2))
    user_id = message.from_user.id

    # =====================================================
    # 1-BLOK HAMMA LEVELDA OCHIQ
    # =====================================================

    if block == 1:
        await start_quiz_block(
            message,
            level,
            block
        )
        return

    # =====================================================
    # LEVEL SECURITY
    # =====================================================

    user_data = db_execute(
        "SELECT unlocked_level FROM users WHERE user_id = %s",
        (user_id,),
        fetchone=True
    )

    current_unlocked = (
        user_data[0]
        if user_data else "A1"
    )

    # =====================================================
    # CHECK PREVIOUS RESULT
    # =====================================================

    row = db_execute(
        """
        SELECT best_score
        FROM quiz_progress
        WHERE user_id = %s
        AND level = %s
        AND block_number = %s
        """,
        (
            user_id,
            level,
            block
        ),
        fetchone=True
    )

    if row:

        best_score = row[0] or 0

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Ha, qayta ishlash",
                        callback_data=
                        f"restartquiz:{level}:{block}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Yo'q",
                        callback_data="cancelquiz"
                    )
                ]
            ]
        )

        await message.answer(

            f"📊 Oxirgi natijangiz\n\n"

            f"🇩🇪 Daraja: {level}\n"

            f"📚 Blok: {block}\n\n"

            f"🏆 Eng yaxshi natija: "
            f"{best_score}%\n\n"

            f"Qayta ishlamoqchimisiz?",

            reply_markup=keyboard
        )

        return

    # =====================================================
    # FIRST START
    # =====================================================

    await start_quiz_block(
        message,
        level,
        block
    )
    # =====================================================
    # CHECK PREVIOUS RESULT
    # =====================================================

    row = db_execute(
        """
        SELECT best_score
        FROM quiz_progress
        WHERE user_id = %s
        AND level = %s
        AND block_number = %s
        """,
        (
            user_id,
            level,
            block
        ),
        fetchone=True
    )

    # AGAR OLDIN ISHLAGAN BO'LSA
    if row:

        best_score = row[0] or 0

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Ha, qayta ishlash",
                        callback_data=
                        f"restartquiz:{level}:{block}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Yo'q",
                        callback_data="cancelquiz"
                    )
                ]
            ]
        )

        await message.answer(

            f"📊 Oxirgi natijangiz\n\n"

            f"🇩🇪 Daraja: {level}\n"

            f"📚 Blok: {block}\n\n"

            f"🏆 Eng yaxshi natija: "
            f"{best_score}/100\n\n"

            f"Qayta ishlamoqchimisiz?",

            reply_markup=keyboard
        )

        return

    # =====================================================
    # FIRST START
    # =====================================================

    await start_quiz_block(
        message,
        level,
        block
    )
# =========================================================
# SEND QUESTION
# =========================================================

async def send_next_question(chat_id, user_id):
    session = quiz_sessions.get(user_id)
    if not session:
        quiz_running.discard(user_id)
        return

    questions = session["questions"]
    index = session["index"]

    if index >= len(questions):
        await finish_quiz(chat_id, user_id)
        return

    question = questions[index]
    answers = [question["correct"], question["wrong1"], question["wrong2"]]
    random.shuffle(answers)

    qid = f"{user_id}_{question['id']}"
    answered_users[qid] = set()

    # Tugmalar yaratish
    builder = InlineKeyboardBuilder()
    callback_map = {}

    for i, ans in enumerate(answers):
        key = f"a{i}"
        callback_map[key] = ans
        builder.button(text=ans, callback_data=f"quiz:{qid}:{key}")
    
    builder.button(text="⛔ Yakunlash", callback_data=f"stopquiz:{user_id}")
    builder.adjust(1)

    active_questions[qid] = {
        "user_id": user_id,
        "question_id": question["id"],
        "correct": question["correct"],
        "answers": callback_map
    }

    try:
        await bot.send_message(
            chat_id,
            f"📚 {session['level']}-{session['block']}\n📊 {index + 1}/{len(questions)}\n\n🇩🇪 {question['german']}",
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        logger.error(f"Send question error: {e}")
        # Xatolik bo'lsa sessiyani tozalash
        quiz_running.discard(user_id)
        quiz_sessions.pop(user_id, None)
        active_questions.pop(qid, None)

# =========================================================
# ANSWER
# =========================================================

@dp.callback_query(F.data.startswith("quiz:"))
async def quiz_answer(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    # Callback ma'lumotini xavfsiz olish
    data_parts = callback.data.split(":", 2)
    if len(data_parts) < 3:
        await callback.answer("❌ Callback xatosi.", show_alert=True)
        return
    
    qid = data_parts[1]
    answer_key = data_parts[2]

    # Savol mavjudligini va sessiyani tekshirish
    question_data = active_questions.get(qid)
    session = quiz_sessions.get(user_id)

    if not question_data or not session:
        await callback.answer("❌ Test seansi tugagan yoki eskirgan.", show_alert=True)
        return

    # DOUBLE ANSWER BLOCK: Foydalanuvchi bir savolga ikki marta javob bera olmasligi
    if user_id in answered_users.get(qid, set()):
        await callback.answer("❌ Siz allaqachon javob bergansiz.", show_alert=True)
        return

    answered_users.setdefault(qid, set()).add(user_id)

    # Javobni tekshirish
    correct = question_data["correct"]
    selected = question_data["answers"].get(answer_key)

    if selected == correct:
        session["score"] += 1
        await callback.answer("✅ To'g'ri!")
    else:
        await callback.answer(f"❌ Noto'g'ri!\n✅ {correct}", show_alert=True)

    session["index"] += 1

    # Savolni xotiradan tozalash
    active_questions.pop(qid, None)
    answered_users.pop(qid, None)

    # Tugmani o'chirish
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    # Keyingi savolga o'tish
    await send_next_question(callback.message.chat.id, user_id)

# =========================================================
# FINISH QUIZ
# =========================================================

async def finish_quiz(
    chat_id,
    user_id
):

    session = quiz_sessions.get(
        user_id
    )

    if not session:
        return

    score = session["score"]

    level = session["level"]

    block = session["block"]

    total = len(
        session["questions"]
    )

    old_result = db_execute(
        """
        SELECT best_score
        FROM quiz_progress
        WHERE user_id = %s
        AND level = %s
        AND block_number = %s
        """,
        (
            user_id,
            level,
            block
        ),
        fetchone=True
    )

    old_score = (
        old_result[0]
        if old_result
        else 0
    )

    xp_gain = max(
        0,
        score - old_score
    )

    db_execute(
        """
        INSERT INTO quiz_progress
        (
            user_id,
            level,
            block_number,
            best_score
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s
        )
        ON CONFLICT
        (
            user_id,
            level,
            block_number
        )
        DO UPDATE SET
        best_score =
        GREATEST(
            quiz_progress.best_score,
            EXCLUDED.best_score
        )
        """,
        (
            user_id,
            level,
            block,
            score
        )
    )

    if xp_gain > 0:

        db_execute(
            """
            UPDATE users
            SET
            total_score =
            COALESCE(total_score,0)
            + %s,

            daily_score =
            COALESCE(daily_score,0)
            + %s

            WHERE user_id = %s
            """,
            (
                xp_gain,
                xp_gain,
                user_id
            )
        )

    new_level = check_level_unlock(
        user_id,
        level
    )

    unlock_text = ""

    if new_level:

        unlock_text = (
            f"\n\n"
            f"🔓 Yangi daraja ochildi:\n"
            f"🎯 {new_level}"
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Qayta ishlash",
                    callback_data=
                    f"restartquiz:{level}:{block}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Menyuga qaytish",
                    callback_data=
                    "cancelquiz"
                )
            ]
        ]
    )

    await bot.send_message(

        chat_id,

        f"🏁 Test yakunlandi!\n\n"

        f"🇩🇪 Daraja: {level}\n"

        f"📚 Blok: {block}\n\n"

        f"🏆 Natija: "
        f"{score}/{total}\n"

        f"⭐ XP: +{xp_gain}"

        f"{unlock_text}",

        reply_markup=keyboard
    )

    quiz_running.discard(
        user_id
    )

    quiz_sessions.pop(
        user_id,
        None
    )

    prefix = f"{user_id}_"

    for key in [
        k
        for k
        in active_questions
        if k.startswith(prefix)
    ]:

        active_questions.pop(
            key,
            None
        )

        answered_users.pop(
            key,
            None
        )
# =========================================================
# RESTART QUIZ
# =========================================================

@dp.callback_query(F.data.startswith("restartquiz:"))
async def restart_quiz_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    # Tozalash
    quiz_running.discard(user_id)
    quiz_sessions.pop(user_id, None)
    
    prefix = f"{user_id}_"
    for key in [k for k in active_questions if k.startswith(prefix)]:
        active_questions.pop(key, None)
        answered_users.pop(key, None)

    # Ma'lumotlarni ajratib olish
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("❌ Callback xatosi.", show_alert=True)
        return

    level, block = parts[1], int(parts[2])

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.answer("🔄 Test qayta boshlandi.")
    await start_quiz_block(
        message=callback.message, 
        level=level, 
        block=block, 
        force_restart=True, 
        user_id=user_id
    )
# =========================================================
# CANCEL & STOP QUIZ
# =========================================================

@dp.callback_query(F.data == "cancelquiz")
async def cancel_quiz_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    menu = await build_level_menu(
        callback.from_user.id
    )

    await bot.send_message(
        callback.from_user.id,
        "🎮 WortSpiel\n\nDarajani tanlang:",
        reply_markup=menu
    )

    await callback.answer()

@dp.callback_query(F.data.startswith("stopquiz:"))
async def stop_quiz(callback: CallbackQuery):
    try:
        user_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        return

    if callback.from_user.id != user_id:
        await callback.answer("❌ Bu sizning testingiz emas.", show_alert=True)
        return

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await finish_quiz(callback.message.chat.id, user_id)
# =========================================================
# GLOBAL MENU (Handlerlardan oldin e'lon qilinadi)
# =========================================================

rating_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🏆 Umumiy Reyting"),
            KeyboardButton(text="⚡ Kunlik Reyting")
        ],
        [
            KeyboardButton(text="⬅️ Darajalar")
        ]
    ],
    resize_keyboard=True
)
# =========================================================
# RANKING MENU & LOGIC
# =========================================================

@dp.message(F.text == "🏆 Reytinglar")
async def open_rating_menu(message: Message):

    await message.answer(
        "🏆 Reyting bo'limi",
        reply_markup=rating_menu
    )


async def _get_ranking_text(
    query_type: str,
    message: Message
):

    col = (
        "total_score"
        if query_type == "total"
        else "daily_score"
    )

    title = (
        "🏆 TOP 100 UMUMIY REYTING"
        if query_type == "total"
        else "⚡ TOP 100 KUNLIK REYTING"
    )

    rankings = db_execute(
        f"""
        SELECT
            COALESCE(full_name,'Unknown'),
            {col}
        FROM users
        WHERE {col} > 0
        ORDER BY {col} DESC
        LIMIT 100
        """,
        fetchall=True
    )

    if not rankings:

        return (
            f"📭 {title} hali bo'sh.\n\n"
            f"🎮 Birinchi bo'lib test ishlang!"
        )

    text = f"{title}\n\n"

    medals = {
        1: "🥇",
        2: "🥈",
        3: "🥉"
    }

    for i, (name, score) in enumerate(
        rankings,
        start=1
    ):

        medal = medals.get(
            i,
            f"{i}."
        )

        text += (
            f"{medal} "
            f"{name} "
            f"— "
            f"{score} XP\n"
        )

    my_score_row = db_execute(
        f"""
        SELECT {col}
        FROM users
        WHERE user_id = %s
        """,
        (message.from_user.id,),
        fetchone=True
    )

    my_score = (
        my_score_row[0]
        if my_score_row
        else 0
    )

    my_rank = db_execute(
        f"""
        SELECT COUNT(*) + 1
        FROM users
        WHERE {col} > %s
        """,
        (my_score,),
        fetchone=True
    )

    my_position = (
        my_rank[0]
        if my_rank
        else "-"
    )

    text += "\n━━━━━━━━━━━━━━\n"

    if my_score > 0:

        text += (
            f"👤 Sizning o'rningiz: "
            f"#{my_position}\n"
            f"⭐ Ballingiz: "
            f"{my_score} XP"
        )

    else:

        text += (
            "🎮 Siz hali test ishlamagansiz."
        )

    return text


@dp.message(F.text == "🏆 Umumiy Reyting")
async def total_ranking(message: Message):

    text = await _get_ranking_text(
        "total",
        message
    )

    await message.answer(text)


@dp.message(F.text == "⚡ Kunlik Reyting")
async def daily_ranking(message: Message):

    text = await _get_ranking_text(
        "daily",
        message
    )

    await message.answer(text)

# =========================================================
# AUTO MEMORY CLEANUP
# =========================================================
async def cleanup_quiz_memory():
    while True:
        # Xotira toshib ketmasligi uchun xavfsiz tozalash
        if len(active_questions) > 2000: active_questions.clear()
        if len(answered_users) > 2000: answered_users.clear()

        # O'lik sessiyalarni tozalash
        for uid in list(quiz_sessions.keys()):
            if uid not in quiz_running:
                quiz_sessions.pop(uid, None)

        # Eskirgan PNG fayllarni tozalash
        if os.path.exists(GENERATED_DIR):
            for file in os.listdir(GENERATED_DIR):
                if file.endswith(".png"):
                    try:
                        os.remove(os.path.join(GENERATED_DIR, file))
                    except OSError:
                        pass
        
        await asyncio.sleep(3600) # 1 soatda bir

# =========================================================
# DAILY RESET SCHEDULER
# =========================================================

async def daily_reset_scheduler():
    while True:
        now = datetime.now()
        target = now.replace(hour=0, minute=0, second=5, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        
        await asyncio.sleep((target - now).total_seconds())
        reset_daily_scores()
        logger.info("Daily scores reset ✅")

# =========================================================
# ADMIN STATES
# =========================================================

class AdminStates(StatesGroup):
    broadcast = State()

    personal_user_id = State()
    personal_text = State()


# =========================================================
# ADMIN PANEL
# =========================================================

@dp.message(Command("admin"))
async def admin_panel(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "⚙️ Admin Panel",
        reply_markup=admin_menu
    )


# =========================================================
# STATISTIKA
# =========================================================

@dp.message(F.text == "📊 Statistika")
async def admin_statistics(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    total_users = db_execute(
        "SELECT COUNT(*) FROM users",
        fetchone=True
    )[0]

    approved_users = db_execute(
        "SELECT COUNT(*) FROM users WHERE approved = 1",
        fetchone=True
    )[0]

    courses = db_execute(
        """
        SELECT
            course,
            COUNT(*)
        FROM users
        WHERE approved = 1
        GROUP BY course
        """,
        fetchall=True
    )

    course_text = ""

    if courses:

        for course, count in courses:

            course_text += (
                f"📚 {course}: {count} ta\n"
            )

    text = (
        "📊 BOT STATISTIKASI\n\n"
        f"👥 Foydalanuvchilar: {total_users}\n"
        f"💳 Xaridorlar: {approved_users}\n\n"
        f"{course_text}"
    )

    await message.answer(text)
# =========================================================
# BROADCAST SEND
# =========================================================

@dp.message(BroadcastState.waiting_for_message)
async def process_broadcast(
    message: Message,
    state: FSMContext
):

    if message.from_user.id != ADMIN_ID:
        return

    users = db_execute(
        """
        SELECT user_id
        FROM users
        """,
        fetchall=True
    )

    if not users:

        await message.answer(
            "❌ Foydalanuvchilar topilmadi."
        )

        await state.clear()

        return

    status_msg = await message.answer(
        "📤 Reklama yuborilmoqda..."
    )

    success = 0
    failed = 0

    for user in users:

        user_id = user[0]

        try:

            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )

            success += 1

            await asyncio.sleep(0.05)

        except Exception as e:

            logger.error(
                f"Broadcast error {user_id}: {e}"
            )

            failed += 1

    await status_msg.edit_text(

        f"📢 Reklama yakunlandi\n\n"

        f"👥 Jami foydalanuvchilar: {len(users)}\n"

        f"✅ Yuborildi: {success}\n"

        f"❌ Yuborilmadi: {failed}"

    )

    await state.clear()
# =========================================================
# PERSONAL MESSAGE START
# =========================================================

@dp.message(F.text == "📨 Shaxsiy Xabar")
async def personal_message_start(
    message: Message,
    state: FSMContext
):

    if message.from_user.id != ADMIN_ID:
        return

    await state.set_state(
        AdminStates.personal_user_id
    )

    await message.answer(
        "🆔 Foydalanuvchi ID sini yuboring."
    )


# =========================================================
# PERSONAL USER ID
# =========================================================

@dp.message(AdminStates.personal_user_id)
async def personal_message_user(
    message: Message,
    state: FSMContext
):

    if message.from_user.id != ADMIN_ID:
        return

    if not message.text.isdigit():

        await message.answer(
            "❌ ID raqam bo'lishi kerak."
        )

        return

    await state.update_data(
        target_user=int(message.text)
    )

    await state.set_state(
        AdminStates.personal_text
    )

    await message.answer(
        "✉️ Yuboriladigan xabarni yuboring."
    )


# =========================================================
# PERSONAL MESSAGE SEND
# =========================================================

@dp.message(AdminStates.personal_text)
async def personal_message_send(
    message: Message,
    state: FSMContext
):

    if message.from_user.id != ADMIN_ID:
        return

    data = await state.get_data()

    target_user = data.get(
        "target_user"
    )

    try:

        await bot.copy_message(
            chat_id=target_user,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )

        await message.answer(
            "✅ Xabar yuborildi."
        )

    except Exception as e:

        await message.answer(
            f"❌ Xatolik:\n{e}"
        )

    await state.clear()

# =========================================================
# START BROADCAST
# =========================================================

@dp.message(F.text == "📢 Reklama Yuborish")
async def broadcast_start(
    message: Message,
    state: FSMContext
):

    if message.from_user.id != ADMIN_ID:
        return

    await state.set_state(
        BroadcastState.waiting_for_message
    )

    await message.answer(

        "📢 Reklama rejimi yoqildi.\n\n"

        "Matn, rasm, video yoki forward "
        "xabar yuboring."

    )
# =========================================================
# ADMIN EXIT
# =========================================================

@dp.message(F.text == "⬅️ Admin Chiqish")
async def admin_exit(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "🏠 Asosiy menyu",
        reply_markup=main_menu
    )
# =========================================================
# MAIN INITIALIZATION & RUN
# =========================================================
async def main():
    try:
        init_db_pool()
        init_tables()
        init_certificate_table()
        load_artikel()
        load_vizu_lesen()
        load_vizu_horen()
        init_w_certificates_table()

        # =====================================================
        # DEBUG: CSV YUKLANGANINI TEKSHIRISH
        # =====================================================
        logger.info(f"HÖREN QUESTIONS COUNT: {len(vizu_horen_questions)}")
        logger.info(f"LESEN QUESTIONS COUNT: {len(vizu_lesen_questions)}")

        # =====================================================
        # DEBUG: VIZU-A1 PAPKASI ICHINI KO'RISH
        # =====================================================
        folder = "VIZU-A1"
        if os.path.exists(folder):
            files = os.listdir(folder)
            logger.info(f"VIZU-A1 FILES: {files}")
        else:
            logger.error("VIZU-A1 PAPKASI YO'Q!")

        init_vizu_attempts_table()
        init_vizu_lesen_results_table()
        init_vizu_horen_results_table()
        init_vizu_schreiben_results_table()
        init_vizu_sprechen_results_table()
        load_all_quizzes()
        reset_daily_scores()

        # =====================================================
        # CONFLICT OLDINI OLISH
        # =====================================================
        await bot.delete_webhook(drop_pending_updates=True)
        await asyncio.sleep(2)

        Thread(target=run_web, daemon=True).start()

        logger.info("BOT ISHGA TUSHDI ✅")
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
    except Exception as e:
        logger.error(f"CRITICAL MAIN ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())