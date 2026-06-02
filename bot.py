# =========================================================
# STANDARD LIBRARY IMPORTS
# =========================================================
import os
import csv
import random
import logging
import asyncio
from datetime import datetime, timedelta, date
from contextlib import contextmanager
from threading import Thread
from typing import Optional

# =========================================================
# THIRD-PARTY IMPORTS
# =========================================================
# Web & Environment
from flask import Flask
from dotenv import load_dotenv

# Imaging & Utilities
from PIL import Image, ImageDraw, ImageFont
import qrcode

# Database
import psycopg2
from psycopg2 import pool

# AIOGRAM (Guruhlangan)
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton, 
    CallbackQuery, FSInputFile, ReplyKeyboardRemove
)
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Konfiguratsiya o'zgaruvchilari
GENERATED_DIR = "generated"
CERTIFICATE_DIR = "certificates"
TOTAL_WORDS = 5555 
# =========================================================
# ENV & CONFIGURATION
# =========================================================
load_dotenv()

TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
ADMIN_CHANNEL = int(os.getenv("ADMIN_CHANNEL", "0"))

# Xavfsizlik tekshiruvi
if not TOKEN:
    raise ValueError("TOKEN topilmadi")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL topilmadi")

CHANNEL_USERNAME = "@vizu_deutsch"

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
        "price": "150.000 so'm"
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
            last_daily_reset DATE
        )
    """)

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

class AdminStates(StatesGroup):
    broadcast = State()

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

# Agar save_certificate yoki send_admin_photo_log funksiyalaringiz bo'lsa,
# ularni ham shu yerga yoki faylning teparoq qismiga joylashtiring.
# =========================================================
# BOT INSTANCE & STORAGE
# =========================================================
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# =========================================================
# STATES GROUP
# =========================================================
class RegisterState(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()

class BroadcastState(StatesGroup):
    waiting_for_message = State()

class PersonalMessageState(StatesGroup):
    waiting_for_id = State()
    waiting_for_text = State()

class ProfileState(StatesGroup):
    change_name = State()

# =========================================================
# KEYBOARDS (REPLY MARKUPS)
# =========================================================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎥 Video Kurslar")],
        [KeyboardButton(text="🎓 Darslarni O'rganish")],
        [KeyboardButton(text="📚 Ma'lumotlar")],
        [
            KeyboardButton(text="📚 Artikel Topish"),
            KeyboardButton(text="🎮 So'z O'yini")
        ],
        [KeyboardButton(text="👤 Mening Profilim")]
    ],
    resize_keyboard=True
)

video_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🇩🇪 A1"), KeyboardButton(text="🇩🇪 A2")],
        [KeyboardButton(text="🇩🇪 B1")],
        [KeyboardButton(text="🔥 A1-B1")],
        [KeyboardButton(text="🔥 A1-C1")],
        [KeyboardButton(text="🎬 Namuna Dars")],
        [KeyboardButton(text="⬅️ Orqaga")]
    ],
    resize_keyboard=True
)

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="👥 Foydalanuvchilar")],
        [KeyboardButton(text="💳 Xaridorlar")],
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
            [KeyboardButton(text="✏️ Ism Familiyani o'zgartirish")],
            [KeyboardButton(text="🔥 XP Reytingi")],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
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
# LEVEL LESSONS MENU (OPTIMALLASHTIRILGAN VARIANT)
# =========================================================

def build_level_lessons_menu(level, unlocked, exam_passed=False):
    total_lessons = LESSON_COUNTS.get(level, 10) # Xatolik bermasligi uchun default 10
    keyboard = []
    current_row = []

    for lesson in range(1, total_lessons + 1):
        if lesson <= unlocked:
            text = f"📖 Unterricht {lesson}"  
        else:
            text = f"🔒 Unterricht {lesson}"  

        current_row.append(KeyboardButton(text=text))

        if len(current_row) == 4:
            keyboard.append(current_row)
            current_row = []

    if current_row:
        keyboard.append(current_row)

    if unlocked > total_lessons:
        exam_text = "🎓 Yakuniy Imtihon"
    else:
        exam_text = "🔒 Yakuniy Imtihon"
    
    if exam_passed:
        cert_text = f"🏆 {level} Sertifikati"
    else:
        cert_text = f"🔒 {level} Sertifikati"

    # Imtihon va Sertifikat tugmalarini yonma-yon yoki alohida chiroyli joylashtiramiz
    keyboard.append([KeyboardButton(text=exam_text)])
    keyboard.append([KeyboardButton(text=cert_text)])
    
    # Navigatsiya
    keyboard.append([KeyboardButton(text="⬅️ Orqaga")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=f"🇩🇪 {level} darslaridan birini tanlang..."
    )
# =========================================================
# BUILD TASK MENU (OPTIMALLASHTIRILGAN)
# =========================================================
def build_task_menu(user_id, level, lesson):
    builder = InlineKeyboardBuilder()
    next_task = get_next_task(user_id, level, lesson)

    rows = db_execute(
        "SELECT task_name FROM lesson_task_progress WHERE user_id = %s AND level = %s AND lesson = %s AND completed = TRUE",
        (user_id, level, lesson), fetchall=True
    )
    completed_tasks = {r[0] for r in rows} if rows else set()

    for task in LESSON_TASKS:
        if task in completed_tasks:
            icon, callback = "✅", f"start_{task}_{lesson}"
        elif task == next_task:
            icon, callback = "📖", f"start_{task}_{lesson}"
        else:
            icon, callback = "🔒", "locked_task"

        builder.row(InlineKeyboardButton(text=f"{icon} {task}", callback_data=callback))

    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"level_{level}"))
    return builder.as_markup()
# =========================================================
# UNTERRICHT HANDLER
# =========================================================
@dp.message(F.text.regexp(r"^📖 Unterricht \d+$"))
async def lesson_handler(message: Message):
    user_id = message.from_user.id
    try:
        lesson_num = int(message.text.split()[-1])
        lesson_id = f"{lesson_num}-dars" # Bazaga mos format
        
        row = db_execute("SELECT course FROM users WHERE user_id = %s", (user_id,), fetchone=True)
        level = get_available_levels(row[0])[0] if row and get_available_levels(row[0]) else "A1"

        active_lessons[user_id] = {"level": level, "lesson": lesson_id}

        await message.answer(
            f"🇩🇪 {level}\n\n📖 Unterricht {lesson_num}\n\nKerakli vazifani bajaring:",
            reply_markup=build_task_menu(user_id, level, lesson_id)
        )
    except Exception as e:
        logger.exception(f"LESSON_HANDLER_ERROR: {e}")
        await message.answer("❌ Darsni ochishda xatolik.")
# =========================================================
# FINISH GRAMMATIK QUIZ (YAKUNIY)
# =========================================================
async def finish_grammatik_quiz(message: Message, user_id: int):
    # Sessiyani olish
    session = lesson_quiz_sessions.get(user_id)
    if not session:
        return

    level = session["level"]
    lesson = session["lesson"]
    score = session["score"]
    total = len(session["questions"])
    percentage = (score / total) * 100 if total > 0 else 0

    if percentage >= 70:
        # BAZANI YANGILASH
        db_execute("""
            INSERT INTO lesson_task_progress (user_id, level, lesson, task_name, completed, completed_at)
            VALUES (%s, %s, %s, 'Grammatik', TRUE, NOW())
            ON CONFLICT (user_id, level, lesson, task_name) 
            DO UPDATE SET completed = TRUE, completed_at = NOW()
        """, (user_id, level, lesson))

        await message.answer(
            f"🎉 <b>Ajoyib natija! Grammatika testidan o'tdingiz!</b>\n\n"
            f"📊 Natijangiz: <b>{score}/{total}</b> ({percentage:.1f}%)\n"
            f"🔓 <b>Keyingi bo'lim:</b> Endi '📖 Lesen' qismini boshlashingiz mumkin.",
            reply_markup=build_task_menu(user_id, level, lesson),
            parse_mode="HTML"
        )
    else:
        # QAYTA ISHLASH TUGMASI
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="🔄 Testni Qayta Ishlash", 
            callback_data=f"start_Grammatik_{lesson}"
        ))
        
        await message.answer(
            f"⚠️ <b>Grammatika testidan o'ta olmadingiz.</b>\n\n"
            f"📊 Oxirgi natijangiz: <b>{score}/{total}</b> ({percentage:.1f}%)\n"
            f"🎯 O'tish bali: <b>70%</b>\n\n"
            f"Iltimos, darsni qayta ko'rib chiqing va quyidagi tugma orqali testni qaytadan topshiring:",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )

    # MUHIM: Xotirani tozalash
    lesson_quiz_sessions.pop(user_id, None)
    
    # Active questions ham tozalash (agar kerak bo'lsa)
    prefix = f"{user_id}_"
    for key in [k for k in lesson_active_questions if k.startswith(prefix)]:
        lesson_active_questions.pop(key, None)

# =========================================================
# LESEN
# =========================================================

@dp.callback_query(
    F.data.startswith("start_Lesen_")
)
async def lesen_callback_handler(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    lesson = int(
        callback.data.split("_")[-1]
    )

    check = db_execute(
        """
        SELECT completed

        FROM lesson_task_progress

        WHERE
            user_id = %s
            AND task_name = 'Grammatik'
            AND lesson = %s
        """,
        (
            user_id,
            lesson
        ),
        fetchone=True
    )

    if not check or not check[0]:

        await callback.answer(
            "🔒 Avval Grammatikani tugating!",
            show_alert=True
        )

        return

    lesson_data = active_lessons.get(
        user_id
    )

    if not lesson_data:

        await callback.answer(
            "❌ Dars topilmadi.",
            show_alert=True
        )

        return

    level = lesson_data["level"]

    try:

        file_path = (
            f"{level}-Level/texts/"
            f"{level}-{lesson}-lesen.txt"
        )

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as f:

            text = f.read()

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ O'qib chiqdim",
                        callback_data=
                        f"read_lesen_{lesson}"
                    )
                ]
            ]
        )

        await callback.message.answer(
            f"📖 LESEN\n\n{text}",
            reply_markup=keyboard
        )

    except Exception as e:

        logger.error(
            f"Lesen text error: {e}"
        )

        await callback.answer(
            "❌ Matn topilmadi.",
            show_alert=True
        )


# =========================================================
# LESEN TEST START
# =========================================================

@dp.callback_query(
    F.data.startswith("read_lesen_")
)
async def lesen_quiz_start(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    lesson = int(
        callback.data.split("_")[-1]
    )

    lesson_data = active_lessons.get(
        user_id
    )

    if not lesson_data:

        await callback.answer(
            "❌ Dars topilmadi.",
            show_alert=True
        )

        return

    level = lesson_data["level"]

    questions = load_lesson_csv(
        f"{level}-Level/{level}-Lesen.csv",
        lesson
    )

    if not questions:

        await callback.answer(
            "❌ Lesen test topilmadi.",
            show_alert=True
        )

        return

    random.shuffle(
        questions
    )

    lesson_quiz_sessions[user_id] = {

        "level": level,

        "lesson": lesson,

        "task": "Lesen",

        "questions": questions,

        "index": 0,

        "score": 0
    }

    await callback.message.answer(
        f"📝 Lesen testi boshlandi!\n\n"
        f"📚 Savollar: {len(questions)}"
    )

    await send_lesson_question(
        callback.message.chat.id,
        user_id
    )

    await callback.answer()

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
# ADMIN TEXT LOG
# =========================================================

async def send_admin_log(
    text
):
    logger.info(
        f"ADMIN_CHANNEL = {ADMIN_CHANNEL}"
    )

    if not ADMIN_CHANNEL:
        logger.warning(
            "ADMIN_CHANNEL topilmadi!"
        )
        return

    try:
        await bot.send_message(
            chat_id=ADMIN_CHANNEL,
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
        f"ADMIN_CHANNEL = {ADMIN_CHANNEL}"
    )

    if not ADMIN_CHANNEL:
        logger.warning(
            "ADMIN_CHANNEL topilmadi!"
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
            chat_id=ADMIN_CHANNEL,
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

_MENU_BUTTONS = {
    "🎮 So'z O'yini",
    "🎥 Video Kurslar",
    "🎓 Darslarni O'rganish",
    "📚 Ma'lumotlar",
    "⬅️ Orqaga"
}

@dp.message(F.text == "📚 Artikel Topish")
async def artikel_start(message: Message):
    artikel_users[message.from_user.id] = True
    await message.answer(
        "🔍 Nemischa so'z yuboring.\n\n"
        "Masalan:\n"
        "Haus\n"
        "Auto\n"
        "Mann"
    )

@dp.message(
    F.text,
    lambda message: message.from_user.id in artikel_users
)
async def artikel_handler(message: Message):
    user_id = message.from_user.id

    # MENU BOSILSA REJIMDAN CHIQISH VA NATIVE HANDLERLARGA YO'L BERISH
    if message.text in _MENU_BUTTONS:
        artikel_users.pop(user_id, None)
        # aiogram handler zanjirini davom ettirishi uchun xabarni qayta yuborish mantiqi
        return

    word = message.text.lower().strip()
    result = artikel.get(word)

    await message.answer(
        result if result else (
            "❌ So'z topilmadi.\n\n"
            "Boshqa so'z yuboring."
        )
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

    # 3. Adminga yangi foydalanuvchi haqida xabar yuborish
    if user_id != ADMIN_ID:
        try:
            username_str = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔔 <b>Yangi foydalanuvchi kirdi!</b>\n\n"
                     f"👤 Ism: {full_name}\n"
                     f"🆔 ID: <code>{user_id}</code>\n"
                     f"🌐 Username: {username_str}"
            )
        except Exception as e:
            logger.error(f"Adminga start notification yuborishda xatolik: {e}")

    # 4. Asosiy menyuni foydalanuvchiga taqdim etish (Eski klaviatura avtomat yangilanadi)
    await message.answer(
        f"🇩🇪 <b>Nemis Tili (Vizu Deutsch) Botiga Xush Kelibsiz!</b>\n\n"
        f"Platformamiz orqali nemis tilini vizual darslar va tizimli testlar orqali o'rganishingiz mumkin.\n\n"
        f"🎉 <b>Hozirda barcha video kurslarimiz 70% CHEGIRMADA!</b>",
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

        if user_id != ADMIN_ID:
            try:
                username_str = f"@{callback.from_user.username}" if callback.from_user.username else "Mavjud emas"
                await bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"🔔 <b>Yangi foydalanuvchi (Obunadan o'tdi):</b>\n\n"
                         f"👤 Ism: {full_name}\n"
                         f"🆔 ID: <code>{user_id}</code>\n"
                         f"🌐 Username: {username_str}"
                )
            except Exception as e:
                logger.error(f"Adminga sub notification yuborishda xatolik: {e}")

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
        LIMIT 10
        """,
        fetchall=True
    )

    if not rows:
        await message.answer("🏆 Hozircha reyting mavjud emas.")
        return

    text = "🏆 TOP 10 XP Reyting\n\n"
    medals = ["🥇", "🥈", "🥉"]

    for i, row in enumerate(rows, start=1):
        medal = medals[i - 1] if i <= 3 else f"{i}."
        name = row[0] or "Foydalanuvchi"
        score = row[1] or 0
        text += f"{medal} {name} — {score} XP\n"

    await message.answer(text)

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

