from aiogram import Router, F
from aiogram.types import (
    Message,
)

from config import (
    LEVEL_ORDER,
    LEVEL_CONFIG,
)

from database import db_execute

router = Router()

# =========================================================
# CONSTANTS
# =========================================================

CERTIFICATE_TITLE = (
    "🏅 <b>W-ZERTIFIKAT</b>\n\n"
)

READY_TEXT = "✅ Tayyor"
NOT_STARTED_TEXT = "❌ Boshlanmagan"

# =========================================================
# GRADE SYSTEM
# =========================================================

def calculate_grade(
    average: int,
) -> str:

    if average >= 90:
        return "🥇 Gold"

    if average >= 80:
        return "🥈 Silver"

    if average >= 70:
        return "🥉 Bronze"

    return "✅ Pass"

# =========================================================
# LEVEL STATUS
# =========================================================

def get_level_status(
    user_id: int,
    level: str,
) -> dict:

    config = LEVEL_CONFIG[level]

    total_blocks = config["blocks"]
    block_size = config["size"]

    completed_blocks = 0
    total_percent = 0

    for block in range(1, total_blocks + 1):

        row = db_execute(
            """
            SELECT
                best_score
            FROM quiz_progress
            WHERE user_id=%s
              AND level=%s
              AND block_number=%s
            """,
            (
                user_id,
                level,
                block,
            ),
            fetchone=True,
        )

        if not row:
            continue

        score = row["best_score"] or 0

        percent = round(
            score / block_size * 100
        )

        total_percent += percent

        if percent >= 60:
            completed_blocks += 1

    remaining_blocks = (
        total_blocks - completed_blocks
    )

    if completed_blocks == 0:

        return {
            "level": level,
            "ready": False,
            "started": False,
            "average": 0,
            "grade": "",
            "completed_blocks": 0,
            "remaining_blocks": total_blocks,
        }

    if remaining_blocks > 0:

        average = round(
            total_percent / completed_blocks
        )

        return {
            "level": level,
            "ready": False,
            "started": True,
            "average": average,
            "grade": "",
            "completed_blocks": completed_blocks,
            "remaining_blocks": remaining_blocks,
        }

    average = round(
        total_percent / total_blocks
    )

    return {
        "level": level,
        "ready": True,
        "started": True,
        "average": average,
        "grade": calculate_grade(
            average
        ),
        "completed_blocks": completed_blocks,
        "remaining_blocks": 0,
    }

# =========================================================
# BUILD CERTIFICATE TEXT
# =========================================================

def build_certificate_text(
    statuses: list,
) -> str:

    text = CERTIFICATE_TITLE

    text += (
        "Quyida barcha darajalaringiz holati "
        "ko'rsatilgan.\n\n"
    )

    for status in statuses:

        text += "━━━━━━━━━━━━━━━━━━\n\n"

        text += (
            f"🎯 <b>{status['level']}</b>\n\n"
        )

        if status["ready"]:

            text += (
                f"{READY_TEXT}\n"
                f"📊 O'rtacha natija: "
                f"{status['average']}%\n"
                f"🏅 Daraja: "
                f"{status['grade']}\n\n"
                "📄 Sertifikat olish mumkin.\n\n"
            )

            continue

        if not status["started"]:

            text += (
                f"{NOT_STARTED_TEXT}\n\n"
                "Bu daraja hali boshlanmagan.\n\n"
            )

            continue

        text += (
            "📚 Jarayonda\n\n"
            f"✅ Tugallangan bloklar: "
            f"{status['completed_blocks']}\n"
            f"🔒 Qolgan bloklar: "
            f"{status['remaining_blocks']}\n\n"
            "ℹ️ Sertifikat olish uchun\n"
            "barcha bloklarni kamida\n"
            "60% natija bilan yakunlang.\n\n"
        )

    return text
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
)

# =========================================================
# BUILD KEYBOARD
# =========================================================

def build_certificate_keyboard(
    statuses: list,
) -> ReplyKeyboardMarkup:

    rows = []

    for status in statuses:

        if status["ready"]:

            rows.append(
                [
                    KeyboardButton(
                        text=f"📄 {status['level']} Sertifikat"
                    )
                ]
            )

    rows.append(
        [
            KeyboardButton(
                text="⬅️ Darajalar"
            )
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
    )


# =========================================================
# CERTIFICATE MENU
# =========================================================

@router.message(F.text == "🏅 W-Zertifikat")
async def certificate_handler(
    message: Message,
):

    statuses = []

    for level in LEVEL_ORDER:

        statuses.append(
            get_level_status(
                user_id=message.from_user.id,
                level=level,
            )
        )

    await message.answer(
        build_certificate_text(statuses),
        parse_mode="HTML",
        reply_markup=build_certificate_keyboard(
            statuses
        ),
    )


# =========================================================
# DOWNLOAD BUTTONS
# =========================================================

CERTIFICATE_BUTTONS = [
    "📄 A1 Sertifikat",
    "📄 A2 Sertifikat",
    "📄 B1 Sertifikat",
    "📄 B2 Sertifikat",
    "📄 C1 Sertifikat",
]


@router.message(
    F.text.in_(CERTIFICATE_BUTTONS)
)
async def download_certificate(
    message: Message,
):

    level = (
        message.text
        .replace("📄 ", "")
        .replace(" Sertifikat", "")
        .strip()
    )

    status = get_level_status(
        user_id=message.from_user.id,
        level=level,
    )

    if not status["ready"]:

        await message.answer(
            "❌ Ushbu sertifikat hali tayyor emas."
        )

        return

    await message.answer(
        (
            f"📄 {level} sertifikati tayyor.\n\n"
            "⏳ PDF tayyorlanmoqda..."
        )
    )

    # =====================================================
    # 2-qismda yoziladigan generator
    #
    # pdf_path = generate_certificate(
    #     user_id=message.from_user.id,
    #     level=level,
    #     average=status["average"],
    #     grade=status["grade"],
    # )
    #
    # await message.answer_document(
    #     FSInputFile(pdf_path)
    # )
    # =====================================================


# =========================================================
# BACK TO LEVELS
# =========================================================

@router.message(
    F.text == "⬅️ Darajalar"
)
async def back_to_levels(
    message: Message,
):

    from handlers.wordgame import (
        build_level_menu,
    )

    menu = await build_level_menu(
        message.from_user.id
    )

    await message.answer(
        "🎯 Darajani tanlang.",
        reply_markup=menu,
    )