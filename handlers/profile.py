from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database import db_execute
from keyboards import main_menu, profile_keyboard
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
        parse_mode="HTML",
        reply_markup=profile_keyboard(),
    )


# =========================================================
# CHANGE FULL NAME
# =========================================================

@router.message(F.text == "✏️ Ism va familiyani o'zgartirish")
async def change_full_name(message: Message, state: FSMContext):

    await state.set_state(ProfileState.waiting_new_name)

    await message.answer(
        """
✏️ <b>Ism va familiyani o'zgartirish</b>

Yangi ism va familiyangizni yuboring.

Masalan:

<i>Zayniddin Makhmudov</i>
""",
        parse_mode="HTML",
    )


# =========================================================
# SAVE NEW FULL NAME
# =========================================================

@router.message(ProfileState.waiting_new_name)
async def save_full_name(message: Message, state: FSMContext):

    full_name = message.text.strip()

    if len(full_name) < 3:
        await message.answer(
            "❌ Ism va familiya kamida 3 ta belgidan iborat bo'lishi kerak."
        )
        return

    db_execute(
        """
        UPDATE users
        SET full_name=%s
        WHERE user_id=%s
        """,
        (
            full_name,
            message.from_user.id,
        ),
    )

    await state.clear()

    await message.answer(
        "✅ Ism va familiyangiz muvaffaqiyatli yangilandi.",
        reply_markup=profile_keyboard(),
    )


# =========================================================
# MY CERTIFICATES
# =========================================================

@router.message(F.text == "🏆 Mening Sertifikatlarim")
async def my_certificates(message: Message):

    certificates = db_execute(
        """
        SELECT
            level,
            certificate_type,
            score,
            issue_date
        FROM certificates
        WHERE user_id=%s
        ORDER BY issue_date DESC
        """,
        (message.from_user.id,),
        fetch=True,
    )

    if not certificates:

        await message.answer(
            """
🏆 <b>Mening Sertifikatlarim</b>

Sizda hozircha sertifikat mavjud emas.

📚 Kurslarni muvaffaqiyatli yakunlaganingizdan so'ng sertifikatlaringiz shu yerda ko'rinadi.
""",
            parse_mode="HTML",
        )
        return

    text = "🏆 <b>Mening Sertifikatlarim</b>\n\n"

    for certificate in certificates:

        text += (
            f"🎓 <b>{certificate['level']}</b>\n"
            f"🥇 Daraja: {certificate['certificate_type']}\n"
            f"📊 Ball: {certificate['score']}%\n"
            f"📅 Sana: {certificate['issue_date'].strftime('%d.%m.%Y')}\n\n"
        )

    await message.answer(
        text,
        parse_mode="HTML",
    )


# =========================================================
# BACK TO MAIN MENU
# =========================================================

@router.message(F.text == "⬅️ Orqaga")
async def back_to_main_menu(message: Message):

    await message.answer(
        "🏠 Bosh menyu",
        reply_markup=main_menu(),
    )