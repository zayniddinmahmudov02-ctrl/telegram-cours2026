from aiogram import Router, F
from aiogram.types import Message

from database import db_execute

router = Router()


@router.message(F.text == "🔥 XP Reytingi")
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
        fetchall=True,
    )

    if not rows:
        await message.answer("🏆 Hozircha reyting mavjud emas.")
        return

    medals = ["🥇", "🥈", "🥉"]

    text = "🏆 <b>TOP 100 XP Reyting</b>\n\n"

    for index, (name, score) in enumerate(rows, start=1):
        prefix = medals[index - 1] if index <= 3 else f"{index}."

        text += (
            f"{prefix} "
            f"{name or 'Foydalanuvchi'} — "
            f"{score or 0} XP\n"
        )

    await message.answer(
        text,
        parse_mode="HTML",
    )