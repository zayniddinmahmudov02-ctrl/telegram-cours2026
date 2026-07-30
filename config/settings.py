import os
from dotenv import load_dotenv

# =========================================================
# LOAD ENV
# =========================================================

load_dotenv()

# =========================================================
# BOT CONFIG
# =========================================================

BOT_NAME = "vizu_academy_bot"

TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# =========================================================
# ADMINS
# =========================================================

_ADMIN_IDS_RAW = os.getenv("ADMIN_IDS") or os.getenv("ADMIN_ID", "")

ADMIN_IDS = [
    int(x)
    for x in _ADMIN_IDS_RAW.split(",")
    if x.strip()
]

# Orqaga moslik
ADMIN_ID = ADMIN_IDS[0] if ADMIN_IDS else 0

# To'lovlar keladigan admin kanal
ADMIN_CHANNEL_ID = int(
    os.getenv("ADMIN_CHANNEL_ID", "0")
)

CHANNEL_USERNAME = "@vizu_deutsch"

# Numeric chat id of the mandatory subscription channel.
# get_chat_member() works with the username above too, but the
# numeric id is more reliable (usernames can change).
CHANNEL_ID = int(
    os.getenv("CHANNEL_ID", "0")
)

# =========================================================
# DIRECTORIES
# =========================================================

GENERATED_DIR = "generated"
CERTIFICATE_DIR = "certificates"

# =========================================================
# SYSTEM
# =========================================================

TOTAL_WORDS = 5555

# =========================================================
# COURSE LINKS
# =========================================================

COURSE_LINKS = {
    "🇩🇪 A1": "https://t.me/+Kmh9agD9LDRlNGZi",
    "🇩🇪 A2": "https://t.me/+SZCN9fthZcpiZDEy",
    "🇩🇪 B1": "https://t.me/+1l2f9IQWIfg1ZTZi",
    "🔥 A1-B1": "https://t.me/+uN_dHBYQCUY0MzUy",
    "🔥 A1-C1": "https://t.me/+oRNjGr3PoY5kYjIy",
}

# =========================================================
# GROUP LINKS
# =========================================================

GROUP_LINKS = {
    "🇩🇪 A1": "https://t.me/+fvnLkVcG29k5ZDhi",
    "🇩🇪 A2": "https://t.me/+Z91t_jwr7i82MGZi",
    "🇩🇪 B1": "https://t.me/+N1DgYCQSRK80ZmZi",
    "🔥 A1-B1": "https://t.me/+WAm5rG5jr4M0ZjVi",
    "🔥 A1-C1": "https://t.me/+toQIeCS3Obo3MDVi",
}

# =========================================================
# COURSE INFO
# =========================================================

COURSE_INFO = {
    "🇩🇪 A1": {
        "lessons": 14,
        "old_price": "100.000 so'm",
        "price": 50000,
        "price_text": "50.000 so'm",
    },

    "🇩🇪 A2": {
        "lessons": 14,
        "old_price": "200.000 so'm",
        "price": 100000,
        "price_text": "100.000 so'm",
    },

    "🇩🇪 B1": {
        "lessons": 20,
        "old_price": "200.000 so'm",
        "price": 100000,
        "price_text": "100.000 so'm",
    },

    "🔥 A1-B1": {
        "lessons": 48,
        "old_price": "400.000 so'm",
        "price": 200000,
        "price_text": "200.000 so'm",
    },

    "🔥 A1-C1": {
        "lessons": 100,
        "old_price": "800.000 so'm",
        "price": 400000,
        "price_text": "400.000 so'm",
    },
}

# =========================================================
# CHANNELS
# =========================================================

FILM_CHANNEL_ID = -1004392327496

# =========================================================
# SECURITY CHECK
# =========================================================

if not TOKEN:
    raise ValueError("TOKEN topilmadi")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL topilmadi")

if ADMIN_CHANNEL_ID == 0:
    raise ValueError("ADMIN_CHANNEL_ID topilmadi")

# =========================================================
# SOCIAL LINKS
# =========================================================

ADMIN_URL = "https://t.me/Mahmudow_Z"

CHANNEL_URL = "https://t.me/vizu_deutsch"

INSTAGRAM_URL = "https://instagram.com/vizu_deutsch"

YOUTUBE_URL = "https://youtube.com/@vizu_deutsch"

WEBSITE_URL = "https://vizu-deutsch.com"

RESULTS_URL = "https://t.me/+o8b2cf3rwAs1MzFi"

# =========================================================
# FILES
# =========================================================

TEACHER_PHOTO = "teacher.jpg"

# =========================================================
# LEVEL CONFIG
# =========================================================

LEVEL_CONFIG = {
    "A1": {
        "file": "A1-words.csv",
        "blocks": 10,
        "size": 100,
        "required": 600,
    },
    "A2": {
        "file": "A2-words.csv",
        "blocks": 10,
        "size": 100,
        "required": 600,
    },
    "B1": {
        "file": "B1-words.csv",
        "blocks": 10,
        "size": 100,
        "required": 600,
    },
    "B2": {
        "file": "B2-words.csv",
        "blocks": 15,
        "size": 100,
        "required": 900,
    },
    "C1": {
        "file": "C1-words.csv",
        "blocks": 11,
        "size": 100,
        "required": 600,
    },
}
# =========================================================
# LEVEL ORDER
# =========================================================

LEVEL_ORDER = [
    "A1",
    "A2",
    "B1",
    "B2",
    "C1",
]

# =========================================================
# QUIZ STORAGE
# =========================================================

QUIZ_DATA = {}

quiz_sessions = {}

quiz_running = set()

active_questions = {}

answered_users = {}