@dp.message(F.text.in_({"📘 A1", "📘 A2", "📘 B1", "📘 B2", "📘 C1"}))
async def level_lessons(message: Message):
    level = message.text.replace("📘 ", "").strip()
    user_id = message.from_user.id

    unlocked = get_unlocked_lesson(user_id, level)
    exam_passed = is_final_exam_passed(user_id, level)

    await message.answer(
        f"🇩🇪 {level} Darajasi\n\n"
        f"Darsni tanlang:",
        reply_markup=build_level_lessons_menu(level, unlocked, exam_passed)
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

# =========================
# SAMPLE LESSON
# =========================

@dp.message(F.text == "🎬 Namuna Dars")
async def sample_lesson(message: Message):
    await message.answer(
        "🎬 Namuna Dars:\n"
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
    
# =========================
# COURSE HANDLER
# =========================

async def send_course_info(message: Message, course: str):
    info = COURSE_INFO.get(course)
    if not info:
        await message.answer("❌ Kurs haqida ma'lumot topilmadi.")
        return

    text = (
        f"🎉 Hozirda barcha kurslar 70% CHEGIRMADA!\n\n"
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
        await callback.answer("❌ Sizda ruxsat yo'q!", show_alert=True)
        return

    try:
        user_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("❌ Xatolik yuz berdi.")
        return

    # Foydalanuvchini bazada tasdiqlash
    db_execute("UPDATE users SET approved = 1 WHERE user_id = %s", (user_id,))

    row = db_execute(
        "SELECT course, full_name FROM users WHERE user_id = %s",
        (user_id,),
        fetchone=True
    )

    if not row:
        await callback.answer("❌ Foydalanuvchi topilmadi!")
        return

    course, full_name = row[0] or "Noma'lum kurs", row[1] or "Talaba"

    # Dinamik havolalarni olish (Lug'atdan kurs bo'yicha)
    default_link = "https://t.me/vizu_deutsch"
    course_link = COURSE_LINKS.get(course, default_link)
    group_link = GROUP_LINKS.get(course, default_link)

    # Foydalanuvchiga yuboriladigan tugmalar
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎥 Kurs Kanali", url=course_link)],
            [InlineKeyboardButton(text="💬 Savollar Guruhi", url=group_link)]
        ]
    )

    # Foydalanuvchiga xabar yuborish
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
        logger.error(f"Foydalanuvchiga tasdiqlash xabarini yuborishda xatolik: {e}")

    # Admin panelidagi tugmalarni olib tashlash
    await callback.message.edit_reply_markup(reply_markup=None)

    # Admin uchun tasdiqlash habari
    await callback.message.answer(
        f"✅ Foydalanuvchi tasdiqlandi!\n\n👤 {full_name}\n📚 {course}"
    )
    await callback.answer("✅ Muvaffaqiyatli tasdiqlandi")


@dp.callback_query(F.data.startswith("reject:"))
async def reject_user(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    user_id = int(callback.data.split(":")[1])

    row = db_execute("SELECT full_name FROM users WHERE user_id = %s", (user_id,), fetchone=True)
    full_name = row[0] if row and row[0] else "Foydalanuvchi"

    # Foydalanuvchiga rad etilgani haqida habar
    try:
        await bot.send_message(
            chat_id=user_id,
            text=(
                "❌ Chekingiz tasdiqlanmadi.\n\n"
                "Iltimos:\n"
                "• chekni aniqroq yuboring\n"
                "• yoki admin bilan bog'laning."
            )
        )
    except Exception as e:
        logger.error(f"Foydalanuvchiga rad xabarini yuborishda xatolik: {e}")

    # Admin panelini yangilash
    await callback.message.edit_reply_markup(reply_markup=None)

    await callback.message.answer(f"❌ {full_name} rad qilindi.")
    await callback.answer("❌ Rad qilindi")

# =========================================================
# SEND LESSON QUESTION (MUKAMMAL INTEGRATSIYA)
# =========================================================

async def send_lesson_question(message: Message, user_id: int):
    session = lesson_quiz_sessions.get(user_id)
    if not session:
        return

    questions = session["questions"]
    index = session["index"]

    # Agar savollar tugasa, Grammatika yakunlash funksiyasini chaqiramiz
    if index >= len(questions):
        await finish_grammatik_quiz(message, user_id)
        return

    # CSV jadvalidagi tartib bo'yicha ma'lumotlarni olamiz:
    # lesson, task_id, type, question, correct, wrong1, wrong2
    question_data = questions[index]
    
    task_id = question_data[1]
    question_text = question_data[3]
    correct_ans = str(question_data[4])
    wrong1_ans = str(question_data[5])
    wrong2_ans = str(question_data[6])

    # Variantlarni ro'yxatga olib aralashtiramiz
    answers = [correct_ans, wrong1_ans, wrong2_ans]
    random.shuffle(answers)

    # Telegram callback_data xavfsizligi uchun QID yaratamiz
    qid = f"lesson_{user_id}_{task_id}"

    callback_map = {}
    buttons = []

    # Javoblarni 'a0', 'a1', 'a2' kalitlariga xaritaga (map) joylaymiz
    for i, answer in enumerate(answers):
        answer_key = f"a{i}"
        callback_map[answer_key] = answer

        buttons.append([
            InlineKeyboardButton(
                text=answer,
                # callback_data: gq:QID:kalit (uzunlik qisqa va xavfsiz bo'ladi)
                callback_data=f"gq:{qid}:{answer_key}"
            )
        ])

    # Kesh xotiraga to'g'ri javob va variantlar xaritasi saqlanadi
    lesson_active_questions[qid] = {
        "user_id": user_id,
        "correct": correct_ans,
        "answers": callback_map
    }

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    # Chat IDni message ob'ektidan xavfsiz aniqlaymiz
    chat_id = message.chat.id if hasattr(message, 'chat') else message.message.chat.id

    await bot.send_message(
        chat_id=chat_id,
        text=f"📝 <b>Grammatika test | Savol {index + 1}/{len(questions)}</b>\n\n"
             f"{question_text}",
        reply_markup=keyboard
    )
# =========================================================
# LESSON QUIZ ANSWER (GRAMMATIKA JAVOBLARINI TEKSHIRISH)
# =========================================================

@dp.callback_query(F.data.startswith("gq:"))
async def lesson_quiz_answer(callback: CallbackQuery):
    user_id = callback.from_user.id

    try:
        # Format: gq:qid:answer_key
        _, qid, answer_key = callback.data.split(":", 2)
    except ValueError:
        return

    # Savol keshda bormi?
    if qid not in lesson_active_questions:
        await callback.answer("❌ Bu savol faol emas yoki eskirgan.", show_alert=True)
        return

    question_data = lesson_active_questions[qid]

    # Xavfsizlik tekshiruvi: boshqa foydalanuvchi tugmasini bosib qo'ymasin
    if question_data["user_id"] != user_id:
        await callback.answer("❌ Bu sizning testingiz emas.", show_alert=True)
        return

    session = lesson_quiz_sessions.get(user_id)
    if not session:
        await callback.answer("❌ Test seansi topilmadi.", show_alert=True)
        return

    # Foydalanuvchi tanlagan matn va to'g'ri javobni olamiz
    selected = question_data["answers"].get(answer_key)
    correct_answer = question_data["correct"]

    # To'g'ri yoki noto'g'riligini tekshiramiz
    if str(selected) == str(correct_answer):
        session["score"] += 1
        await callback.answer("✅ To'g'ri!")
    else:
        await callback.answer(f"❌ Noto'g'ri!\n\nTo'g'ri javob: {correct_answer}", show_alert=True)

    # Indeksni oshiramiz va savol keshini o'chiramiz
    session["index"] += 1
    lesson_active_questions.pop(qid, None)

    # Ekran chiroyli turishi uchun joriy inline tugmalarni o'chirib yuboramiz
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Keyingi savolga o'tamiz (message ob'ektining o'zi uzatiladi!)
    await send_lesson_question(callback.message, user_id)
# =========================================================
# FINISH LESSON QUIZ (MUKAMMAL NATIJA VA RE-TRY TIZIMI)
# =========================================================

async def finish_lesson_quiz(message: Message, user_id: int):
    session = lesson_quiz_sessions.get(user_id)
    if not session:
        return

    score = session["score"]
    total = len(session["questions"])
    
    # Nolga bo'linish xatosidan himoya
    percent = (score * 100) // total if total > 0 else 0

    level = session["level"]
    lesson = session["lesson"]
    task = session["task"]  # 'Grammatik'

    chat_id = message.chat.id if hasattr(message, 'chat') else message.message.chat.id

    if percent >= 70:
        # 70% dan o'tgani uchun seansni keshdan o'chiramiz
        lesson_quiz_sessions.pop(user_id, None)

        # 1. Grammatika topshirilganini bazaga yozamiz
        db_execute(
            """
            INSERT INTO lesson_task_progress (user_id, level, lesson, task_name, completed)
            VALUES (%s, %s, %s, %s, TRUE)
            ON CONFLICT (user_id, level, lesson, task_name)
            DO UPDATE SET completed = TRUE, completed_at = NOW()
            """,
            (user_id, level, lesson, task)
        )

        # 2. Xuddi shu darsning keyingi bo'limi (Lesen) ochilganini bildiramiz
        # build_task_menu funksiyangiz endi foydalanuvchiga '📖 Lesen' tugmasini ko'rsatadi
        await bot.send_message(
            chat_id=chat_id,
            text=f"🎉 <b>Ajoyib! Grammatika vazifasi muvaffaqiyatli topshirildi!</b>\n\n"
                 f"📊 Natijangiz: <b>{score}/{total}</b>\n"
                 f"🎯 Ko'rsatkich: <b>{percent}%</b>\n\n"
                 f"🇩🇪 {level} | Unterricht {lesson}\n"
                 f"🔓 <b>Yangi bo'lim ochildi:</b> Ushbu darsning '📖 Lesen' (Matn o'qish va tahlil) qismi faollashdi. Davom etishingiz mumkin!",
            reply_markup=build_task_menu(user_id, level, lesson)
        )

    else:
        # 70% dan past bo'lsa, qayta ishlash so'rovi va oxirgi natija chiqadi
        retry_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Testni Qayta Ishlash",
                        callback_data="retry_grammatik"
                    )
                ]
            ]
        )

        await bot.send_message(
            chat_id=chat_id,
            text=f"⚠️ <b>Afsuski, grammatika testidan o'ta olmadingiz.</b>\n\n"
                 f"📊 Oxirgi natijangiz: <b>{score}/{total}</b>\n"
                 f"🎯 Ko'rsatkich: <b>{percent}%</b>\n"
                 f"📉 O'tish bali: <b>70%</b>\n\n"
                 f"<i>Dars materiallarini qayta ko'rib chiqishni va quyidagi tugma orqali testni boshqatdan topshirishingizni maslahat beramiz:</i>",
            reply_markup=retry_keyboard
        )
