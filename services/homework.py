import re

from config import LEVEL_ORDER

# =========================================================
# FSM BAIL-OUT
# =========================================================
# Free-text FSM steps (password entry, profile fields) must not
# swallow a user tapping a main-menu / admin-menu button while
# mid-flow - same defensive pattern as handlers.payment's explicit
# exit-text check. Any of these arriving during a Hausaufgaben
# text step aborts the flow instead of being treated as input.

MENU_EXIT_TEXTS = {
    "/start",
    "🏠 Bosh menyu",
    "📚 Artikel Topish",
    "🎮 So'z O'yini",
    "🎥 Video Kurslar",
    "🎬 Medien",
    "📚 Ma'lumotlar",
    "👤 Mening Profilim",
    "📚 Hausaufgaben",
    "👨‍💼 Admin Panel",
    "⬅️ Admin Chiqish",
}


def is_menu_exit(text: str | None) -> bool:
    return text in MENU_EXIT_TEXTS

# =========================================================
# SCORE -> STATUS MAPPING
# =========================================================

SCORE_LABELS = {
    1: "Vazifa tushunilmagan",
    2: "Qoniqarsiz, qayta bajaring",
    3: "Qabul qilishga yetarli emas, qayta bajaring",
    4: "Qabul qilindi, lekin yaxshilanish kerak",
    5: "Juda yaxshi bajarilgan",
}

SCORE_RESULT_STATUS = {
    1: "revision_required",
    2: "revision_required",
    3: "revision_required",
    4: "accepted",
    5: "excellent",
}

STATUS_LABELS = {
    "draft": "✏️ Qoralama",
    "submitted": "🟡 Ko'rib chiqilmoqda",
    "revision_required": "🔴 Qayta ishlash kerak",
    "accepted": "🟢 Qabul qilindi",
    "excellent": "🌟 A'lo baholandi",
}


def score_to_result_status(score: int) -> str:
    return SCORE_RESULT_STATUS[score]


def score_label(score: int) -> str:
    return SCORE_LABELS[score]


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


# =========================================================
# FILE TYPE LABELS
# =========================================================

FILE_TYPE_LABELS = {
    "audio": "🎤 Audio",
    "voice": "🎤 Audio",
    "photo": "🖼 Rasm",
    "document": "📄 Fayl",
    "pdf": "📄 PDF",
    "text": "📝 Matn",
}


# =========================================================
# VALIDATION
# =========================================================

_NAME_RE = re.compile(r"^[A-Za-zÀ-ÿʻ'`\-Ѐ-ӿ ]{2,40}$")


def is_valid_name(value: str) -> bool:
    return bool(_NAME_RE.fullmatch(value.strip()))


def is_valid_level(value: str) -> bool:
    return value.strip().upper() in LEVEL_ORDER


def normalize_level(value: str) -> str:
    return value.strip().upper()


def parse_lesson_number(value: str) -> int | None:
    value = value.strip()

    if not value.isdigit():
        return None

    lesson = int(value)

    if lesson < 1 or lesson > 300:
        return None

    return lesson


# =========================================================
# LEVEL GROUPS (Sprechen guruh only)
# =========================================================
# Sprechen collects a level *group* instead of a single level - the
# stored/internal value (dict key, fits the existing
# homework_submissions.level VARCHAR(5) column unchanged) vs. the
# button/display label (dict value).

LEVEL_GROUP_LABELS = {
    "0-A1": "🟢 0–A1",
    "A2-B1": "🟡 A2–B1",
    "B2-C1": "🔵 B2–C1",
}


def is_valid_level_group(value: str) -> bool:
    return value in LEVEL_GROUP_LABELS


# =========================================================
# GENDER (Sprechen guruh only)
# =========================================================

GENDER_LABELS = {
    "male": "👨 Erkak",
    "female": "👩 Ayol",
}


def is_valid_gender(value: str) -> bool:
    return value in GENDER_LABELS


# =========================================================
# SPRECHEN LESSONS (fixed 1-20, button-selected - never typed)
# =========================================================

SPRECHEN_LESSON_COUNT = 20


def is_valid_sprechen_lesson(lesson_number: int) -> bool:
    return 1 <= lesson_number <= SPRECHEN_LESSON_COUNT


# =========================================================
# SPRECHEN ACCESS VALIDITY
# =========================================================
# The single source of truth for "does this member currently have
# access" - checked at every Sprechen entry point AND every content
# handler (menu, lesson select, profile, total score, deep-links),
# never just once at the door. Every one of these must hold:
#
#   1. category exists and is active
#   2. gender is a recognized value (not just "something present")
#   3. level_group is a recognized value (same)
#   4. the password snapshot stamped on the membership (see
#      database.homework.set_membership_access_password) matches
#      the category's CURRENT password_hash
#
# homework_categories.password_hash is the only authority for #4 -
# the membership's stamped hash never overrides it, it can only
# ever match or fail to match whatever the category's live value
# currently is. Changing the category password (database.homework.
# set_homework_category_password) also clears every membership's
# stamped hash in the same atomic statement, so #4 fails for every
# existing member immediately and unconditionally on rotation -
# this comparison is a second, independent guard against the same
# thing, not the only one.

def is_sprechen_access_valid(membership: dict | None, category: dict | None) -> bool:
    if not membership or not category:
        return False

    if not category.get("is_active"):
        return False

    gender = membership.get("gender")
    level_group = membership.get("level_group")

    if not gender or not is_valid_gender(gender):
        return False

    if not level_group or not is_valid_level_group(level_group):
        return False

    stamped = membership.get("access_password_hash")
    current = category.get("password_hash")

    return bool(stamped and current and stamped == current)


# =========================================================
# CHANNEL MESSAGE TEXT
# =========================================================

def build_submission_header(
    submission_uid: str,
    first_name: str,
    last_name: str,
    category_name: str,
    level: str,
    lesson_number: int,
    user_id: int,
    file_count: int,
    created_at,
    level_label: str = "Daraja",
    gender: str | None = None,
) -> str:
    gender_line = (
        f"⚥ <b>Jins:</b> {GENDER_LABELS.get(gender, gender)}\n" if gender else ""
    )

    return (
        f"📥 <b>Yangi Hausaufgaben</b>\n\n"
        f"👤 <b>{first_name} {last_name}</b>\n"
        f"{gender_line}"
        f"📚 <b>Kategoriya:</b> {category_name}\n"
        f"📊 <b>{level_label}:</b> {level}\n"
        f"📖 <b>Dars:</b> {lesson_number}-dars\n"
        f"🆔 <b>Submission:</b> <code>{submission_uid}</code>\n"
        f"👤 <b>User ID:</b> <code>{user_id}</code>\n"
        f"🕐 <b>Sana:</b> {created_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"📎 <b>Fayllar soni:</b> {file_count}"
    )


def build_result_message(
    category_name: str,
    lesson_number: int,
    score: int,
) -> str:
    return (
        f"🏆 Vazifangiz baholandi.\n\n"
        f"📚 {category_name}\n"
        f"📖 {lesson_number}-dars\n"
        f"⭐ Ball: {score}/5\n\n"
        f"{score_label(score)}"
    )
