from flask import Flask
from threading import Thread
from dotenv import load_dotenv
import os
import asyncio
import csv
import random
import logging

from PIL import (
    Image,
    ImageDraw,
    ImageFont
)

import qrcode
from datetime import datetime, timedelta, date

from contextlib import contextmanager

import psycopg2
from psycopg2 import pool

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    FSInputFile,
    ReplyKeyboardRemove,
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================================================
# ENV
# =========================================================

import os

from dotenv import load_dotenv

load_dotenv()

# =========================================================
# TOKENS
# =========================================================

TOKEN = os.getenv(
    "TOKEN"
)

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

# =========================================================
# ADMINS
# =========================================================

ADMIN_ID = int(
    os.getenv(
        "ADMIN_ID",
        "0"
    )
)

ADMIN_PASSWORD = os.getenv(
    "ADMIN_PASSWORD",
    ""
)

ADMIN_CHANEL = int(
    os.getenv(
        "ADMIN_CHANEL",
        "0"
    )
)

# =========================================================
# SECURITY CHECK
# =========================================================

if not TOKEN:

    raise ValueError(
        "TOKEN topilmadi"
    )

if not DATABASE_URL:

    raise ValueError(
        "DATABASE_URL topilmadi"
    )

# =========================================================
# CONFIG
# =========================================================

CHANNEL_USERNAME = "@vizu_deutsch"

# =========================================================
# COURSE LINKS
# =========================================================

COURSE_LINKS = {

    "🇩🇪 A1":
    "https://t.me/+Y0ilZiDqgTJjZjMy",

    "🇩🇪 A2":
    "https://t.me/+Co8biP05FtViZGEy",

    "🇩🇪 B1":
    "https://t.me/+XcBAw2lLmdlmNDky",

    "🔥 A1-B1":
    "https://t.me/+ILaI0GhJkS1jYmQy",

    "🔥 A1-C1":
    "https://t.me/+J7IoPtpXu0s3ZGIy",
}

# =========================================================
# GROUP LINKS
# =========================================================

GROUP_LINKS = {

    "🇩🇪 A1":
    "https://t.me/+_76BNOk0NTgxODRi",

    "🇩🇪 A2":
    "https://t.me/+syhRWPBkeoxlZjQy",

    "🇩🇪 B1":
    "https://t.me/+6vSnu6iFLBI1ZGIy",

    "🔥 A1-B1":
    "https://t.me/+ILaI0GhJkS1jYmQy",

    "🔥 A1-C1":
    "https://t.me/+J7IoPtpXu0s3ZGIy",
}

# =========================================================
# COURSE INFO
# =========================================================

COURSE_INFO = {

    "🇩🇪 A1": {

        "lessons": 14,

        "price": "100.000 so'm"
    },

    "🇩🇪 A2": {

        "lessons": 14,

        "price": "150.000 so'm"
    },

    "🇩🇪 B1": {

        "lessons": 20,

        "price": "200.000 so'm"
    },

    "🔥 A1-B1": {

        "lessons": 48,

        "price": "300.000 so'm"
    },

    "🔥 A1-C1": {

        "lessons": 100,

        "price": "600.000 so'm"
    },
}

# =========================================================
# DATABASE
# =========================================================

db_pool = None

# =========================================================
# INIT DATABASE POOL
# =========================================================

def init_db_pool():

    global db_pool

    try:

        # OLD POOL CLOSE
        if db_pool:

            try:

                db_pool.closeall()

            except:
                pass

        db_pool = pool.ThreadedConnectionPool(

            minconn=1,

            maxconn=20,

            dsn=DATABASE_URL
        )

        logger.info(
            "Database connected ✅"
        )

    except Exception as e:

        logger.error(
            f"Database pool error: {e}"
        )

        raise

# =========================================================
# DATABASE CONNECTION
# =========================================================

@contextmanager
def get_db():

    global db_pool

    conn = None

    try:

        # RECONNECT
        if not db_pool:

            init_db_pool()

        try:

            conn = db_pool.getconn()

        except Exception as e:

            logger.error(
                f"Reconnect DB: {e}"
            )

            init_db_pool()

            conn = db_pool.getconn()

        yield conn

        conn.commit()

    except Exception as e:

        if conn:

            try:
                conn.rollback()

            except:
                pass

        logger.error(
            f"DB transaction error: {e}"
        )

        raise

    finally:

        if conn and db_pool:

            try:

                db_pool.putconn(conn)

            except Exception as e:

                logger.error(
                    f"Return connection error: {e}"
                )

# =========================================================
# DATABASE EXECUTE
# =========================================================

def db_execute(
    query,
    params=(),
    fetchone=False,
    fetchall=False
):

    try:

        with get_db() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    query,
                    params
                )

                # FETCH ONE
                if fetchone:

                    return cur.fetchone()

                # FETCH ALL
                if fetchall:

                    return cur.fetchall()

        return None

    except Exception as e:

        logger.error(
            f"DB execute error: {e}"
        )

        return None

# =========================================================
# INIT TABLES
# =========================================================

def init_tables():
    # =====================================================
    # USERS TABLE
    # =====================================================

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

    # =====================================================
    # QUIZ PROGRESS
    # =====================================================

    db_execute("""
        CREATE TABLE IF NOT EXISTS quiz_progress (

            user_id BIGINT,

            level TEXT,

            block_number INTEGER,

            best_score INTEGER DEFAULT 0,

            PRIMARY KEY(
                user_id,
                level,
                block_number
            )
        )
    """)

    # =====================================================
    # SAFE MIGRATIONS
    # =====================================================

    try:

        db_execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS score
            INTEGER DEFAULT 0
        """)

    except Exception as e:

        logger.error(e)

    try:

        db_execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS course
            TEXT
        """)

    except Exception as e:

        logger.error(e)

    try:

        db_execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS total_score
            INTEGER DEFAULT 0
        """)

    except Exception as e:

        logger.error(e)

    try:

        db_execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS daily_score
            INTEGER DEFAULT 0
        """)

    except Exception as e:

        logger.error(e)

    try:

        db_execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS unlocked_level
            TEXT DEFAULT 'A1'
        """)

    except Exception as e:

        logger.error(e)

    try:

        db_execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS last_daily_reset
            DATE
        """)

    except Exception as e:

        logger.error(e)

    # =====================================================
    # INDEXES
    # =====================================================

    db_execute("""
        CREATE INDEX IF NOT EXISTS idx_users_score
        ON users(score)
    """)

    db_execute("""
        CREATE INDEX IF NOT EXISTS idx_users_approved
        ON users(approved)
    """)

    db_execute("""
        CREATE INDEX IF NOT EXISTS idx_users_course
        ON users(course)
    """)

    db_execute("""
        CREATE INDEX IF NOT EXISTS idx_users_total_score
        ON users(total_score)
    """)

    db_execute("""
        CREATE INDEX IF NOT EXISTS idx_users_daily_score
        ON users(daily_score)
    """)

    db_execute("""
        CREATE INDEX IF NOT EXISTS idx_quiz_progress_user
        ON quiz_progress(user_id)
    """)

    db_execute("""
        CREATE INDEX IF NOT EXISTS idx_quiz_progress_level
        ON quiz_progress(level)
    """)

    logger.info(
        "Database tables ready ✅"
    )

