from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database import db_execute
from keyboards import profile_keyboard
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
        fetchone=True
    )

    if not user:
        await message.answer("❌ Profil topilmadi.")
        return

    await message.answer(
        f"👤 Mening Profilim\n\n"
        f"👨 Ism: {user[0] or '-'}\n"
        f"📱 Telefon: {user[1] or '-'}\n"
        f"🎓 Kurs: {user[2] or '-'}\n\n"
        f"🏆 Umumiy XP: {user[3] or 0}\n"
        f"🔥 Bugungi XP: {user[4] or 0}\n"
        f"🔓 Daraja: {user[5] or 'A1'}",
        reply_markup=profile_keyboard()
    )


# =========================================================
# CHANGE NAME START
# =========================================================

@router.message(F.text == "✏️ Ism Familiyani o'zgartirish")
async def change_name_start(
    message: Message,
    state: FSMContext
):
    await state.set_state(ProfileState.change_name)

    await message.answer(
        "✏️ Yangi ism va familiyangizni yuboring.\n\n"
        "Masalan:\n"
        "Zayniddin Mahmudov"
    )


# =========================================================
# CHANGE NAME SAVE
# =========================================================

@router.message(StateFilter(ProfileState.change_name))
async def change_name_save(
    message: Message,
    state: FSMContext
):
    full_name = message.text.strip()
    words = full_name.split()

    if len(words) < 2 or any(len(word) < 2 for word in words):
        await message.answer(
            "❌ Iltimos, ism va familiyangizni to'liq va to'g'ri kiriting.\n"
            "Masalan: Zayniddin Mahmudov"
        )
        return

    db_execute(
        """
        UPDATE users
        SET full_name = %s
        WHERE user_id = %s
        """,
        (full_name, message.from_user.id)
    )

    await state.clear()

    await message.answer(
        "✅ Ism familiya yangilandi.",
        reply_markup=profile_keyboard()
    )