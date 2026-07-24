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

ADMIN_ID = int(
    os.getenv("ADMIN_ID", "0")
)


BUYERS_CHANNEL_ID = int(
    os.getenv("BUYERS_CHANNEL_ID", "0")
)

CHANNEL_USERNAME = "@vizu_deutsch"

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

# =========================================================
# COURSE INFO
# =========================================================
COURSE_INFO = {
    "🇩🇪 A1": {
        "lessons": 14,
        "old_price": "100.000 so'm",
        "price": "50.000 so'm"
    },
    "🇩🇪 A2": {
        "lessons": 14,
        "old_price": "200.000 so'm",
        "price": "100.000 so'm"
    },
    "🇩🇪 B1": {
        "lessons": 20,
        "old_price": "200.000 so'm",
        "price": "100.000 so'm"
    },
    "🔥 A1-B1": {
        "lessons": 48,
        "old_price": "400.000 so'm",
        "price": "200.000 so'm"
    },
    "🔥 A1-C1": {
        "lessons": 100,
        "old_price": "800.000 so'm",
        "price": "400.000 so'm"
    }
}
# =========================================================
# MEDIEN CHANNELS
# =========================================================

FILM_CHANNEL_ID =-1004392327496

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
    },
    "A2": {
        "file": "A2-words.csv",
    },
    "B1": {
        "file": "B1-words.csv",
    },
    "B2": {
        "file": "B2-words.csv",
    },
    "C1": {
        "file": "C1-words.csv",
    },
}
# =========================================================
# QUIZ STORAGE
# =========================================================

QUIZ_DATA = {}

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
# RUNTIME STORAGE
# =========================================================

active_questions = {}

answered_users = {}

quiz_sessions = {}

quiz_running = {}