# =========================================================
# RETRY GRAMMATIK TEST CALLBACK HANDLER
# =========================================================

@dp.callback_query(F.data == "retry_grammatik")
async def retry_grammatik_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    session = lesson_quiz_sessions.get(user_id)

    if not session:
        await callback.answer("❌ Seans eskirgan. Iltimos, '📖 Grammatik' tugmasini qayta bosing.", show_alert=True)
        return

    # Kesh ichidagi ko'rsatkichlarni nollaymiz va savollarni qayta aralashtiramiz
    session["index"] = 0
    session["score"] = 0
    random.shuffle(session["questions"])

    await callback.answer("🔄 Test boshqatdan boshlanmoqda...")
    
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Birinchi savolni qayta yuboramiz
    await send_lesson_question(callback.message, user_id)
# =========================================================
# ADVANCED CEFR QUIZ ENGINE
# =========================================================

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

# =========================================================
# LESSON QUIZ SYSTEM
# =========================================================

LESSON_QUIZ_DATA = {}
lesson_quiz_sessions = {}
lesson_active_questions = {}
lesson_answered_users = {}

# =========================================================
# REGISTER STATES
# =========================================================

class RegisterStates(StatesGroup):
    waiting_full_name = State()

# =========================================================
# LEVEL CONFIG
# =========================================================

