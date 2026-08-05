from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from database import db_execute
from database.leaderboard import get_user_xp_summary
from keyboards import main_menu, profile_keyboard
from keyboards.inline.certificate import certificates_keyboard
from services.certificate_generator import generate_certificate
from services.logger import logger
from states.profile import ProfileState

router = Router()


# =========================================================
# MY PROFILE
# =========================================================

@router.message(F.text == "👤 Mening Profilim")
async def my_profile(message: Message):

    user = await db_execute(
        """
        SELECT
            full_name,
            phone,
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
    level = user["unlocked_level"] or "A1"

    xp = await get_user_xp_summary(message.from_user.id)

    accuracy_text = (
        f"{xp['accuracy']}%"
        if xp["accuracy"] is not None
        else "—"
    )

    await message.answer(
        f"""
👤 <b>Mening Profilim</b>

👨 <b>F.I.Sh:</b> {full_name}
📱 <b>Telefon:</b> {phone}

━━━━━━━━━━━━━━

⭐ <b>Bugungi XP:</b> {xp['today_xp']}
⭐ <b>Haftalik XP:</b> {xp['weekly_xp']}
⭐ <b>Oylik XP:</b> {xp['monthly_xp']}
⭐ <b>Umumiy XP:</b> {xp['overall_xp']}

🎯 <b>O'rtacha aniqlik:</b> {accuracy_text}
🎓 <b>Daraja:</b> {level}

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

    await db_execute(
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

    certificates = await db_execute(
        """
        SELECT
            level,
            certificate_type,
            score,
            rank,
            created_at
        FROM certificates
        WHERE user_id=%s
        ORDER BY created_at DESC
        """,
        (message.from_user.id,),
        fetchall=True,
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
            "📄 Turi: W-Zertifikat\n"
            f"🥇 Daraja: {certificate['rank']}\n"
            f"📊 Ball: {certificate['score']}%\n"
            f"📅 Sana: {certificate['created_at'].strftime('%d.%m.%Y')}\n"
            "✅ Holat: Berilgan\n\n"
        )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=certificates_keyboard(certificates),
    )


# =========================================================
# VIEW CERTIFICATE PDF
# =========================================================

@router.callback_query(F.data.startswith("profile_cert:"))
async def view_certificate_pdf(callback: CallbackQuery):

    level = callback.data.split(":")[1]

    try:
        pdf_path = await generate_certificate(
            user_id=callback.from_user.id,
            level=level,
        )

    except Exception as e:

        logger.error(
            f"Certificate PDF retrieval failed "
            f"(user={callback.from_user.id}, level={level}): {e}"
        )

        await callback.answer(
            "❌ Sertifikat topilmadi.",
            show_alert=True,
        )
        return

    await callback.message.answer_document(
        FSInputFile(pdf_path),
        caption=f"🏅 <b>{level} W-Zertifikat</b>",
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# BACK TO MAIN MENU
# =========================================================

@router.message(F.text == "⬅️ Orqaga")
async def back_to_main_menu(message: Message):

    await message.answer(
        "🏠 Bosh menyu",
        reply_markup=main_menu,
    )