# =========================
# FLASK
# =========================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running ✅"


def run_web():

    port = int(
        os.environ.get("PORT", 10000)
    )

    app.run(
    host="0.0.0.0",
    port=port,
    debug=False,
    use_reloader=False
)
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
        [KeyboardButton(text="🎥 Video Kurslar")],
        [KeyboardButton(text="📚 Artikel Topish"), KeyboardButton(text="🎮 So'z O'yini")],
        [KeyboardButton(text="👨‍🏫 Ustoz haqida"), KeyboardButton(text="🏆 Natijalar")],
        [KeyboardButton(text="📞 Admin bilan bog'lanish")],
    ],
    resize_keyboard=True,
)
video_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🇩🇪 A1"), KeyboardButton(text="🇩🇪 A2")],
        [KeyboardButton(text="🇩🇪 B1")],
        [KeyboardButton(text="🔥 A1-B1")],
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

# =========================
# HELPERS
# =========================

def is_admin(
    message: Message
) -> bool:

    return (
        message.from_user.id
        == ADMIN_ID
    )

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

    # CHANNEL DISABLED
    if ADMIN_CHANEL == 0:

        return

    try:

        await bot.send_message(

            ADMIN_CHANEL,

            text
        )

    except Exception as e:

        logger.error(
            f"Admin log error: {e}"
        )

# =========================================================
# ADMIN PHOTO LOG
# =========================================================

async def send_admin_photo_log(

    photo_path,

    caption
):

    # CHANNEL DISABLED
    if ADMIN_CHANEL == 0:

        return

    # FILE CHECK
    if not os.path.exists(
        photo_path
    ):

        logger.warning(
            f"Photo not found: "
            f"{photo_path}"
        )

        return

    try:

        await bot.send_photo(

            ADMIN_CHANEL,

            FSInputFile(photo_path),

            caption=caption
        )

    except Exception as e:

        logger.error(
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

# user_id -> last active timestamp
artikel_users: dict[int, float] = {}

def load_artikel():

    csv_path = "nouns.csv"

    if not os.path.exists(csv_path):

        logger.warning(
            "nouns.csv not found — Artikel feature disabled."
        )

        return

    with open(csv_path, "r", encoding="utf-8") as f:

        reader = csv.DictReader(f)

        for row in reader:

            try:

                word = row["lemma"].lower().strip()

                gender = str(
                    row["genus"]
                ).lower().strip()

                art_map = {
                    "m": "der",
                    "f": "die",
                    "n": "das"
                }

                art = art_map.get(gender)

                if art:

                    artikel[word] = (
                        f"{art} {word.capitalize()}"
                    )

            except Exception as e:

                logger.error(e)

    logger.info(
        f"Artikel loaded: {len(artikel)} words"
    )
# =========================
# START
# =========================
@dp.message(CommandStart())
async def cmd_start(message: Message):

    user_id = message.from_user.id

    # eski keyboardni tozalash
    await message.answer(
        "🔄 Menu yangilanmoqda...",
        reply_markup=ReplyKeyboardRemove()
    )

    await asyncio.sleep(1)

    # Kanal obunasini tekshirish
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
            "❌ Botdan foydalanish uchun kanalga a'zo bo'ling.",
            reply_markup=keyboard
        )

        return

    # userni bazaga qo'shish
    db_execute(
        "INSERT INTO users (user_id, approved) "
        "VALUES (%s, 0) "
        "ON CONFLICT DO NOTHING",
        (user_id,)
    )

    # admin notification
    if user_id != ADMIN_ID:

        try:

            await bot.send_message(
                ADMIN_ID,
                f"🔔 Yangi foydalanuvchi!\n\n"
                f"👤 Ism: {message.from_user.full_name}\n"
                f"🆔 ID: {user_id}\n"
                f"Username: @{message.from_user.username}",
            )

        except Exception as e:

            logger.error(e)

    # main menu
    await message.answer(
        "🇩🇪 Nemis Tili Video Darslari Botiga "
        "Xush Kelibsiz!\n\n"
        "🎉 Hozirda barcha kurslar "
        "50% CHEGIRMADA!",
        reply_markup=main_menu,
    )

# =========================
# CHECK SUBSCRIPTION BUTTON
# =========================

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):

    user_id = callback.from_user.id

    # qayta tekshiradi
    if await check_subscription(user_id):

        # bazaga qo'shadi
        db_execute(
            "INSERT INTO users (user_id, approved) "
            "VALUES (%s, 0) "
            "ON CONFLICT DO NOTHING",
            (user_id,)
        )

        # eski xabarni o'chiradi
        try:
            await callback.message.delete()
        except:
            pass

        # admin notification
        if user_id != ADMIN_ID:

            try:

                await bot.send_message(
                    ADMIN_ID,
                    f"🔔 Yangi foydalanuvchi!\n\n"
                    f"👤 Ism: {callback.from_user.full_name}\n"
                    f"🆔 ID: {user_id}\n"
                    f"Username: @{callback.from_user.username}",
                )

            except Exception as e:

                logger.error(e)

        # userga menu chiqaradi
        await callback.message.answer(
            "✅ Obuna tasdiqlandi!\n\n"
            "🇩🇪 Botga xush kelibsiz.",
            reply_markup=main_menu
        )

        await callback.answer()

    else:

        await callback.answer(
            "❌ Hali kanalga a'zo bo'lmagansiz.",
            show_alert=True
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
    artikel_users.pop(message.from_user.id, None)
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
   artikel_users.pop(message.from_user.id, None) 
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

@dp.message(F.text == "🇩🇪 A1")
async def course_a1(message: Message): await send_course_info(message, "🇩🇪 A1")

@dp.message(F.text == "🇩🇪 A2")
async def course_a2(message: Message): await send_course_info(message, "🇩🇪 A2")

@dp.message(F.text == "🇩🇪 B1")
async def course_b1(message: Message): await send_course_info(message, "🇩🇪 B1")


@dp.message(F.text == "🔥 A1-B1")
async def course_a1b1(message: Message): await send_course_info(message, "🔥 A1-B1")

@dp.message(F.text == "🔥 A1-C1")
async def course_a1c1(message: Message): await send_course_info(message, "🔥 A1-C1")
# =========================
# CHECK PHOTO (payment receipt)
# =========================

@dp.message(F.photo)
async def check_photo(
    message: Message,
    state: FSMContext
):

    # user kurs tanlaganmi
    row = db_execute(
        "SELECT course FROM users "
        "WHERE user_id = %s",
        (message.from_user.id,),
        fetchone=True
    )

    if not row or not row[0]:

        await message.answer(
            "❌ Avval kurs tanlang."
        )

        return

    # photo save
    await state.update_data(
        photo=message.photo[-1].file_id
    )

    # next step
    await message.answer(
        "👤 Ism va familiyangizni yuboring:"
    )

    await state.set_state(
        RegisterState.waiting_for_name
    )


@dp.message(RegisterState.waiting_for_name)
async def get_name(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        full_name=message.text.strip()
    )

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
        "📱 Telefon raqamingizni yuboring:",
        reply_markup=keyboard
    )

    await state.set_state(
        RegisterState.waiting_for_phone
    )