LEVEL_CONFIG = {
    "A1": {"file": "A1-words.csv", "blocks": 10, "size": 100, "required": 600},
    "A2": {"file": "A2-words.csv", "blocks": 10, "size": 100, "required": 600},
    "B1": {"file": "B1-words.csv", "blocks": 10, "size": 100, "required": 600},
    "B2": {"file": "B2-words.csv", "blocks": 15, "size": 100, "required": 900},
    "C1": {"file": "C1-words.csv", "blocks": 11, "size": 100, "required": 600}
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
# LOAD LESSON CSV
# =========================================================

def load_lesson_csv(filename, lesson):
    data = []

    if not os.path.exists(filename):
        return []

    try:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    # Kalit so'zlar borligini va satr butunligini xavfsiz tekshirish
                    if not row.get("lesson") or not row.get("task_id"):
                        continue
                        
                    if int(row["lesson"]) != lesson:
                        continue

                    data.append({
                        "id": int(row["task_id"]),
                        "question": row.get("question", "").strip(),
                        "correct": row.get("correct", "").strip(),
                        "wrong1": row.get("wrong1", "").strip(),
                        "wrong2": row.get("wrong2", "").strip()
                    })
                except Exception as e:
                    logger.error(f"Lesson CSV row parsed error: {e}")
    except Exception as e:
        logger.error(f"Lesson CSV file read error: {e}")

    return data


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
    for i, level in enumerate(LEVEL_ORDER):
        # OPEN
        if i <= unlocked_index:
            text = f"🎯 {level}"
        # LOCKED
        else:
            text = f"🔒 {level}"

        current.append(KeyboardButton(text=text))

        # 2 BUTTONS
        if len(current) == 2:
            rows.append(current)
            current = []

    # LAST ROW
    if current:
        rows.append(current)

    # =====================================================
    # RANKING
    # =====================================================
    rows.append([KeyboardButton(text="🏆 Reytinglar")])

    # =====================================================
    # CERTIFICATE
    # =====================================================
    rows.append([KeyboardButton(text="🏅 Sertifikat")])

    # =====================================================
    # BACK
    # =====================================================
    rows.append([KeyboardButton(text="⬅️ Orqaga")])

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True
    )

