from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from database import db_execute
from services.quiz import start_quiz_block


async def check_retry(
    message: Message,
    level: str,
    block: int,
):
    user_id = message.from_user.id

    result = await db_execute(
        """
        SELECT best_score
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

    if not result:

        await start_quiz_block(
            message=message,
            level=level,
            block=block,
        )
        return

    best = result["best_score"] or 0

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Qayta ishlash",
                    callback_data=f"retryconfirm:{level}:{block}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data="cancelquiz",
                )
            ],
        ]
    )

    await message.answer(
        (
            "⚠️ <b>Diqqat!</b>\n\n"
            "Siz ushbu blokni avval ishlagansiz.\n\n"
            f"🏆 Eng yaxshi natija: <b>{best}/100</b>\n\n"
            "Blokni qayta ishlasangiz:\n"
            "• faqat rekord natija saqlanadi;\n"
            "• qo'shimcha XP berilmaydi.\n\n"
            "Davom etasizmi?"
        ),
        parse_mode="HTML",
        reply_markup=keyboard,
    )