@dp.message(RegisterState.waiting_for_phone)
async def get_phone(
    message: Message,
    state: FSMContext
):

    if message.contact:

        phone = (
            message.contact.phone_number
        )

    else:

        phone = message.text.strip()

        if len(phone) < 7:

            await message.answer(
                "❌ Telefon raqam noto'g'ri.\n\n"
                "Qayta yuboring."
            )

            return

    data = await state.get_data()

    photo = data["photo"]

    full_name = data["full_name"]

    user = message.from_user

    # selected course
    row = db_execute(
        "SELECT course FROM users "
        "WHERE user_id = %s",
        (user.id,),
        fetchone=True
    )

    course = (
        row[0]
        if row and row[0]
        else "Kurs tanlanmagan"
    )

    # save user info
    db_execute(
        "UPDATE users "
        "SET full_name = %s, phone = %s "
        "WHERE user_id = %s",
        (
            full_name,
            phone,
            user.id
        ),
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Approve",
                    callback_data=(
                        f"approve:{user.id}"
                    )
                ),
                InlineKeyboardButton(
                    text="❌ Reject",
                    callback_data=(
                        f"reject:{user.id}"
                    )
                ),
            ]
        ]
    )

    caption = (
        f"💳 Yangi xaridor!\n\n"
        f"👤 Ism: {full_name}\n"
        f"📱 Telefon: {phone}\n\n"
        f"🆔 ID: {user.id}\n"
        f"📚 Kurs: {course}\n\n"
        f"Username: @{user.username}"
    )

    await bot.send_photo(
        ADMIN_ID,
        photo=photo,
        caption=caption,
        reply_markup=keyboard
    )

    await message.answer(
        "✅ Ma'lumotlaringiz "
        "adminga yuborildi!\n\n"
        "⏳ Tasdiqlanishini kuting.",
        reply_markup=main_menu,
    )

    await state.clear()
# =========================
# APPROVE / REJECT
# =========================

@dp.callback_query(F.data.startswith("approve:"))
async def approve_user(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:

        await callback.answer(
            "❌ Ruxsat yo'q",
            show_alert=True
        )

        return

    user_id = int(
        callback.data.split(":")[1]
    )

    db_execute(
        "UPDATE users "
        "SET approved = 1 "
        "WHERE user_id = %s",
        (user_id,)
    )

    row = db_execute(
        "SELECT course, full_name "
        "FROM users "
        "WHERE user_id = %s",
        (user_id,),
        fetchone=True
    )

    if not row:

        await callback.answer(
            "❌ User topilmadi"
        )

        return

    course = row[0]

    full_name = row[1] or "Student"

    course_link = COURSE_LINKS.get(
        course
    )

    group_link = GROUP_LINKS.get(
        course
    )

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

    await bot.send_message(
        user_id,
        f"🎉 Assalomu alaykum, {full_name}!\n\n"
        f"✅ To'lovingiz muvaffaqiyatli tasdiqlandi.\n\n"
        f"📚 Kurs: {course}\n\n"
        f"👇 Quyidagi tugmalar orqali kursga qo‘shiling.",
        reply_markup=keyboard
    )

    try:

        await callback.message.edit_reply_markup(
            reply_markup=None
        )

    except Exception as e:

        logger.error(e)

    await callback.message.answer(
        f"✅ User tasdiqlandi\n\n"
        f"👤 {full_name}\n"
        f"📚 {course}"
    )

    await callback.answer(
        "✅ Tasdiqlandi"
    )


@dp.callback_query(F.data.startswith("reject:"))
async def reject_user(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:

        await callback.answer(
            "❌ Ruxsat yo'q",
            show_alert=True
        )

        return

    user_id = int(
        callback.data.split(":")[1]
    )

    row = db_execute(
        "SELECT full_name "
        "FROM users "
        "WHERE user_id = %s",
        (user_id,),
        fetchone=True
    )

    full_name = (
        row[0]
        if row else "User"
    )

    await bot.send_message(
        user_id,
        "❌ Chekingiz tasdiqlanmadi.\n\n"
        "Iltimos:\n"
        "• chekni aniqroq yuboring\n"
        "• yoki admin bilan bog'laning."
    )

    try:

        await callback.message.edit_reply_markup(
            reply_markup=None
        )

    except Exception as e:

        logger.error(e)

    await callback.message.answer(
        f"❌ User rad qilindi\n\n"
        f"👤 {full_name}"
    )

    await callback.answer(
        "❌ Rad qilindi"
    )
# =========================================================
# ADVANCED CEFR QUIZ ENGINE
# =========================================================

import os
import csv
import random

from datetime import date

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

# =========================================================
# GLOBALS
# =========================================================

# QUIZ DATA
QUIZ_DATA = {}

# ACTIVE QUIZ USERS
quiz_running = set()

# USER QUIZ SESSIONS
quiz_sessions = {}

# ACTIVE QUESTIONS
active_questions = {}

# ANSWER TRACKING
answered_users = {}

# APPROVED USERS CACHE
approved_users = set()

# ARTIKEL DATA
artikel_data = {}

# ADMIN CACHE
admin_sessions = {}

# DAILY RESET TRACKER
last_daily_reset = None

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

        "required": 600
    }
}

LEVEL_ORDER = [

    "A1",

    "A2",

    "B1",

    "B2",

    "C1"
]
# =========================================================
# LOAD CSV
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATA_DIR = BASE_DIR

def load_level_csv(
    level,
    filename
):

    data = []

    # =====================================================
    # FILE CHECK
    # =====================================================

    if not os.path.exists(filename):

        logger.warning(
            f"{filename} topilmadi"
        )

        # ADMIN WARNING
        try:

            asyncio.create_task(
                bot.send_message(
                    ADMIN_ID,
                    f"⚠️ CSV topilmadi:\n{filename}"
                )
            )

        except Exception as e:

            logger.error(
                f"CSV warning error: {e}"
            )

        return

    # =====================================================
    # LOAD FILE
    # =====================================================

    try:

        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as f:

            reader = csv.reader(f)

            # HEADER SKIP
            next(reader, None)

            for row in reader:

                try:

                    # INVALID ROW
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

                    logger.error(
                        f"CSV row error: {e}"
                    )

    except Exception as e:

        logger.error(
            f"CSV load error: {e}"
        )

        return

    # =====================================================
    # SAVE DATA
    # =====================================================

    QUIZ_DATA[level] = data

    logger.info(
        f"{level}: "
        f"{len(data)} loaded ✅"
    )

# =========================================================
# LOAD ALL QUIZZES
# =========================================================

def load_all_quizzes():

    QUIZ_DATA.clear()

    for level, config in LEVEL_CONFIG.items():

        try:

            load_level_csv(
                level,
                config["file"]
            )

        except Exception as e:

            logger.error(
                f"{level} load failed: {e}"
            )

    logger.info(
        "All quizzes loaded ✅"
    )
# =========================================================
# DAILY RESET
# =========================================================

def reset_daily_scores():

    today = date.today()

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
# =========================================================
# QUIZ MENU
# =========================================================

