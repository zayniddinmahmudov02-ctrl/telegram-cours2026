# =========================================================
# STANDARD LIBRARY
# =========================================================

import asyncio
import csv
import glob
import logging
import os
import random
import uuid

from datetime import date, datetime, timedelta

# =========================================================
# DATABASE & CONFIG
# =========================================================

from config import *
from database import *

# =========================================================
# KEYBOARDS
# =========================================================

from keyboards import *

# =========================================================
# RUNTIME
# =========================================================

from services.runtime import *

from handlers.profile import register_profile_handlers

# =========================================================
# STATES
# =========================================================

from states.admin import BroadcastState, PersonalMessageState
from states.certificate import VizuCertificateState
from states.profile import ProfileState
from states.register import RegisterState
from states.schreiben import SchreibenState
from states.sprechen import SprechenState

# =========================================================
# AIOGRAM
# =========================================================

from aiogram import Bot, Dispatcher, F

from aiogram.filters import (
    Command,
    CommandStart,
    StateFilter,
)

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

from aiogram.utils.keyboard import InlineKeyboardBuilder

# =========================================================
# LOGGING
# =========================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
# HELPER FUNCTIONS
# =========================================================

def is_admin(message: Message) -> bool:
    return bool(
        message.from_user and
        message.from_user.id == ADMIN_ID
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
# FILME LOAD
# =========================================================

import csv

FILME = []

try:

    with open(
        "Filme.csv",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            FILME.append({
                "level":
                    row["level"].strip(),

                "category":
                    row["category"].strip(),

                "title":
                    row["title"].strip(),

                "message_id":
                    int(
                        row["message_id"]
                    )
            })

    print(
        f"FILME LOADED: "
        f"{len(FILME)}"
    )

except Exception as e:

    print(
        f"FILME LOAD ERROR: {e}"
    )
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
# MAIN INITIALIZATION & RUN
# =========================================================

async def main():
    try:

        # DATABASE
        init_database()

        # LOADERS
        load_artikel()
        load_vizu_lesen()
        load_vizu_horen()
        load_all_quizzes()

        # SCORES
        reset_daily_scores()

        # DEBUG
        logger.info(
            f"HÖREN QUESTIONS COUNT: {len(vizu_horen_questions)}"
        )

        logger.info(
            f"LESEN QUESTIONS COUNT: {len(vizu_lesen_questions)}"
        )

        folder = "VIZU-A1"

        if os.path.exists(folder):
            files = os.listdir(folder)
            logger.info(
                f"VIZU-A1 FILES: {files}"
            )
        else:
            logger.error(
                "VIZU-A1 PAPKASI YO'Q!"
            )

        # TELEGRAM
        await bot.delete_webhook(
            drop_pending_updates=True
        )

        await asyncio.sleep(2)

        # WEB SERVER
        Thread(
            target=run_web,
            daemon=True
        ).start()

        logger.info(
            "BOT ISHGA TUSHDI ✅"
        )

        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )

    except Exception as e:

        logger.error(
            f"CRITICAL MAIN ERROR: {e}"
        )


if __name__ == "__main__":
    asyncio.run(main())