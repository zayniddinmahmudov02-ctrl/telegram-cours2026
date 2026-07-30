from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message, User

from database import db_execute
from keyboards import main_menu_for
from keyboards.subscription import subscription_keyboard
from middlewares.subscription import check_subscription

router = Router()


def register_user(user: User):
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


async def send_welcome(message: Message, user: User):
    register_user(user)

    await message.answer(
        f"Assalomu alaykum, {user.full_name}! 🇩🇪\n\n"
        "VIZU Academy botiga xush kelibsiz.",
        reply_markup=main_menu_for(user.id),
    )


@router.message(CommandStart())
async def start_handler(message: Message, bot: Bot):
    user = message.from_user

    if not await check_subscription(bot, user.id):
        await message.answer(
            "📢 Botdan foydalanish uchun avval quyidagi "
            "kanalga a'zo bo'ling:\n"
            "https://t.me/vizu_deutsch",
            reply_markup=subscription_keyboard(),
        )
        return

    await send_welcome(message, user)


@router.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery, bot: Bot):
    user = callback.from_user

    if not await check_subscription(bot, user.id):
        await callback.answer(
            "❌ Siz hali kanalga qo'shilmagansiz.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        "✅ A'zolik tasdiqlandi!",
        reply_markup=None,
    )

    await send_welcome(callback.message, user)

    await callback.answer()