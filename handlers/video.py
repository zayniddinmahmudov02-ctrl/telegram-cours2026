from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
)

from keyboards.main import main_menu_for

router = Router()


# =========================================================
# VIDEO COURSE SALES - DISCONTINUED
# =========================================================
# Video course sales were removed from the bot. Users can still
# have the old "🎥 Video Kurslar" reply keyboard (or the course
# menu under it) cached on their device, and old payment messages
# in their chat still carry the inline buttons - so every one of
# those entry points is caught here and answered with a short
# notice instead of being silently ignored. Nothing here creates
# an order or touches the payments table.

SALES_CLOSED_TEXT = "ℹ️ Video kurslar sotuvi hozircha to'xtatilgan."

LEGACY_VIDEO_BUTTONS = {
    "🎥 Video Kurslar",
    "🎬 Bepul Namuna Darslar",
    "🇩🇪 A1 — 50% CHEGIRMA",
    "🇩🇪 A2 — 50% CHEGIRMA",
    "🇩🇪 B1 — 50% CHEGIRMA",
    "🇩🇪 B2 — TEZ ORADA",
    "🇩🇪 C1 — TEZ ORADA",
    "🔥 A1-B1 — 50% CHEGIRMA",
    "🔥 B2-C1 — TEZ ORADA",
    "🔥 A1-C1 — 50% CHEGIRMA",
}


@router.message(F.text.in_(LEGACY_VIDEO_BUTTONS))
async def video_sales_closed(message: Message):
    await message.answer(
        SALES_CLOSED_TEXT,
        reply_markup=main_menu_for(message.from_user.id),
    )


@router.callback_query(
    F.data.startswith("payment:")
    | F.data.startswith("payment_receipt:")
    | (F.data == "payment_cancel")
)
async def video_sales_closed_callback(callback: CallbackQuery):
    await callback.answer(
        SALES_CLOSED_TEXT,
        show_alert=True,
    )
