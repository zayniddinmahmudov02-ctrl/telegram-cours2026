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

# Timezone used for Daily/Weekly/Monthly ranking boundaries,
# so "today"/"this week"/"this month" match the real local
# day regardless of the database server's own timezone setting.
APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Asia/Tashkent")

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

# Movie poster images, looked up by name (no extension) from
# Filme.csv's `photo` column - see services.media.resolve_movie_photo.
MOVIE_POSTERS_DIR = os.path.join("assets", "medien", "film", "photos")

# Single shared cover image used for every song in the Musik
# gallery - see services.media.resolve_music_cover.
MUSIC_COVER_PATH = os.path.join("assets", "medien", "musik", "cover_photo.png")

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
        "old_price_text": "100.000 so'm",
        "price": 49000,
        "price_text": "49.000 so'm",
    },

    "🇩🇪 A2": {
        "lessons": 14,
        "old_price_text": "200.000 so'm",
        "price": 99000,
        "price_text": "99.000 so'm",
    },

    "🇩🇪 B1": {
        "lessons": 20,
        "old_price_text": "200.000 so'm",
        "price": 99000,
        "price_text": "99.000 so'm",
    },

    "🔥 A1-B1": {
        "lessons": 48,
        "old_price_text": "400.000 so'm",
        "price": 199000,
        "price_text": "199.000 so'm",
    },

    "🔥 A1-C1": {
        "lessons": 100,
        "old_price_text": "800.000 so'm",
        "price": 399000,
        "price_text": "399.000 so'm",
    },
}

# =========================================================
# CHANNELS
# =========================================================

FILM_CHANNEL_ID = -1004392327496
BOOK_CHANNEL_ID = -1003796668138
MUSIC_CHANNEL_ID = -1003763602068

# =========================================================
# HAUSAUFGABEN (HOMEWORK)
# =========================================================
# One private channel per category - every submission is posted
# there for the admin to see and score. Centralized here (not
# scattered across handlers) so re-pointing a category to a new
# channel is a one-line change.

HOMEWORK_SP_CHANNEL_ID = -1004325769295
HOMEWORK_VIDEO_CHANNEL_ID = -1003908094525
HOMEWORK_ONLINE_CHANNEL_ID = -1003901303027

# code -> (display name, channel). `code` is also the DB row's
# `homework_categories.code` and is seeded into the DB on startup
# (see database.homework.seed_homework_categories) - this dict is
# the single source of truth for what categories exist at all;
# enable/disable and password are runtime DB state on top of it.
HOMEWORK_CATEGORIES = {
    "sprechen": {
        "name": "🗣 Sprechen guruh",
        "channel_id": HOMEWORK_SP_CHANNEL_ID,
    },
    "video": {
        "name": "🎥 Video darslar",
        "channel_id": HOMEWORK_VIDEO_CHANNEL_ID,
    },
    "online": {
        "name": "👥 Online guruhlar",
        "channel_id": HOMEWORK_ONLINE_CHANNEL_ID,
    },
}

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