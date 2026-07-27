from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from keyboards.main import main_menu

router = Router()

MAINTENANCE_TEXT = (
    "🛠 <b>Ta'minot ishlari</b>\n\n"
    "Homework bo'limida texnik yangilash va takomillashtirish ishlari olib borilmoqda.\n\n"
    "⏳ Ushbu bo'lim tez orada qayta ishga tushiriladi.\n\n"
    "🙏 Tushunganingiz uchun rahmat!\n"
    "<b>VIZU Academy</b>"
)


# =========================================================
# HOMEWORK
# =========================================================

@router.message(F.text == "📝 Homework")
async def homework_menu(message: Message):
    await message.answer(
        MAINTENANCE_TEXT,
        parse_mode="HTML",
    )


@router.callback_query(F.data == "homework")
async def homework_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        MAINTENANCE_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu,
    )
    await callback.answer()


# =========================================================
# BARCHA HOMEWORK TUGMALARI
# =========================================================

@router.callback_query(
    F.data.in_(
        {
            "hw_online",
            "hw_video",
            "hw_speaking",
            "hw_teacher",
        }
    )
)
async def maintenance(callback: CallbackQuery):
    await callback.answer("Bo'lim vaqtincha yopilgan.")
    await callback.message.edit_text(
        MAINTENANCE_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu,
    )


# =========================================================
# BACK
# =========================================================

@router.callback_query(F.data == "hw_back")
async def back(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏠 <b>Asosiy menyu</b>",
        parse_mode="HTML",
        reply_markup=main_menu,
    )
    await callback.answer()