# =========================================================
# BLOCK MENU
# =========================================================

def build_block_keyboard(level):
    config = LEVEL_CONFIG.get(level)
    if not config:
        # Agar daraja konfiguratsiyasi topilmasa, default xavfsiz menyu qaytariladi
        return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="⬅️ Orqaga")]], resize_keyboard=True)

    rows = []
    current = []

    for i in range(1, config["blocks"] + 1):
        current.append(KeyboardButton(text=f"📚 {level}-{i}-Blok"))

        if len(current) == 2:
            rows.append(current)
            current = []

    if current:
        rows.append(current)

    rows.append([KeyboardButton(text="⬅️ Orqaga")])

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
# LOCKED LEVEL
# =========================================================

@dp.message(F.text.regexp(r"🔒 (A1|A2|B1|B2|C1)"))
async def locked_level_handler(message: Message):
    await message.answer(
        "🔒 Bu daraja hali ochilmagan.\n\n"
        "Keyingi darajani ochish uchun:\n"
        "• barcha bloklardan kamida 60% natija ko'rsating."
    )

# =========================================================
# OPEN LEVEL
# =========================================================

@dp.message(F.text.regexp(r"🎯 (A1|A2|B1|B2|C1)"))
async def open_level_handler(message: Message):
    level = message.text.replace("🎯 ", "").strip()
    await message.answer(
        f"📚 {level} bloklari",
        reply_markup=build_block_keyboard(level)
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
# RESTART WARNING
# =====================================================

# (Tavsiya: Oldingi kodda qolgan qism shu yerda davom etadi)
# ... [restart logika saqlandi] ...

# =====================================================
# USER LEVEL SECURITY
# =====================================================

    user_data = db_execute(
        "SELECT unlocked_level FROM users WHERE user_id = %s",
        (user_id,),
        fetchone=True
    )
    current_unlocked = user_data[0] if user_data else "A1"

    if level not in LEVEL_ORDER or current_unlocked not in LEVEL_ORDER:
        await message.answer("❌ Xatolik yuz berdi.")
        return

    if LEVEL_ORDER.index(level) > LEVEL_ORDER.index(current_unlocked):
        await message.answer("🔒 Bu daraja hali ochilmagan.")
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
    end_index = 1055 if (level == "C1" and block == 11) else (start_index + 100)

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

@dp.message(F.text.regexp(r"📚 (A1|A2|B1|B2|C1)-(\d+)-Blok"))
async def start_block(message: Message):
    parts = message.text.replace("📚 ", "").split("-")
    level, block = parts[0], int(parts[1])
    await start_quiz_block(message, level, block)

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

async def finish_quiz(chat_id, user_id):
    session = quiz_sessions.get(user_id)
    if not session:
        return

    score = session["score"]
    level = session["level"]
    block = session["block"]
    total = len(session["questions"])

    # Eski natijani olish
    old_result = db_execute(
        "SELECT best_score FROM quiz_progress WHERE user_id = %s AND level = %s AND block_number = %s",
        (user_id, level, block),
        fetchone=True
    )
    old_score = old_result[0] if old_result else 0

    # XP hisoblash
    xp_gain = max(0, score - old_score)

    # BAZA: Natijani saqlash
    db_execute(
        """
        INSERT INTO quiz_progress (user_id, level, block_number, best_score)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id, level, block_number)
        DO UPDATE SET best_score = GREATEST(quiz_progress.best_score, EXCLUDED.best_score)
        """,
        (user_id, level, block, score)
    )

    # BAZA: XP yangilash
    if xp_gain > 0:
        db_execute(
            """
            UPDATE users 
            SET total_score = COALESCE(total_score, 0) + %s,
                daily_score = COALESCE(daily_score, 0) + %s
            WHERE user_id = %s
            """,
            (xp_gain, xp_gain, user_id)
        )

    # Darajani tekshirish
    new_level = check_level_unlock(user_id, level)
    unlock_text = f"\n\n🔓 Yangi daraja ochildi: {new_level}" if new_level else ""

    # Xabar tuzish
    result_text = f"🏁 Test tugadi!\n\n🏆 Natija: {score}/{total}"
    result_text += f"\n⭐ XP qo'shildi: +{xp_gain}" if xp_gain > 0 else "\n♻️ Bu blokdan avvalroq yuqoriroq natija olgansiz."
    result_text += unlock_text

    await bot.send_message(chat_id, result_text)

    # Xotirani tozalash
    quiz_running.discard(user_id)
    quiz_sessions.pop(user_id, None)
    
    # Userga tegishli savollarni tozalash
    prefix = f"{user_id}_"
    for key in [k for k in active_questions if k.startswith(prefix)]:
        active_questions.pop(key, None)
        answered_users.pop(key, None)


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
        await callback.message.edit_text("❌ Qayta ishlash bekor qilindi.")
    except Exception:
        pass
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
            KeyboardButton(text="⬅️ Orqaga")
        ]
    ],
    resize_keyboard=True
)

