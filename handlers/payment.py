# =========================================================
# PAYMENT HANDLERS
# =========================================================

from aiogram import F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from config import *
from database import db_execute
from keyboards import *
from states.register import RegisterState


# =========================================================
# SEND RECEIPT TO ADMIN
# =========================================================

async def send_admin_receipt(
    bot,
    logger,
    photo: str,
    full_name: str,
    phone: str,
    user,
    course: str,
):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Approve",
                    callback_data=f"approve:{user.id}"
                ),
                InlineKeyboardButton(
                    text="❌ Reject",
                    callback_data=f"reject:{user.id}"
                ),
            ]
        ]
    )

    username = (
        f"@{user.username}"
        if user.username
        else "Mavjud emas"
    )

    caption = (
        "💳 <b>Yangi xaridor!</b>\n\n"
        f"👤 Ism: {full_name}\n"
        f"📱 Telefon: {phone}\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📚 Kurs: <b>{course}</b>\n"
        f"🌐 Username: {username}"
    )

    try:
        await bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo,
            caption=caption,
            reply_markup=keyboard,
        )

    except Exception as e:
        logger.error(
            f"Receipt yuborishda xatolik: {e}"
        )
# =========================================================
# CHECK PAYMENT RECEIPT
# =========================================================

@dp.message(F.photo, StateFilter(None))
async def check_photo(
    message: Message,
    state: FSMContext
):
    user_id = message.from_user.id

    row = db_execute(
        """
        SELECT course
        FROM users
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True,
    )

    if not row or not row[0]:
        await message.answer(
            "❌ Avval sotib olmoqchi bo'lgan kursingizni tanlang."
        )
        return

    await state.update_data(
        photo=message.photo[-1].file_id
    )

    await message.answer(
        "👤 Ism va familiyangizni yuboring."
    )

    await state.set_state(
        RegisterState.waiting_for_name
    )


# =========================================================
# GET FULL NAME
# =========================================================

@dp.message(RegisterState.waiting_for_name)
async def get_name(
    message: Message,
    state: FSMContext
):
    full_name = message.text.strip()

    words = full_name.split()

    if (
        len(words) < 2
        or any(len(word) < 2 for word in words)
    ):
        await message.answer(
            "❌ Ism va familiyangizni to'liq kiriting.\n\n"
            "Masalan:\n"
            "Zayniddin Mahmudov"
        )
        return

    await state.update_data(
        full_name=full_name
    )

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📱 Telefon Raqamni Yuborish",
                    request_contact=True,
                )
            ]
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "📱 Telefon raqamingizni yuboring.",
        reply_markup=keyboard,
    )

    await state.set_state(
        RegisterState.waiting_for_phone
    )
# =========================================================
# GET PHONE
# =========================================================

@dp.message(RegisterState.waiting_for_phone)
async def get_phone(
    message: Message,
    state: FSMContext
):
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = "".join(
            filter(str.isdigit, message.text.strip())
        )

        if len(phone) < 9:
            await message.answer(
                "❌ Telefon raqami noto'g'ri.\n"
                "Iltimos, qaytadan kiriting."
            )
            return

    data = await state.get_data()

    photo = data["photo"]
    full_name = data["full_name"]

    user = message.from_user

    row = db_execute(
        """
        SELECT course
        FROM users
        WHERE user_id = %s
        """,
        (user.id,),
        fetchone=True,
    )

    course = (
        row[0]
        if row and row[0]
        else "Kurs tanlanmagan"
    )

    db_execute(
        """
        UPDATE users
        SET
            full_name=%s,
            phone=%s
        WHERE user_id=%s
        """,
        (
            full_name,
            phone,
            user.id,
        ),
    )

    await send_admin_receipt(
        bot=bot,
        logger=logger,
        photo=photo,
        full_name=full_name,
        phone=phone,
        user=user,
        course=course,
    )

    await message.answer(
        "✅ To'lov chekingiz muvaffaqiyatli yuborildi.\n\n"
        "⏳ Admin tasdiqlashini kuting.",
        reply_markup=main_menu,
    )

    await state.clear()

# =========================================================
# SEND COURSE LINKS
# =========================================================

async def send_course_links(
    bot,
    logger,
    user_id: int,
    full_name: str,
    course: str,
):
    course_link = COURSE_LINKS.get(course)
    group_link = GROUP_LINKS.get(course)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎥 Kurs Kanali",
                    url=course_link,
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 Savollar Guruhi",
                    url=group_link,
                )
            ],
        ]
    )

    try:
        await bot.send_message(
            chat_id=user_id,
            text=(
                f"🎉 Assalomu alaykum, {full_name}!\n\n"
                "✅ To'lovingiz tasdiqlandi.\n\n"
                f"📚 Kurs: {course}\n\n"
                "👇 Quyidagi tugmalar orqali kursga qo'shiling."
            ),
            reply_markup=keyboard,
        )

    except Exception as e:
        logger.error(
            f"Kurs havolalarini yuborishda xatolik: {e}"
        )


# =========================================================
# NOTIFY BUYERS CHANNEL
# =========================================================

async def notify_buyers_channel(
    bot,
    logger,
    user_id: int,
    full_name: str,
    course: str,
):
    try:
        await bot.send_message(
            chat_id=-1003916093529,
            text=(
                "💳 Yangi Xaridor\n\n"
                f"👤 Ism: {full_name}\n"
                f"🆔 ID: {user_id}\n"
                f"📚 Kurs: {course}\n\n"
                "✅ To'lov tasdiqlandi"
            ),
        )

    except Exception as e:
        logger.error(
            f"Buyers kanaliga yuborishda xatolik: {e}"
        )
# =========================================================
# APPROVE USER
# =========================================================

@dp.callback_query(F.data.startswith("approve:"))
async def approve_user(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "❌ Sizda ruxsat yo'q!",
            show_alert=True
        )
        return

    try:
        user_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("❌ Xatolik yuz berdi.")
        return

    db_execute(
        """
        UPDATE users
        SET approved = 1
        WHERE user_id = %s
        """,
        (user_id,)
    )

    row = db_execute(
        """
        SELECT course, full_name
        FROM users
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    if not row:
        await callback.answer("❌ Foydalanuvchi topilmadi!")
        return

    course = row[0] or "Noma'lum kurs"
    full_name = row[1] or "Talaba"

    await send_course_links(
        bot=bot,
        logger=logger,
        user_id=user_id,
        full_name=full_name,
        course=course,
    )

    await notify_buyers_channel(
        bot=bot,
        logger=logger,
        user_id=user_id,
        full_name=full_name,
        course=course,
    )

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await callback.message.answer(
        f"✅ Foydalanuvchi tasdiqlandi.\n\n"
        f"👤 {full_name}\n"
        f"📚 {course}"
    )

    await callback.answer(
        "✅ Muvaffaqiyatli tasdiqlandi"
    )


# =========================================================
# REJECT USER
# =========================================================

@dp.callback_query(F.data.startswith("reject:"))
async def reject_user(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "❌ Sizda ruxsat yo'q!",
            show_alert=True
        )
        return

    try:
        user_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer(
            "❌ Xatolik yuz berdi."
        )
        return

    db_execute(
        """
        UPDATE users
        SET
            approved = 0,
            course = NULL
        WHERE user_id = %s
        """,
        (user_id,)
    )

    try:
        await bot.send_message(
            chat_id=user_id,
            text=(
                "❌ To'lovingiz tasdiqlanmadi.\n\n"
                "Iltimos, chekni qayta yuboring yoki "
                "admin bilan bog'laning."
            )
        )

    except Exception as e:
        logger.error(
            f"Reject xabarini yuborishda xatolik: {e}"
        )

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await callback.message.answer(
        f"❌ Foydalanuvchi rad etildi.\n\n"
        f"🆔 {user_id}"
    )

    await callback.answer(
        "❌ To'lov rad etildi."
    )