async def build_level_menu(
    user_id
):

    result = db_execute(
        """
        SELECT unlocked_level

        FROM users

        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    unlocked = (
        result[0]
        if result
        else "A1"
    )

    unlocked_index = LEVEL_ORDER.index(
        unlocked
    )

    rows = []

    current = []

    # =====================================================
    # LEVELS
    # =====================================================

    for i, level in enumerate(
        LEVEL_ORDER
    ):

        # OPEN
        if i <= unlocked_index:

            text = (
                f"🎯 {level}"
            )

        # LOCKED
        else:

            text = (
                f"🔒 {level}"
            )

        current.append(

            KeyboardButton(
                text=text
            )
        )

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

    rows.append([

        KeyboardButton(
            text="🏆 Reytinglar"
        )
    ])

    # =====================================================
    # CERTIFICATE
    # =====================================================

    rows.append([

        KeyboardButton(
            text="🏅 Sertifikat"
        )
    ])

    # =====================================================
    # BACK
    # =====================================================

    rows.append([

        KeyboardButton(
            text="⬅️ Orqaga"
        )
    ])

    return ReplyKeyboardMarkup(

        keyboard=rows,

        resize_keyboard=True
    )

# =========================================================
# BLOCK MENU
# =========================================================

def build_block_keyboard(level):

    config = LEVEL_CONFIG[level]

    rows = []

    current = []

    for i in range(1, config["blocks"] + 1):

        current.append(
            KeyboardButton(
                text=f"📚 {level}-{i}-Blok"
            )
        )

        if len(current) == 2:

            rows.append(current)

            current = []

    if current:
        rows.append(current)

    rows.append([
        KeyboardButton(
            text="⬅️ Orqaga"
        )
    ])

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True
    )

# =========================================================
# OPEN WORD GAME
# =========================================================

@dp.message(F.text == "🎮 So'z O'yini")
async def word_game_handler(
    message: Message,
    state: FSMContext
):

    user_id = message.from_user.id

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

    full_name = (
        result[0]
        if result
        else None
    )

    # =====================================================
    # ASK NAME
    # =====================================================

    if (
        not full_name
        or
        full_name == "Unknown"
    ):

        await message.answer(

            "📝 To'liq ism familiyangizni kiriting.\n\n"

            "Masalan:\n"
            "Zayniddinkhuja Makhmudov"
        )

        await state.set_state(
            RegisterStates.waiting_full_name
        )

        return

    # =====================================================
    # OPEN MENU
    # =====================================================

    menu = await build_level_menu(
        user_id
    )

    await message.answer(

        "🎮 WortSpiel\n\n"
        "Darajani tanlang:",

        reply_markup=menu
    )
# =========================================================
# SAVE FULL NAME
# =========================================================

@dp.message(
    RegisterStates.waiting_full_name
)
async def save_full_name(
    message: Message,
    state: FSMContext
):

    user_id = message.from_user.id

    full_name = (
        message.text.strip()
    )

    # =====================================================
    # VALIDATION
    # =====================================================

    if len(full_name) < 5:

        await message.answer(
            "❌ Juda qisqa ism."
        )

        return

    if len(full_name) > 50:

        await message.answer(
            "❌ Juda uzun ism."
        )

        return

    # AT LEAST 2 WORDS
    if len(full_name.split()) < 2:

        await message.answer(

            "❌ Ism va familiya kiriting.\n\n"

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
        (
            full_name,
            user_id
        )
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

    menu = await build_level_menu(
        user_id
    )

    await message.answer(

        "🎮 WortSpiel\n\n"
        "Darajani tanlang:",

        reply_markup=menu
    )

# =========================================================
# LOCKED LEVEL
# =========================================================

@dp.message(
    F.text.regexp(
        r"🔒 (A1|A2|B1|B2|C1)"
    )
)
async def locked_level_handler(
    message: Message
):

    await message.answer(
        "🔒 Bu daraja hali ochilmagan.\n\n"
        "Keyingi darajani ochish uchun:\n"
        "• barcha bloklardan kamida 60% ishlang."
    )

# =========================================================
# OPEN LEVEL
# =========================================================

@dp.message(
    F.text.regexp(
        r"🎯 (A1|A2|B1|B2|C1)"
    )
)
async def open_level_handler(
    message: Message
):

    level = message.text.replace(
        "🎯 ",
        ""
    )

    await message.answer(
        f"📚 {level} bloklari",
        reply_markup=build_block_keyboard(level)
    )

# =========================================================
# CHECK LEVEL UNLOCK
# =========================================================

def check_level_unlock(
    user_id,
    current_level
):

    # C1 LAST LEVEL
    if current_level == "C1":

        return None

    required = LEVEL_CONFIG[
        current_level
    ]["required"]

    result = db_execute(
        """
        SELECT
            COALESCE(
                SUM(best_score),
                0
            )

        FROM quiz_progress

        WHERE user_id = %s
        AND level = %s
        """,
        (
            user_id,
            current_level
        ),
        fetchone=True
    )

    total = result[0] if result else 0

    if total >= required:

        next_level = LEVEL_ORDER[
            LEVEL_ORDER.index(
                current_level
            ) + 1
        ]

        db_execute(
            """
            UPDATE users
            SET unlocked_level = %s
            WHERE user_id = %s
            """,
            (
                next_level,
                user_id
            )
        )

        return next_level

    return None
# =========================================================
# START QUIZ BLOCK
# =========================================================

async def start_quiz_block(
    message: Message,
    level: str,
    block: int,
    force_restart=False
):

    user_id = message.from_user.id

    # ACTIVE QUIZ CHECK
    if user_id in quiz_running:

        await message.answer(
            "⚠️ Sizda aktiv test mavjud."
        )

        return

    # =====================================================
    # RESTART WARNING
    # =====================================================

    if not force_restart:

        old_result = db_execute(
            """
            SELECT best_score

            FROM quiz_progress

            WHERE
                user_id = %s
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

        if old_result:

            best_score = old_result[0]

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔄 Qayta ishlash",
                            callback_data=(
                                f"restartquiz:{level}:{block}"
                            )
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="❌ Bekor qilish",
                            callback_data="cancelquiz"
                        )
                    ]
                ]
            )

            await message.answer(
                f"⚠️ Siz bu blokni avval ishlagansiz.\n\n"
                f"🏆 Eng yaxshi natija: {best_score}/100\n\n"
                f"🔄 Test 0 dan boshlanadi.\n"
                f"⭐ XP faqat yangi rekord uchun beriladi.\n\n"
                f"Davom etasizmi?",
                reply_markup=keyboard
            )

            return

    # =====================================================
    # USER LEVEL SECURITY
    # =====================================================

    user_data = db_execute(
        """
        SELECT unlocked_level
        FROM users
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    current_unlocked = (
        user_data[0]
        if user_data
        else "A1"
    )

    if LEVEL_ORDER.index(level) > LEVEL_ORDER.index(current_unlocked):

        await message.answer(
            "🔒 Bu daraja hali ochilmagan."
        )

        return

    # =====================================================
    # BLOCK SECURITY
    # =====================================================

    config = LEVEL_CONFIG[level]

    if block > config["blocks"]:

        await message.answer(
            "❌ Noto'g'ri blok."
        )

        return

    # =====================================================
    # PREVIOUS BLOCK CHECK
    # =====================================================

    if block > 1:

        prev_block = block - 1

        result = db_execute(
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
                prev_block
            ),
            fetchone=True
        )

        prev_score = (
            result[0]
            if result
            else 0
        )

        if prev_score < 60:

            await message.answer(
                f"🔒 Avval {prev_block}-Blokdan "
                f"kamida 60/100 ishlang."
            )

            return

    # =====================================================
    # LOAD QUESTIONS
    # =====================================================

    questions = QUIZ_DATA[level]

    start_index = (block - 1) * 100

    end_index = start_index + 100

    if level == "C1" and block == 11:

        end_index = 1055

    if start_index >= len(questions):

        await message.answer(
            "❌ CSV yetarli emas."
        )

        return

    block_questions = questions[
        start_index:end_index
    ]

    if not block_questions:

        await message.answer(
            "❌ Blok bo'sh."
        )

        return

    # =====================================================
    # START QUIZ
    # =====================================================

    random.shuffle(
        block_questions
    )

    quiz_running.add(
        user_id
    )

    quiz_sessions[user_id] = {

        "level": level,
        "block": block,
        "questions": block_questions,
        "index": 0,
        "score": 0
    }

    await message.answer(
        f"🚀 {level}-{block}-Blok boshlandi!\n\n"
        f"📚 Savollar: {len(block_questions)}"
    )

    await send_next_question(
        message.chat.id,
        user_id
    )
# =========================================================
# START BLOCK
# =========================================================

@dp.message(
    F.text.regexp(
        r"📚 (A1|A2|B1|B2|C1)-(\d+)-Blok"
    )
)
async def start_block(
    message: Message
):

    text = message.text.replace(
        "📚 ",
        ""
    )

    level = text.split("-")[0]

    block = int(
        text.split("-")[1]
    )

    await start_quiz_block(
        message,
        level,
        block
    )

# =========================================================
# SEND QUESTION
# =========================================================

async def send_next_question(
    chat_id,
    user_id
):

    # MEMORY SAFETY
    if user_id not in quiz_sessions:

        quiz_running.discard(
            user_id
        )

        return

    session = quiz_sessions.get(
        user_id
    )

    if not session:

        quiz_running.discard(
            user_id
        )

        return

    questions = session["questions"]

    index = session["index"]

    # QUIZ FINISH
    if index >= len(questions):

        await finish_quiz(
            chat_id,
            user_id
        )

        return

    question = questions[index]

    answers = [

        question["correct"],

        question["wrong1"],

        question["wrong2"]
    ]

    random.shuffle(answers)

    qid = (
        f"{user_id}_"
        f"{question['id']}"
    )

    answered_users[qid] = set()

    callback_map = {}

    callback_buttons = []

    for i, answer in enumerate(
        answers
    ):

        answer_key = f"a{i}"

        callback_map[
            answer_key
        ] = answer

        callback_buttons.append([

            InlineKeyboardButton(

                text=answer,

                callback_data=(
                    f"quiz:"
                    f"{qid}:"
                    f"{answer_key}"
                )
            )
        ])

    callback_buttons.append([

        InlineKeyboardButton(

            text="⛔ Yakunlash",

            callback_data=(
                f"stopquiz:{user_id}"
            )
        )
    ])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=callback_buttons
    )

    active_questions[qid] = {

        "correct": question["correct"],

        "answers": callback_map
    }

    await bot.send_message(

        chat_id,

        f"📚 "
        f"{session['level']}"
        f"-{session['block']}\n"

        f"📊 "
        f"{index+1}/"
        f"{len(questions)}\n\n"

        f"🇩🇪 "
        f"{question['german']}",

        reply_markup=keyboard
    )

# =========================================================
# ANSWER
# =========================================================

@dp.callback_query(
    F.data.startswith("quiz:")
)
async def quiz_answer(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    try:

        _, qid, answer_key = (
            callback.data.split(
                ":",
                2
            )
        )

    except:

        await callback.answer(
            "❌ Callback xatosi.",
            show_alert=True
        )

        return

    # OWNER SECURITY
    owner_id = int(
        qid.split("_")[0]
    )

    if owner_id != user_id:

        await callback.answer(
            "❌ Bu sizning testingiz emas.",
            show_alert=True
        )

        return

    # QUESTION EXISTS
    if qid not in active_questions:

        await callback.answer(
            "❌ Savol tugagan.",
            show_alert=True
        )

        return

    # DOUBLE ANSWER BLOCK
    if user_id in answered_users[qid]:

        await callback.answer(
            "❌ Javob berilgansiz.",
            show_alert=True
        )

        return

    answered_users[qid].add(
        user_id
    )

    question_data = active_questions[qid]

    answers_map = question_data["answers"]

    selected = answers_map.get(
        answer_key
    )

    correct = question_data["correct"]

    session = quiz_sessions.get(
        user_id
    )

    if not session:

        quiz_running.discard(
            user_id
        )

        return

    # CORRECT
    if selected == correct:

        session["score"] += 1

        await callback.answer(
            "✅ To'g'ri!"
        )

    # WRONG
    else:

        await callback.answer(
            f"❌ Noto'g'ri!\n\n"
            f"✅ {correct}",
            show_alert=True
        )

    session["index"] += 1

    active_questions.pop(
        qid,
        None
    )

    answered_users.pop(
        qid,
        None
    )

    try:

        await callback.message.edit_reply_markup(
            reply_markup=None
        )

    except:
        pass

    await send_next_question(
        callback.message.chat.id,
        user_id
    )

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

        quiz_running.discard(
            user_id
        )

        return

    score = session["score"]

    level = session["level"]

    block = session["block"]

    total = len(
        session["questions"]
    )

    # =====================================================
    # OLD SCORE
    # =====================================================

    old_result = db_execute(
        """
        SELECT best_score

        FROM quiz_progress

        WHERE
            user_id = %s
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

    # =====================================================
    # XP GAIN
    # =====================================================

    xp_gain = max(
        0,
        score - old_score
    )

    # =====================================================
    # SAVE BEST SCORE
    # =====================================================

    db_execute(
        """
        INSERT INTO quiz_progress
        (
            user_id,
            level,
            block_number,
            best_score
        )

        VALUES (%s,%s,%s,%s)

        ON CONFLICT
        (
            user_id,
            level,
            block_number
        )

        DO UPDATE SET

            best_score = GREATEST(
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

    # =====================================================
    # UPDATE XP
    # =====================================================

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

    # =====================================================
    # LEVEL UNLOCK
    # =====================================================

    new_level = check_level_unlock(
        user_id,
        level
    )

    unlock_text = ""

    if new_level:

        unlock_text = (
            f"\n\n🔓 Yangi daraja ochildi: "
            f"{new_level}"
        )

    # =====================================================
    # RESULT MESSAGE
    # =====================================================

    result_text = (

        f"🏁 Test tugadi!\n\n"

        f"🏆 Natija: "
        f"{score}/{total}"
    )

    if xp_gain > 0:

        result_text += (
            f"\n⭐ XP qo'shildi: "
            f"+{xp_gain}"
        )

    else:

        result_text += (
            "\n♻️ Bu blokdan avvalroq "
            "yuqoriroq natija olgansiz."
        )

    result_text += unlock_text

    await bot.send_message(
        chat_id,
        result_text
    )

    # =====================================================
    # CLEAN SESSION
    # =====================================================

    quiz_running.discard(
        user_id
    )

    quiz_sessions.pop(
        user_id,
        None
    )

    # =====================================================
    # MEMORY CLEAN
    # =====================================================

    remove_keys = [

        key

        for key in active_questions

        if key.startswith(
            f"{user_id}_"
        )
    ]

    for key in remove_keys:

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

@dp.callback_query(
    F.data.startswith(
        "restartquiz:"
    )
)
async def restart_quiz_handler(
    callback: CallbackQuery
):

    try:

        parts = callback.data.split(
            ":"
        )

        if len(parts) != 3:

            await callback.answer(
                "❌ Noto'g'ri callback.",
                show_alert=True
            )

            return

        level = parts[1]

        block = int(
            parts[2]
        )

        try:

            await callback.message.delete()

        except Exception:

            pass

        await start_quiz_block(
            callback.message,
            level,
            block,
            force_restart=True
        )

        await callback.answer()

    except Exception as e:

        logger.error(
            f"Restart quiz error: {e}"
        )

        await callback.answer(
            "❌ Xatolik yuz berdi.",
            show_alert=True
        )


# =========================================================
# CANCEL RESTART
# =========================================================

@dp.callback_query(
    F.data == "cancelquiz"
)
async def cancel_quiz_handler(
    callback: CallbackQuery
):

    try:

        await callback.message.edit_text(
            "❌ Qayta ishlash bekor qilindi."
        )

    except Exception:

        pass

    await callback.answer()

# =========================================================
# STOP QUIZ
# =========================================================

@dp.callback_query(
    F.data.startswith(
        "stopquiz:"
    )
)
async def stop_quiz(
    callback: CallbackQuery
):

    user_id = int(
        callback.data.split(":")[1]
    )

    # OWNER SECURITY
    if callback.from_user.id != user_id:

        await callback.answer(
            "❌ Bu sizning testingiz emas.",
            show_alert=True
        )

        return

    # BUTTON CLEAN
    try:

        await callback.message.edit_reply_markup(
            reply_markup=None
        )

    except:
        pass

    await finish_quiz(
        callback.message.chat.id,
        user_id
    )

# =========================================================
# RATING MENU
# =========================================================

rating_menu = ReplyKeyboardMarkup(
    keyboard=[

        [
            KeyboardButton(
                text="🏆 Umumiy Reyting"
            ),

            KeyboardButton(
                text="⚡ Kunlik Reyting"
            )
        ],

        [
            KeyboardButton(
                text="⬅️ Orqaga"
            )
        ]
    ],
    resize_keyboard=True
)

# =========================================================
# OPEN RATING MENU
# =========================================================

@dp.message(F.text == "🏆 Reytinglar")
async def open_rating_menu(
    message: Message
):

    await message.answer(
        "🏆 Reyting bo'limi",
        reply_markup=rating_menu
    )

# =========================================================
# TOTAL RANKING
# =========================================================

@dp.message(F.text == "🏆 Umumiy Reyting")
async def total_ranking(
    message: Message
):

    rankings = db_execute(
        """
        SELECT
            COALESCE(full_name,'Unknown'),
            total_score

        FROM users

        WHERE
            total_score IS NOT NULL
            AND total_score > 0

        ORDER BY total_score DESC

        LIMIT 100
        """,
        fetchall=True
    )

    # EMPTY
    if not rankings:

        await message.answer(
            "📭 Reyting hali bo'sh.\n\n"
            "🎮 Birinchi bo'lib test ishlang!"
        )

        return

    text = (
        "🏆 UMUMIY REYTING\n\n"
    )

    medals = {

        1: "🥇",
        2: "🥈",
        3: "🥉"
    }

    for i, (
        full_name,
        score
    ) in enumerate(rankings, 1):

        medal = medals.get(
            i,
            f"{i}."
        )

        text += (
            f"{medal} "
            f"{full_name} — "
            f"{score} XP\n"
        )

    # =====================================================
    # MY SCORE
    # =====================================================

    my = db_execute(
        """
        SELECT total_score
        FROM users
        WHERE user_id = %s
        """,
        (message.from_user.id,),
        fetchone=True
    )

    my_score = my[0] if my else 0

    if my_score <= 0:

        text += (
            "\n━━━━━━━━━━\n"
            "🎮 Siz hali test ishlamagansiz."
        )

    await message.answer(text)
# =========================================================
# DAILY RANKING
# =========================================================

@dp.message(F.text == "⚡ Kunlik Reyting")
async def daily_ranking(
    message: Message
):

    rankings = db_execute(
        """
        SELECT
            COALESCE(full_name,'Unknown'),
            daily_score

        FROM users

        WHERE
            daily_score IS NOT NULL
            AND daily_score > 0

        ORDER BY daily_score DESC

        LIMIT 100
        """,
        fetchall=True
    )

    # EMPTY
    if not rankings:

        await message.answer(
            "📭 Bugungi reyting hali bo'sh.\n\n"
            "🎮 Birinchi bo'lib test ishlang!"
        )

        return

    text = (
        "⚡ KUNLIK REYTING\n\n"
    )

    medals = {

        1: "🥇",
        2: "🥈",
        3: "🥉"
    }

    for i, (
        full_name,
        score
    ) in enumerate(rankings, 1):

        medal = medals.get(
            i,
            f"{i}."
        )

        text += (
            f"{medal} "
            f"{full_name} — "
            f"{score} XP\n"
        )

    # =====================================================
    # MY SCORE
    # =====================================================

    my = db_execute(
        """
        SELECT daily_score
        FROM users
        WHERE user_id = %s
        """,
        (message.from_user.id,),
        fetchone=True
    )

    my_score = my[0] if my else 0

    if my_score <= 0:

        text += (
            "\n━━━━━━━━━━\n"
            "🎮 Siz hali bugun test ishlamagansiz."
        )

    await message.answer(text)

# =========================================================
# SYSTEM STABILITY
# =========================================================

import shutil

# =========================================================
# INIT STORAGE
# =========================================================

def init_storage():

    folders = [

        "generated",

        "certificates",

        "fonts"
    ]

    for folder in folders:

        try:

            os.makedirs(
                folder,
                exist_ok=True
            )

        except Exception as e:

            logger.error(
                f"Folder create error "
                f"{folder}: {e}"
            )

# =========================================================
# CHECK EXISTING CERTIFICATE
# =========================================================

def get_existing_certificate(
    user_id
):

    return db_execute(
        """
        SELECT
            certificate_id,
            rank,
            percent,
            score

        FROM certificates

        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

# =========================================================
# SAVE CERTIFICATE
# =========================================================

def save_certificate(
    user_id,
    cert_id,
    rank,
    percent,
    score
):

    db_execute(
        """
        INSERT INTO certificates
        (
            user_id,
            certificate_id,
            rank,
            percent,
            score
        )

        VALUES (%s,%s,%s,%s,%s)

        ON CONFLICT
        (certificate_id)

        DO NOTHING
        """,
        (
            user_id,
            cert_id,
            rank,
            percent,
            score
        )
    )

# =========================================================
# AUTO MEMORY CLEANUP
# =========================================================

async def cleanup_quiz_memory():

    while True:

        try:

            # ACTIVE QUESTIONS CLEAN
            if len(active_questions) > 3000:

                active_questions.clear()

                logger.warning(
                    "Active questions cleared"
                )

            # ANSWER CACHE CLEAN
            if len(answered_users) > 3000:

                answered_users.clear()

                logger.warning(
                    "Answered users cleared"
                )

            # DEAD SESSIONS
            dead = []

            for user_id in quiz_sessions:

                if user_id not in quiz_running:

                    dead.append(user_id)

            for user_id in dead:

                quiz_sessions.pop(
                    user_id,
                    None
                )

            # GENERATED CLEAN
            try:

                for file in os.listdir(
                    GENERATED_DIR
                ):

                    path = os.path.join(
                        GENERATED_DIR,
                        file
                    )

                    # DELETE PNG
                    if (
                        file.endswith(".png")
                        and
                        os.path.isfile(path)
                    ):

                        os.remove(path)

            except Exception as e:

                logger.error(
                    f"Generated cleanup: {e}"
                )

            logger.info(
                "Memory cleanup complete ✅"
            )

        except Exception as e:

            logger.error(
                f"Cleanup task error: {e}"
            )

        # EVERY 1 HOUR
        await asyncio.sleep(3600)
# =========================================================
# DAILY RESET SCHEDULER
# =========================================================

async def daily_reset_scheduler():

    while True:

        try:

            now = datetime.now()

            tomorrow = (
                now + timedelta(days=1)
            ).replace(
                hour=0,
                minute=0,
                second=5,
                microsecond=0
            )

            wait_seconds = (
                tomorrow - now
            ).total_seconds()

            await asyncio.sleep(
                wait_seconds
            )

            reset_daily_scores()

            logger.info(
                "Daily scores reset ✅"
            )

        except Exception as e:

            logger.error(
                f"Daily reset error: {e}"
            )

            await asyncio.sleep(60)

# =========================================================
# CERTIFICATE SYSTEM
# =========================================================

TOTAL_WORDS = 5555

CERTIFICATE_DIR = "certificates"

GENERATED_DIR = "generated"

# =========================================================
# CERTIFICATE TABLE
# =========================================================

def init_certificate_table():

    db_execute(
        """
        CREATE TABLE IF NOT EXISTS certificates (

            id SERIAL PRIMARY KEY,

            user_id BIGINT,

            rank TEXT,

            certificate_id TEXT UNIQUE,

            percent REAL,

            score INTEGER,

            created_at TIMESTAMP
            DEFAULT NOW(),

            UNIQUE(user_id, rank)
        )
        """
    )

# =========================================================
# GENERATE CERTIFICATE ID
# =========================================================

def generate_certificate_id():

    return (
        f"VIZU-"
        f"{random.randint(100000,999999)}"
    )

# =========================================================
# CHECK EXISTING CERTIFICATE
# =========================================================

def get_existing_certificate(
    user_id,
    rank
):

    return db_execute(
        """
        SELECT
            certificate_id

        FROM certificates

        WHERE
            user_id = %s
            AND rank = %s
        """,
        (
            user_id,
            rank
        ),
        fetchone=True
    )

# =========================================================
# SAVE CERTIFICATE
# =========================================================

def save_certificate(

    user_id,

    cert_id,

    rank,

    percent,

    score
):

    db_execute(
        """
        INSERT INTO certificates
        (
            user_id,
            rank,
            certificate_id,
            percent,
            score
        )

        VALUES (%s,%s,%s,%s,%s)

        ON CONFLICT
        (user_id, rank)

        DO NOTHING
        """,
        (
            user_id,
            rank,
            cert_id,
            percent,
            score
        )
    )

# =========================================================
# GENERATE QR
# =========================================================

def generate_qr(
    data,
    path
):

    qr = qrcode.make(data)

    qr.save(path)

# =========================================================
# DRAW CENTER TEXT
# =========================================================

def draw_center_text(

    draw,

    text,

    font,

    y,

    image_width,

    fill
):

    bbox = draw.textbbox(
        (0,0),
        text,
        font=font
    )

    text_width = (
        bbox[2] - bbox[0]
    )

    x = (
        image_width - text_width
    ) // 2

    draw.text(

        (x, y),

        text,

        font=font,

        fill=fill
    )

# =========================================================
# CREATE CERTIFICATE
# =========================================================

async def create_certificate(

    user_id,

    full_name,

    percent,

    score,

    rank,

    cert_id
):

    # =====================================================
    # STORAGE
    # =====================================================

    os.makedirs(
        GENERATED_DIR,
        exist_ok=True
    )

    # =====================================================
    # TEMPLATE
    # =====================================================

    if rank == "GOLD":

        template = (
            f"{CERTIFICATE_DIR}/"
            "gold_template.png"
        )

        text_color = (
            255,
            215,
            0
        )

    elif rank == "SILVER":

        template = (
            f"{CERTIFICATE_DIR}/"
            "silver_template.png"
        )

        text_color = (
            40,
            40,
            40
        )

    else:

        template = (
            f"{CERTIFICATE_DIR}/"
            "bronze_template.png"
        )

        text_color = (
            90,
            40,
            20
        )

    # =====================================================
    # TEMPLATE CHECK
    # =====================================================

    if not os.path.exists(
        template
    ):

        raise FileNotFoundError(
            f"Template topilmadi: "
            f"{template}"
        )

    # =====================================================
    # LOAD IMAGE
    # =====================================================

    image = Image.open(
        template
    ).convert("RGBA")

    draw = ImageDraw.Draw(image)

    width, height = image.size

    # =====================================================
    # FONTS
    # =====================================================

    name_font = ImageFont.truetype(
        "fonts/GreatVibes-Regular.ttf",
        90
    )

    title_font = ImageFont.truetype(
        "fonts/Montserrat-Bold.ttf",
        42
    )

    small_font = ImageFont.truetype(
        "fonts/Montserrat-Regular.ttf",
        28
    )

    # =====================================================
    # DATE
    # =====================================================

    date = datetime.now().strftime(
        "%d.%m.%Y"
    )

    # =====================================================
    # NAME
    # =====================================================

    draw_center_text(

        draw,

        full_name,

        name_font,

        470,

        width,

        text_color
    )

    # =====================================================
    # PERCENT
    # =====================================================

    draw.text(

        (1320, 355),

        f"{percent}%",

        font=title_font,

        fill=text_color
    )

    # =====================================================
    # SCORE
    # =====================================================

    draw.text(

        (1320, 505),

        f"{score}/5555",

        font=title_font,

        fill=text_color
    )

    # =====================================================
    # CERTIFICATE ID
    # =====================================================

    draw.text(

        (1320, 655),

        cert_id,

        font=small_font,

        fill=text_color
    )

    # =====================================================
    # DATE
    # =====================================================

    draw.text(

        (1320, 805),

        date,

        font=small_font,

        fill=text_color
    )

    # =====================================================
    # QR
    # =====================================================

    qr_path = (
        f"{GENERATED_DIR}/"
        f"qr_{user_id}.png"
    )

    generate_qr(
        cert_id,
        qr_path
    )

    qr = Image.open(
        qr_path
    ).resize((180,180))

    image.paste(
        qr,
        (1450, 850)
    )

    # =====================================================
    # SAVE
    # =====================================================

    output_path = (
        f"{GENERATED_DIR}/"
        f"{cert_id}.png"
    )

    image.save(output_path)

    return output_path

# =========================================================
# CERTIFICATE COMMAND
# =========================================================

@dp.message(F.text == "🏅 Sertifikat")
async def certificate_system(
    message: Message
):

    user_id = message.from_user.id

    # =====================================================
    # CHECK LAST BLOCK
    # =====================================================

    result = db_execute(
        """
        SELECT best_score

        FROM quiz_progress

        WHERE
            user_id = %s
            AND level = 'C1'
            AND block_number = 11
        """,
        (user_id,),
        fetchone=True
    )

    if not result:

        await message.answer(

            "🔒 Sertifikat hali yopiq.\n\n"

            "🎯 C1 oxirgi blokni tugating."
        )

        return

    # =====================================================
    # USER
    # =====================================================

    user_data = db_execute(
        """
        SELECT
            full_name

        FROM users

        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    full_name = (
        user_data[0]
        if user_data
        else message.from_user.full_name
    )

    # =====================================================
    # TOTAL SCORE
    # =====================================================

    total = db_execute(
        """
        SELECT
            COALESCE(
                SUM(best_score),
                0
            )

        FROM quiz_progress

        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    total_score = (
        total[0]
        if total
        else 0
    )

    # =====================================================
    # PERCENT
    # =====================================================

    percent = round(

        (
            total_score
            /
            TOTAL_WORDS
        ) * 100,

        1
    )

    # =====================================================
    # RANK
    # =====================================================

    if percent >= 85:

        rank = "GOLD"

    elif percent >= 70:

        rank = "SILVER"

    elif percent >= 60:

        rank = "BRONZE"

    else:

        await message.answer(

            "❌ Minimum 60% kerak.\n\n"

            f"📊 Natija: "
            f"{percent}%"
        )

        return

    # =====================================================
    # EXISTING
    # =====================================================

    existing = get_existing_certificate(
        user_id,
        rank
    )

    if existing:

        await message.answer(

            f"🏅 Siz allaqachon "
            f"{rank} sertifikatini "
            f"olgansiz."
        )

        return

    # =====================================================
    # CERT ID
    # =====================================================

    cert_id = (
        generate_certificate_id()
    )

    # =====================================================
    # SAVE DATABASE
    # =====================================================

    save_certificate(

        user_id,

        cert_id,

        rank,

        percent,

        total_score
    )

    # =====================================================
    # GENERATE
    # =====================================================

    try:

        path = await create_certificate(

            user_id,

            full_name,

            percent,

            total_score,

            rank,

            cert_id
        )

    except Exception as e:

        logger.error(
            f"Certificate create error: {e}"
        )

        await message.answer(
            "❌ Sertifikat yaratishda xato."
        )

        return

    # =====================================================
    # ADMIN CHANNEL
    # =====================================================

    await send_admin_photo_log(

        path,

        f"🏅 Yangi Sertifikat\n\n"

        f"👤 {full_name}\n\n"

        f"🏆 {rank}\n"

        f"📊 {percent}%\n"

        f"📚 {total_score}/5555\n\n"

        f"🎫 {cert_id}\n"

        f"🆔 {user_id}\n\n"

        f"📅 "
        f"{datetime.now().strftime('%d.%m.%Y')}"
    )

    # =====================================================
    # SEND USER
    # =====================================================

    await message.answer_photo(

        FSInputFile(path),

        caption=(

            f"🏅 {rank} Zertifikat\n\n"

            f"📊 Natija: "
            f"{percent}%\n"

            f"📚 {total_score}/5555\n\n"

            f"🎫 {cert_id}"
        )
    )

# =========================
# ADMIN PANEL
# =========================
@dp.message(Command("admin"))
async def admin_panel(message: Message):

    if not is_admin(message):
        return

    await message.answer(
        "⚙️ Admin Panel",
        reply_markup=admin_menu
    )
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

# =========================================================
# ADMIN STATES
# =========================================================

from aiogram.fsm.context import FSMContext

from aiogram.fsm.state import (
    State,
    StatesGroup
)


class AdminStates(StatesGroup):

    broadcast = State()

# =========================================================
# BROADCAST
# =========================================================

@dp.message(F.text == "📢 Reklama Yuborish")
async def broadcast_start(
    message: Message,
    state: FSMContext
):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "📨 Reklama matnini yuboring:"
    )

    await state.set_state(
        AdminStates.broadcast
    )


@dp.message(
    AdminStates.broadcast
)
async def send_broadcast(
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

    success = 0

    failed = 0

    progress = await message.answer(
        "📢 Reklama yuborilmoqda..."
    )

    for i, (user_id,) in enumerate(
        users,
        1
    ):

        try:

            await bot.copy_message(

                chat_id=user_id,

                from_chat_id=message.chat.id,

                message_id=message.message_id
            )

            success += 1

        except Exception as e:

            failed += 1

            logger.error(
                f"Broadcast error "
                f"{user_id}: {e}"
            )

        # =================================================
        # FLOOD CONTROL
        # =================================================

        await asyncio.sleep(0.12)

        # =================================================
        # LIVE PROGRESS
        # =================================================

        if i % 25 == 0:

            try:

                await progress.edit_text(

                    f"📢 Reklama yuborilmoqda...\n\n"

                    f"✅ Yuborildi: {success}\n"

                    f"❌ Xato: {failed}\n"

                    f"📊 Jarayon: "
                    f"{i}/{len(users)}"
                )

            except:
                pass

    # =====================================================
    # FINAL RESULT
    # =====================================================

    await progress.edit_text(

        f"✅ Reklama yakunlandi.\n\n"

        f"📨 Yuborildi: {success}\n"

        f"❌ Xato: {failed}\n"

        f"👥 Jami: {len(users)}"
    )

    await state.clear()

# =========================
# RUN
# =========================

async def start_bot():

    while True:

        try:

            logger.info(
                "BOT ISHGA TUSHDI ✅"
            )

            await dp.start_polling(
                bot
            )

        except Exception as e:

            logger.error(
                f"BOT CRASH: {e}"
            )

            # reconnect delay
            await asyncio.sleep(10)


async def main():

    # =====================================================
    # DATABASE
    # =====================================================

    init_db_pool()

    init_tables()

    logger.info(
        "DATABASE READY ✅"
    )

    # =====================================================
    # LOAD SYSTEMS
    # =====================================================

    load_artikel()
    load_all_quizzes()


    reset_daily_scores()

    logger.info(
        "SYSTEMS LOADED ✅"
    )

    # =====================================================
    # DELETE OLD WEBHOOK
    # =====================================================

    try:

        await bot.delete_webhook(
            drop_pending_updates=True
        )

        logger.info(
            "WEBHOOK TOZALANDI ✅"
        )

    except Exception as e:

        logger.error(
            f"Webhook error: {e}"
        )

    # =====================================================
    # KEEP ALIVE
    # =====================================================

    try:

        Thread(
            target=run_web,
            daemon=True
        ).start()

        logger.info(
            "KEEP ALIVE STARTED ✅"
        )

    except Exception as e:

        logger.error(
            f"Flask error: {e}"
        )

    # =====================================================
    # START BOT
    # =====================================================

    await start_bot()


if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        logger.info(
            "BOT STOPPED ⛔"
        )

    except Exception as e:

        logger.error(
            f"MAIN ERROR: {e}"
        )