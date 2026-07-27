from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

router = Router()

MAINTENANCE_TEXT = (
    "🛠 <b>Ta'minot ishlari</b>\n\n"
    "Media bo'limi hozirda yangilanmoqda.\n\n"
    "🎬 Kitoblar, filmlar, musiqa va boshqa media materiallari "
    "tez orada yana foydalanish uchun ochiladi.\n\n"
    "⏳ Iltimos, biroz kuting.\n\n"
    "🙏 Tushunganingiz uchun rahmat!\n"
    "<b>VIZU Academy</b>"
)


@router.message(F.text == "🎬 Media")
async def media_menu(message: Message):
    await message.answer(
        MAINTENANCE_TEXT,
        parse_mode="HTML",
    )


@router.callback_query(F.data == "media")
async def media_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        MAINTENANCE_TEXT,
        parse_mode="HTML",
    )
    await callback.answer("Bo'lim vaqtincha yopilgan.")