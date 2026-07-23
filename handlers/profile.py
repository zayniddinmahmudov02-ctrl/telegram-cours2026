from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database import db_execute
from keyboards import profile_keyboard, main_menu
from states.profile import ProfileState

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
            course,
            total_score,
            daily_score,
            unlocked_level
        FROM users
        WHERE user_id = %s
        """,
        (message.from_user.id,),
        fetchone=True,
    )

    if not user:
        await message.answer(
            "❌ Profil topilmadi.\n\n/start buyrug'ini yuboring."
        )
        return

    full_name = user[0] or "-"
    phone = user[1] or "-"
    course = user[2] or "-"
    total_xp = user[3] or 0
    daily_xp = user[4] or 0
    level = user[5] or "A1"

    await message.answer(
        f"""
👤 <b>Mening Profilim</b>

👨 <b>F.I.Sh:</b> {full_name}
📱 <b>Telefon:</b> {phone}
🎓 <b>Kurs:</b> {course}

━━━━━━━━━━━━━━

🏆 <b>Umumiy XP:</b> {total_xp}
🔥 <b>Bugungi XP:</b> {daily_xp}
🎯 <b>Daraja:</b> {level}

━━━━━━━━━━━━━━

🇩🇪 <b>VIZU Academy</b>
""",
        parse_mode="HTML",
        reply_markup=profile_keyboard(),
    )