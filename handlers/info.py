from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
)

from keyboards.info import (
    info_menu,
    back_button,
    social_keyboard,
    admin_keyboard,
)

from keyboards.main_menu import main_menu

from texts.info import (
    INFO_MENU_TEXT,
    VIZU_TEXT,
    AUTHOR_TEXT,
    SOCIAL_TEXT,
    ADMIN_TEXT,
)

router = Router()


# =========================================================
# INFO MENU
# =========================================================

@router.message(F.text == "📚 Ma'lumotlar")
async def info_menu_handler(message: Message):

    await message.answer(
        INFO_MENU_TEXT,
        reply_markup=info_menu,
        parse_mode="HTML",
    )


# =========================================================
# BACK TO MENU
# =========================================================

@router.callback_query(F.data == "info_menu")
async def info_back(callback: CallbackQuery):

    await callback.message.edit_text(
        INFO_MENU_TEXT,
        reply_markup=info_menu,
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# VIZU ACADEMY
# =========================================================

@router.callback_query(F.data == "info_vizu")
async def vizu_info(callback: CallbackQuery):

    await callback.message.edit_text(
        VIZU_TEXT,
        reply_markup=back_button,
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# AUTHOR
# =========================================================

@router.callback_query(F.data == "info_author")
async def author_info(callback: CallbackQuery):

    await callback.message.edit_text(
        AUTHOR_TEXT,
        reply_markup=back_button,
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# SOCIAL
# =========================================================

@router.callback_query(F.data == "info_social")
async def social_info(callback: CallbackQuery):

    await callback.message.edit_text(
        SOCIAL_TEXT,
        reply_markup=social_keyboard,
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# ADMIN
# =========================================================

@router.callback_query(F.data == "info_admin")
async def admin_info(callback: CallbackQuery):

    await callback.message.edit_text(
        ADMIN_TEXT,
        reply_markup=admin_keyboard,
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# EXIT
# =========================================================

@router.callback_query(F.data == "info_back")
async def close_info(callback: CallbackQuery):

    await callback.message.delete()

    await callback.message.answer(
        "🏠 Asosiy menyu",
        reply_markup=main_menu,
    )

    await callback.answer()