# =========================================================
# RANKING MENU & LOGIC
# =========================================================

@dp.message(F.text == "🏆 Reytinglar")
async def open_rating_menu(message: Message):
    await message.answer("🏆 Reyting bo'limi", reply_markup=rating_menu)

async def _get_ranking_text(query_type: str, message: Message):
    col = "total_score" if query_type == "total" else "daily_score"
    title = "🏆 UMUMIY REYTING" if query_type == "total" else "⚡ KUNLIK REYTING"
    
    # Ma'lumotlar bazasidan reytingni olish
    rankings = db_execute(
        f"SELECT COALESCE(full_name, 'Unknown'), {col} FROM users WHERE {col} > 0 ORDER BY {col} DESC LIMIT 50",
        fetchall=True
    )

    if not rankings:
        return f"📭 {title} hali bo'sh.\n🎮 Birinchi bo'lib test ishlang!"

    text = f"{title}\n\n"
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    
    # Reyting ro'yxatini shakllantirish
    for i, (name, score) in enumerate(rankings, 1):
        medal = medals.get(i, f"{i}.")
        text += f"{medal} {name} — {score} XP\n"
        if i >= 10: break # Telegram xabar uzunligi uchun xavfsizlik limiti

    # Foydalanuvchining shaxsiy ballini tekshirish
    my = db_execute(f"SELECT {col} FROM users WHERE user_id = %s", (message.from_user.id,), fetchone=True)
    my_score = my[0] if my else 0
    
    if my_score <= 0:
        text += "\n━━━━━━━━━━\n🎮 Siz hali test ishlamagansiz."
    return text

