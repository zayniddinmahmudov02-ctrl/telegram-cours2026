from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
)

from keyboards.main import main_menu_for

router = Router()


# =========================================================
# REMOVED SECTIONS - HAUSAUFGABEN / MA'LUMOTLAR
# =========================================================
# Both sections were removed from the bot. Users (and admins) can
# still have the old reply keyboard cached on their device, and old
# section messages in their chat - or homework posts in the admin
# channels - still carry inline buttons. Those entry points are
# answered here with a short notice (and a fresh main menu for
# reply buttons) instead of being silently ignored.

SECTION_REMOVED_TEXT = "ℹ️ Bu bo'lim botdan olib tashlandi."

LEGACY_SECTION_BUTTONS = {
    "📚 Hausaufgaben",
    "📋 Hausaufgaben Admin",
    "📚 Ma'lumotlar",
}


@router.message(F.text.in_(LEGACY_SECTION_BUTTONS))
async def section_removed(message: Message):
    await message.answer(
        SECTION_REMOVED_TEXT,
        reply_markup=main_menu_for(message.from_user.id),
    )


@router.callback_query(
    F.data.startswith("hw:")
    | F.data.startswith("hwa:")
    | F.data.startswith("info_")
)
async def section_removed_callback(callback: CallbackQuery):
    await callback.answer(
        SECTION_REMOVED_TEXT,
        show_alert=True,
    )
