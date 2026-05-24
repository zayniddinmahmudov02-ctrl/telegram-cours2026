from flask import Flask
from threading import Thread
from dotenv import load_dotenv
import os
import asyncio
import csv
import random
import logging

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
)
from aiogram.filters import CommandStart, Command
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
if not TOKEN:
    raise ValueError("TOKEN topilmadi")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL topilmadi")
# =========================
# CONFIG
# =========================

ADMIN_ID = int(os.getenv("ADMIN_ID"))
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

db_pool = None

def init_db_pool():

    global db_pool

    try:

        db_pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=DATABASE_URL
        )

        logger.info("Database pool connected ✅")

    except Exception as e:

        logger.error(
            f"Database connection error: {e}"
        )

        raise


@contextmanager
def get_db():

    global db_pool

    conn = None

    try:

        try:

            conn = db_pool.getconn()

        except Exception as e:

            logger.error(
                f"DB reconnect: {e}"
            )

            init_db_pool()

            conn = db_pool.getconn()

        yield conn

        conn.commit()

    except Exception as e:

        if conn:
            conn.rollback()

        logger.error(
            f"Database query error: {e}"
        )

        raise

    finally:

        if conn:

            try:
                db_pool.putconn(conn)

            except Exception as e:
                logger.error(e)


def db_execute(
    query,
    params=(),
    fetchone=False,
    fetchall=False
):

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

        logger.error(
            f"DB execute error: {e}"
        )

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

    # indexes
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

    logger.info("Database tables ready ✅")
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

        member = await bot.get_chat_member(
            CHANNEL_USERNAME,
            user_id
        )

        return member.status not in ("left", "kicked")

    except Exception as e:

        logger.error(f"Subscription check error: {e}")

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

    if not await check_subscription(user_id):

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📢 Kanalga A'zo Bo'lish",
                        url="https://t.me/vizu_deutsch"
                    )
                ]
            ]
        )

        await message.answer(
            "❌ Botdan foydalanish uchun kanalga a'zo bo'ling.",
            reply_markup=keyboard
        )

        return

    db_execute(
        "INSERT INTO users (user_id, approved) "
        "VALUES (%s, 0) "
        "ON CONFLICT DO NOTHING",
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

        except Exception as e:

            logger.error(e)

    await message.answer(
        "🇩🇪 Nemis Tili Video Darslari Botiga "
        "Xush Kelibsiz!\n\n"
        "🎉 Hozirda barcha kurslar "
        "50% CHEGIRMADA!",
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

    user_id = int(callback.data.split(":")[1])

    db_execute(
        "UPDATE users SET approved = 1 WHERE user_id = %s",
        (user_id,)
    )

    row = db_execute(
        "SELECT course, full_name FROM users WHERE user_id = %s",
        (user_id,),
        fetchone=True
    )

    if not row:
        await callback.answer("❌ User topilmadi")
        return

    course = row[0]
    full_name = row[1] or "Student"

    course_link = COURSE_LINKS.get(
        course,
        "https://t.me/vizu_deutsch"
    )

    group_link = GROUP_LINKS.get(
        course,
        "https://t.me/vizu_deutsch"
    )

    await bot.send_message(
        user_id,
        f"🎉 Assalomu alaykum, {full_name}!\n\n"
        f"✅ To'lovingiz muvaffaqiyatli tasdiqlandi.\n\n"
        f"📚 Kurs: {course}\n\n"
        f"🎥 Kurs kanali:\n{course_link}\n\n"
        f"💬 Savollar guruhi:\n{group_link}\n\n"
        f"🚀 Yaxshi o'qish tilaymiz!"
    )

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as e:
        logger.error(e)

    await callback.message.answer(
        f"✅ User tasdiqlandi\n\n"
        f"👤 {full_name}\n"
        f"📚 {course}"
    )

    await callback.answer("✅ Tasdiqlandi")


@dp.callback_query(F.data.startswith("reject:"))
async def reject_user(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "❌ Ruxsat yo'q",
            show_alert=True
        )
        return

    user_id = int(callback.data.split(":")[1])

    row = db_execute(
        "SELECT full_name FROM users WHERE user_id = %s",
        (user_id,),
        fetchone=True
    )

    full_name = row[0] if row else "User"

    await bot.send_message(
        user_id,
        "❌ Chekingiz tasdiqlanmadi.\n\n"
        "Iltimos:\n"
        "• chekni aniqroq yuboring\n"
        "• yoki admin bilan bog'laning."
    )

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as e:
        logger.error(e)

    await callback.message.answer(
        f"❌ User rad qilindi\n\n"
        f"👤 {full_name}"
    )

    await callback.answer("❌ Rad qilindi")
# =========================
# WORD GAME MENU
# =========================
@dp.message(F.text == "🎮 So'z O'yini")
async def word_game(message: Message):
 artikel_users.pop(message.from_user.id, None) 
 await message.answer("🎮 Wortspiel — So'z O'yini", reply_markup=word_game_menu)
# =========================
# QUIZ DATA
# =========================

QUIZ_QUESTIONS = []

def load_quiz_questions():

    global QUIZ_QUESTIONS

    csv_path = "quiz.csv"

    if not os.path.exists(csv_path):

        logger.warning("quiz.csv topilmadi")

        return

    with open(csv_path, "r", encoding="utf-8") as f:

        reader = csv.DictReader(f)

        for row in reader:

            try:

                QUIZ_QUESTIONS.append({
                    "id": int(row["id"]),
                    "german": row["german"].strip(),
                    "correct": row["correct"].strip(),
                    "wrong": row["wrong"].strip(),
                })

            except Exception as e:
                logger.error(e)

    logger.info(f"Quiz loaded: {len(QUIZ_QUESTIONS)}")

# =========================
# QUIZ SYSTEM
# =========================

quiz_running = set()

quiz_sessions = {}

active_questions = {}

answered_users = {}

# =========================
# START QUIZ
# =========================

@dp.message(F.text == "📚 A-Blok Teste")
async def start_quiz(message: Message):

    user_id = message.from_user.id

    if user_id in quiz_running:

        await message.answer(
            "⚠️ Test allaqachon boshlangan."
        )

        return

    if not QUIZ_QUESTIONS:

        await message.answer(
            "❌ Quiz savollari topilmadi."
        )

        return

    quiz_running.add(user_id)

    db_execute(
        "UPDATE users SET score = 0 WHERE user_id = %s",
        (user_id,)
    )

    questions = random.sample(
        QUIZ_QUESTIONS,
        len(QUIZ_QUESTIONS)
    )

    quiz_sessions[user_id] = {
        "questions": questions,
        "index": 0
    }

    await message.answer(
        f"🚀 Test boshlandi!\n\n"
        f"📚 Savollar soni: {len(questions)}"
    )

    await send_next_question(
        message.chat.id,
        user_id
    )

# =========================
# SEND QUESTION
# =========================

async def send_next_question(chat_id, user_id):

    session = quiz_sessions.get(user_id)

    if not session:
        return

    questions = session["questions"]

    index = session["index"]

    # TEST TUGADI
    if index >= len(questions):

        row = db_execute(
            "SELECT score FROM users WHERE user_id = %s",
            (user_id,),
            fetchone=True
        )

        score = row[0] if row else 0

        await bot.send_message(
            chat_id,
            f"🏁 Test tugadi!\n\n"
            f"🏆 Natijangiz: {score}"
        )

        quiz_running.discard(user_id)

        quiz_sessions.pop(user_id, None)

        return

    question = questions[index]

    answers = [
        question["correct"],
        question["wrong"]
    ]

    random.shuffle(answers)

    question_id = f"{user_id}_{question['id']}"

    active_questions[question_id] = question["correct"]

    answered_users[question_id] = set()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"A) {answers[0]}",
                    callback_data=(
                        f"quiz:{question_id}:{answers[0]}"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"B) {answers[1]}",
                    callback_data=(
                        f"quiz:{question_id}:{answers[1]}"
                    )
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

    await bot.send_message(
        chat_id,
        f"📚 Savol ID: {question['id']}\n"
        f"📊 {index + 1}/{len(questions)}\n\n"
        f"🇩🇪 {question['german']}",
        reply_markup=keyboard
    )

# =========================
# QUIZ ANSWER
# =========================

@dp.callback_query(F.data.startswith("quiz:"))
async def quiz_answer(callback: CallbackQuery):

    user_id = callback.from_user.id

    _, question_id, selected = (
        callback.data.split(":", 2)
    )

    if question_id not in active_questions:

        await callback.answer(
            "❌ Savol tugagan.",
            show_alert=True
        )

        return

    if user_id in answered_users[question_id]:

        await callback.answer(
            "❌ Siz javob berib bo'ldingiz!",
            show_alert=True
        )

        return

    answered_users[question_id].add(user_id)

    correct = active_questions[question_id]

    if selected == correct:

        db_execute(
            "UPDATE users "
            "SET score = score + 1 "
            "WHERE user_id = %s",
            (user_id,)
        )

        await callback.answer(
            "✅ To'g'ri!"
        )

    else:

        await callback.answer(
            f"❌ Noto'g'ri!\n\n"
            f"✅ To'g'ri javob: {correct}",
            show_alert=True
        )

    active_questions.pop(question_id, None)

    answered_users.pop(question_id, None)

    session = quiz_sessions.get(user_id)

    if session:
        session["index"] += 1

    try:

        await callback.message.edit_reply_markup(
            reply_markup=None
        )

    except Exception as e:
        logger.error(e)

    await send_next_question(
        callback.message.chat.id,
        user_id
    )

# =========================
# STOP QUIZ
# =========================

@dp.callback_query(F.data.startswith("stopquiz:"))
async def stop_quiz(callback: CallbackQuery):

    user_id = int(
        callback.data.split(":")[1]
    )

    if callback.from_user.id != user_id:

        await callback.answer(
            "❌ Ruxsat yo'q",
            show_alert=True
        )

        return

    row = db_execute(
        "SELECT score FROM users WHERE user_id = %s",
        (user_id,),
        fetchone=True
    )

    score = row[0] if row else 0

    quiz_running.discard(user_id)

    quiz_sessions.pop(user_id, None)

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await callback.message.answer(
        f"⛔ Test yakunlandi!\n\n"
        f"🏆 Natijangiz: {score}"
    )

    await callback.answer()
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
# =========================
# BROADCAST
# =========================

@dp.message(F.text == "📢 Reklama Yuborish")
async def broadcast_start(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return

    await message.answer(
        "📢 Yuboriladigan xabarni kiriting:"
    )

    await state.set_state(
        BroadcastState.waiting_for_message
    )


@dp.message(BroadcastState.waiting_for_message)
async def send_broadcast(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return
    result = db_execute(
        "SELECT user_id "
        "FROM users "
        "WHERE approved = 1",
        fetchall=True
    )
    if not result:

        await message.answer(
            "❌ Foydalanuvchilar topilmadi."
        )

        await state.clear()

        return

    success = 0
    failed = 0

    await message.answer(
        f"🚀 Broadcast boshlandi.\n\n"
        f"👥 Userlar soni: {len(result)}"
    )

    for index, (uid,) in enumerate(result, 1):

        try:

            await bot.send_message(
                uid,
                message.text
            )

            success += 1

            # Telegram flood protection
            await asyncio.sleep(0.08)

            # Har 30 userdan keyin pause
            if index % 30 == 0:
                await asyncio.sleep(2)

        except Exception as e:

            failed += 1

            logger.error(
                f"Broadcast error {uid}: {e}"
            )

    await message.answer(
        f"✅ Broadcast tugadi!\n\n"
        f"👥 Yuborildi: {success}\n"
        f"❌ Yuborilmadi: {failed}"
    )

    await state.clear()
# =========================
# ARTIKEL TOPISH
# =========================
_MENU_BUTTONS = {
    "🎮 So'z O'yini", "🎥 Video Kurslar", "👨‍🏫 Ustoz haqida",
    "🏆 Natijalar", "📞 Admin bilan bog'lanish", "⬅️ Orqaga",
    "🇩🇪 A1", "🇩🇪 A2", "🇩🇪 B1",
    "🔥 A1-B1", "🔥 A1-C1", "🎬 Namuna Dars",
    "/admin", "📊 Statistika", "👥 Foydalanuvchilar",
    "💳 Xaridorlar", "📢 Reklama Yuborish", "📨 Shaxsiy Xabar",
    "⬅️ Admin Chiqish", "📚 A-Blok Teste", "🏆 Top 100",
}

@dp.message(F.text == "📚 Artikel Topish")
async def artikel_start(message: Message):
   artikel_users[
    message.from_user.id
] = asyncio.get_event_loop().time()
   await message.answer("📚 Artikelini topmoqchi bo'lgan so'zni yozing.")

@dp.message(F.text)
async def artikel_handler(message: Message):

    user_id = message.from_user.id

    # eski userlarni tozalash
    now = asyncio.get_event_loop().time()

    expired = [
        uid
        for uid, ts in artikel_users.items()
        if now - ts > 600
    ]

    for uid in expired:
        artikel_users.pop(uid, None)

    # artikel mode emas
    if user_id not in artikel_users:
        return

    # menu button bosilgan
    if message.text in _MENU_BUTTONS:

        artikel_users.pop(user_id, None)

        return

    word = message.text.lower().strip()

    result = artikel.get(word)

    await message.answer(
        result if result else "❌ So'z topilmadi"
    )
# =========================
# RUN
# =========================
async def main():

    init_db_pool()

    init_tables()

    load_artikel()

    load_quiz_questions()

    Thread(
        target=run_web,
        daemon=True
    ).start()

    logger.info("BOT ISHGA TUSHDI ✅")

    await dp.start_polling(bot)


if __name__ == "__main__":

    asyncio.run(main())