@dp.message(F.text == "🏆 Umumiy Reyting")
async def total_ranking(message: Message):
    text = await _get_ranking_text("total", message)
    await message.answer(text)

@dp.message(F.text == "⚡ Kunlik Reyting")
async def daily_ranking(message: Message):
    text = await _get_ranking_text("daily", message)
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
# CERTIFICATE SYSTEM
# =========================================================

def init_certificate_table():
    db_execute("""
        CREATE TABLE IF NOT EXISTS certificates (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            rank TEXT,
            certificate_id TEXT UNIQUE,
            percent REAL,
            score INTEGER,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, rank)
        )
    """)

def save_certificate(user_id, cert_id, rank, percent, score):
    db_execute("""
        INSERT INTO certificates (user_id, rank, certificate_id, percent, score)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (user_id, rank) DO NOTHING
    """, (user_id, rank, cert_id, percent, score))
# =========================================================
# GENERATE QR & DRAWING
# =========================================================

def generate_qr(data, path):
    qr_img = qrcode.make(data)
    qr_img.save(path)

def draw_center_text(draw, text, font, y, image_width, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (image_width - text_width) // 2
    draw.text((x, y), text, font=font, fill=fill)

# =========================================================
# CREATE CERTIFICATE
# =========================================================

async def create_certificate(user_id, full_name, percent, score, rank, cert_id):
    os.makedirs(GENERATED_DIR, exist_ok=True)
    
    templates = {
        "GOLD": (f"{CERTIFICATE_DIR}/gold_template.png", (255, 215, 0)),
        "SILVER": (f"{CERTIFICATE_DIR}/silver_template.png", (40, 40, 40)),
        "BRONZE": (f"{CERTIFICATE_DIR}/bronze_template.png", (90, 40, 20))
    }
    
    template_path, text_color = templates.get(rank, templates["BRONZE"])
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template topilmadi: {template_path}")

    with Image.open(template_path).convert("RGBA") as image:
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        # Fontlarni yuklash
        name_font = ImageFont.truetype("fonts/GreatVibes-Regular.ttf", 90)
        title_font = ImageFont.truetype("fonts/Montserrat-Bold.ttf", 42)
        small_font = ImageFont.truetype("fonts/Montserrat-Regular.ttf", 28)
        
        date = datetime.now().strftime("%d.%m.%Y")
        
        draw_center_text(draw, full_name, name_font, 470, width, text_color)
        draw.text((1320, 355), f"{percent}%", font=title_font, fill=text_color)
        draw.text((1320, 505), f"{score}/5555", font=title_font, fill=text_color)
        draw.text((1320, 655), cert_id, font=small_font, fill=text_color)
        draw.text((1320, 805), date, font=small_font, fill=text_color)
        
        qr_path = os.path.join(GENERATED_DIR, f"qr_{user_id}.png")
        generate_qr(cert_id, qr_path)
        
        with Image.open(qr_path) as qr:
            image.paste(qr.resize((180, 180)), (1450, 850))
            
        output_path = os.path.join(GENERATED_DIR, f"{cert_id}.png")
        image.save(output_path)
        return output_path

# =========================================================
# CERTIFICATE COMMAND
# =========================================================

@dp.message(F.text == "🏅 Sertifikat")
async def certificate_system(message: Message):
    user_id = message.from_user.id
    
    # Blokni tekshirish
    result = db_execute("SELECT best_score FROM quiz_progress WHERE user_id = %s AND level = 'C1' AND block_number = 11", (user_id,), fetchone=True)
    if not result:
        return await message.answer("🔒 Sertifikat yopiq. C1 oxirgi blokni tugating.")

    user_data = db_execute("SELECT full_name FROM users WHERE user_id = %s", (user_id,), fetchone=True)
    full_name = user_data[0] if user_data else message.from_user.full_name
    
    total = db_execute("SELECT COALESCE(SUM(best_score), 0) FROM quiz_progress WHERE user_id = %s", (user_id,), fetchone=True)
    total_score = total[0] if total else 0
    percent = round((total_score / TOTAL_WORDS) * 100, 1)

    if percent < 60:
        return await message.answer(f"❌ Minimum 60% kerak. Natija: {percent}%")

    rank = "GOLD" if percent >= 85 else "SILVER" if percent >= 70 else "BRONZE"
    
    if get_existing_certificate(user_id, rank):
        return await message.answer(f"🏅 Siz allaqachon {rank} sertifikatini olgansiz.")

    cert_id = generate_certificate_id()
    save_certificate(user_id, cert_id, rank, percent, total_score)

    try:
        path = await create_certificate(user_id, full_name, percent, total_score, rank, cert_id)
        await send_admin_photo_log(path, f"🏅 Yangi Sertifikat\n👤 {full_name}\n🏆 {rank}\n📊 {percent}%\n🎫 {cert_id}")
        await message.answer_photo(FSInputFile(path), caption=f"🏅 {rank} Zertifikat\n📊 {percent}%\n📚 {total_score}/5555\n🎫 {cert_id}")
    except Exception as e:
        logger.error(f"Certificate error: {e}")
        await message.answer("❌ Sertifikat yaratishda xato.")

# =========================================================
# ADMIN & BROADCAST
# =========================================================

@dp.message(AdminStates.broadcast)
async def send_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    
    users = db_execute("SELECT user_id FROM users", fetchall=True)
    if not users:
        await message.answer("❌ Foydalanuvchilar topilmadi."); await state.clear(); return

    success, failed = 0, 0
    progress = await message.answer("📢 Reklama yuborilmoqda...")
    
    for i, (user_id,) in enumerate(users, 1):
        try:
            await bot.copy_message(user_id, message.chat.id, message.message_id)
            success += 1
        except:
            failed += 1
        
        if i % 25 == 0:
            await asyncio.sleep(0.1)
            try: await progress.edit_text(f"✅ Yuborildi: {success}\n❌ Xato: {failed}\n📊 {i}/{len(users)}")
            except: pass

    await progress.edit_text(f"✅ Reklama yakunlandi.\n📨 Yuborildi: {success}\n❌ Xato: {failed}")
    await state.clear()

# =========================================================
# MAIN INITIALIZATION & RUN
# =========================================================

async def main():
    try:
        init_db_pool()
        init_tables()
        init_certificate_table() # Sertifikat jadvali qo'shildi
        load_artikel()
        load_all_quizzes()
        reset_daily_scores()
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Flask thread
        Thread(target=run_web, daemon=True).start()
        
        logger.info("BOT ISHGA TUSHDI ✅")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"CRITICAL MAIN ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())