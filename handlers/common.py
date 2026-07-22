# =========================================================
# COMMON HANDLERS
# =========================================================

from aiogram import F
from aiogram.types import Message

from keyboards import *
from services.runtime import artikel_users


# =========================================================
# BACK TO MAIN MENU
# =========================================================

@dp.message(F.text == "⬅️ Orqaga")
async def go_back(message: Message):
    artikel_users.pop(message.from_user.id, None)

    await message.answer(
        "🏠 Asosiy Menu",
        reply_markup=main_menu
    )


# =========================================================
# BACK TO WORD GAME
# =========================================================

@dp.message(F.text == "⬅️ Darajalar")
async def back_to_levels(message: Message):

    await message.answer(
        "🎮 So'z O'yini",
        reply_markup=await build_level_menu(
            message.from_user.id
        )
    )