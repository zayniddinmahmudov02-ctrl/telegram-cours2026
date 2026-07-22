from pathlib import Path

from aiogram import F
from aiogram.types import (
    Message,
    FSInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from loader import dp
from keyboards import info_menu
from config import (
    ADMIN_URL,
    CHANNEL_URL,
    GROUP_URL,
    INSTAGRAM_URL,
    YOUTUBE_URL,
    WEBSITE_URL,
    RESULTS_URL,
    TEACHER_PHOTO,
)


# =========================================================
# MA'LUMOTLAR MENU
# =========================================================

@dp.message(F.text == "📚 Ma'lumotlar")
async def information_menu(message: Message):
    await message.answer(
        "📚 Kerakli bo'limni tanlang.",
        reply_markup=info_menu,
    )


# =========================================================
# USTOZ HAQIDA
# =========================================================

@dp.message(F.text == "👨‍🏫 Ustoz haqida")
async def teacher_info(message: Message):

    photo_path = Path(TEACHER_PHOTO)

    if not photo_path.exists():
        await message.answer(
            "ℹ️ Ustoz haqida ma'lumot tez orada qo'shiladi."
        )
        return

    caption = (
        "👨‍🏫 <b>Zayniddinkhuja Makhmudov</b>\n\n"
        "🇩🇪 Nemis tili o'qituvchisi\n"
        "🎓 VIZU Academy asoschisi\n"
        "📚 Goethe | TestDaF | C1 tayyorlov\n"
        "💻 Online va offline kurslar"
    )

    await message.answer_photo(
        photo=FSInputFile(photo_path),
        caption=caption,
        parse_mode="HTML",
    )


# =========================================================
# NATIJALAR
# =========================================================

@dp.message(F.text == "🏆 Natijalar")
async def results(message: Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏆 Natijalarni ko'rish",
                    url=RESULTS_URL,
                )
            ]
        ]
    )

    await message.answer(
        "🎉 O'quvchilarimizning natijalari.",
        reply_markup=keyboard,
    )


# =========================================================
# ADMIN
# =========================================================

@dp.message(F.text == "📞 Admin bilan bog'lanish")
async def admin_contact(message: Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👨‍💻 Admin",
                    url=ADMIN_URL,
                )
            ]
        ]
    )

    await message.answer(
        "📩 Admin bilan bog'lanish.",
        reply_markup=keyboard,
    )


# =========================================================
# TELEGRAM CHANNEL
# =========================================================

@dp.message(F.text == "📢 Telegram Kanal")
async def telegram_channel(message: Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Kanal",
                    url=CHANNEL_URL,
                )
            ]
        ]
    )

    await message.answer(
        "📢 Rasmiy Telegram kanalimiz.",
        reply_markup=keyboard,
    )


# =========================================================
# TELEGRAM GROUP
# =========================================================

@dp.message(F.text == "💬 Telegram Guruh")
async def telegram_group(message: Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Guruh",
                    url=GROUP_URL,
                )
            ]
        ]
    )

    await message.answer(
        "💬 Savollar guruhi.",
        reply_markup=keyboard,
    )


# =========================================================
# INSTAGRAM
# =========================================================

@dp.message(F.text == "📷 Instagram")
async def instagram(message: Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📷 Instagram",
                    url=INSTAGRAM_URL,
                )
            ]
        ]
    )

    await message.answer(
        "📷 Instagram sahifamiz.",
        reply_markup=keyboard,
    )


# =========================================================
# YOUTUBE
# =========================================================

@dp.message(F.text == "▶️ YouTube")
async def youtube(message: Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="▶️ YouTube",
                    url=YOUTUBE_URL,
                )
            ]
        ]
    )

    await message.answer(
        "▶️ YouTube kanalimiz.",
        reply_markup=keyboard,
    )


# =========================================================
# WEBSITE
# =========================================================

@dp.message(F.text == "🌐 Website")
async def website(message: Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌐 Website",
                    url=WEBSITE_URL,
                )
            ]
        ]
    )

    await message.answer(
        "🌐 Rasmiy VIZU Academy sayti.",
        reply_markup=keyboard,
    )