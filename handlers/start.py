from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from database import db_execute
from keyboards import main_menu

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):
    user = message.from_user

    db_execute(
        """
        INSERT INTO users (user_id, full_name)
        VALUES (%s, %s)
        ON CONFLICT (user_id)
        DO NOTHING
        """,
        (
            user.id,
            user.full_name,
        ),
    )

    await message.answer(
        f"Assalomu alaykum, {user.full_name}! 🇩🇪\n\n"
        "VIZU Academy botiga xush kelibsiz.",
        reply_markup=main_menu,
    )