from aiogram import (
    F,
    Router,
)
from aiogram.types import (
    FSInputFile,
    Message,
)

from keyboards.certificate import (
    certificate_menu,
)
from handlers.wordgame import (
    build_level_menu,
)

from services.certificate import (
    build_all_statuses,
    certificate_ready,
)
from services.certificate_generator import (
    generate_certificate,
)
from services.logger import logger

router = Router()

# =========================================================
# CONSTANTS
# =========================================================

CERTIFICATE_TITLE = (
    "🏅 <b>W-ZERTIFIKAT</b>\n\n"
)

READY_TEXT = "✅ Tayyor"

NOT_STARTED_TEXT = (
    "❌ Boshlanmagan"
)

IN_PROGRESS_TEXT = (
    "📚 Jarayonda"
)

CERTIFICATE_BUTTONS = {
    "🏅 A1 W-Zertifikat": "A1",
    "🏅 A2 W-Zertifikat": "A2",
    "🏅 B1 W-Zertifikat": "B1",
    "🏅 B2 W-Zertifikat": "B2",
    "🏅 C1 W-Zertifikat": "C1",
}
# =========================================================
# BUILD MESSAGE
# =========================================================

def build_certificate_text(
    statuses: list[dict],
) -> str:

    text = (
        CERTIFICATE_TITLE
        + "Quyida barcha darajalaringiz holati ko'rsatilgan.\n\n"
    )

    for status in statuses:

        text += (
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"🎯 <b>{status['level']}</b>\n\n"
        )

        if status["ready"]:

            text += (
                f"{READY_TEXT}\n"
                f"📊 O'rtacha natija: {status['average']}%\n"
                f"🏅 Daraja: {status['rank']}\n\n"
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
            f"{IN_PROGRESS_TEXT}\n\n"
            f"✅ Tugallangan bloklar: {status['completed_blocks']}\n"
            f"🔒 Qolgan bloklar: {status['remaining_blocks']}\n\n"
            "ℹ️ Sertifikat olish uchun barcha bloklarni "
            "kamida 60% natija bilan yakunlang.\n\n"
        )

    return text


# =========================================================
# CERTIFICATE MENU
# =========================================================

@router.message(
    F.text == "🏅 W-Zertifikat"
)
async def certificate_handler(
    message: Message,
):

    statuses = build_all_statuses(
        message.from_user.id,
    )

    await message.answer(
        build_certificate_text(
            statuses,
        ),
        parse_mode="HTML",
        reply_markup=certificate_menu(
            statuses,
        ),
    )
# =========================================================
# DOWNLOAD CERTIFICATE
# =========================================================

@router.message(
    F.text.in_(CERTIFICATE_BUTTONS)
)
async def download_certificate(
    message: Message,
):

    level = CERTIFICATE_BUTTONS[
        message.text
    ]

    if not certificate_ready(
        message.from_user.id,
        level,
    ):

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

    try:
        pdf_path = generate_certificate(
            user_id=message.from_user.id,
            level=level,
        )

    except Exception as e:

        logger.error(
            f"Certificate generation failed "
            f"(user={message.from_user.id}, level={level}): {e}"
        )

        await message.answer(
            "❌ Sertifikatni tayyorlashda xatolik yuz berdi. "
            "Birozdan so'ng qayta urinib ko'ring."
        )

        return

    await message.answer_document(
        FSInputFile(pdf_path),
        caption=(
            f"🏅 <b>{level} W-Zertifikat</b>\n\n"
            "Tabriklaymiz! 🎉"
        ),
        parse_mode="HTML",
    )


# =========================================================
# BACK TO LEVELS
# =========================================================

@router.message(
    F.text == "⬅️ Darajalar"
)
async def back_to_levels(
    message: Message,
):

    await message.answer(
        "🎯 Darajani tanlang.",
        reply_markup=await build_level_menu(
            message.from_user.id,
        ),
    )