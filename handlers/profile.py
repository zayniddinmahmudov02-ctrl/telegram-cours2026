from aiogram import F, Router
from aiogram.types import Message

from database import db_execute
from keyboards import profile_keyboard

router = Router()


# =========================================================
# MY PROFILE
# =========================================================

@router.message(F.text == "👤 Mening Profilim")
async def my_profile(message: Message):

    user = db_execute(
        """
        SELECT
            full_name,
            phone,
            total_score,
            daily_score,
            unlocked_level
        FROM users
        WHERE user_id=%s
        """,
        (message.from_user.id,),
        fetchone=True,
    )

    if not user:
        await message.answer(
            "❌ Profil topilmadi.\n\n/start buyrug'ini yuboring."
        )
        return

    full_name = user["full_name"] or "-"
    phone = user["phone"] or "-"
    total_xp = user["total_score"] or 0
    daily_xp = user["daily_score"] or 0
    level = user["unlocked_level"] or "A1"

    await message.answer(
        f"""
👤 <b>Mening Profilim</b>

👨 <b>F.I.Sh:</b> {full_name}
📱 <b>Telefon:</b> {phone}

━━━━━━━━━━━━━━

🏆 <b>Umumiy XP:</b> {total_xp}
🔥 <b>Bugungi XP:</b> {daily_xp}
🎯 <b>Daraja:</b> {level}

━━━━━━━━━━━━━━

🇩🇪 <b>VIZU Academy</b>
""",
        reply_markup=profile_keyboard(),
    )