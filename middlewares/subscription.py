from typing import Any, Callable, Dict

from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from aiogram import BaseMiddleware

from config import CHANNEL_USERNAME, CHANNEL_ID
from services.auth import is_admin
from keyboards.subscription import subscription_keyboard


async def check_subscription(bot: Bot, user_id: int) -> bool:
    chat_id = CHANNEL_ID or CHANNEL_USERNAME

    try:
        member = await bot.get_chat_member(
            chat_id,
            user_id
        )

        return member.status not in (
            "left",
            "kicked"
        )

    except Exception:
        return False


class SubscriptionMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable,
        event,
        data: Dict[str, Any]
    ):

        bot: Bot = data["bot"]

        if not getattr(event, "from_user", None):
            return await handler(event, data)

        if is_admin(event.from_user.id):
            return await handler(event, data)

        if isinstance(event, Message):

            if event.text and event.text.startswith("/start"):
                return await handler(event, data)

        if isinstance(event, CallbackQuery):

            if event.data == "check_sub":
                return await handler(event, data)

        subscribed = await check_subscription(
            bot,
            event.from_user.id
        )

        if not subscribed:

            keyboard = subscription_keyboard()

            text = (
                "❌ Botdan foydalanish uchun "
                "avval kanalga a'zo bo'ling."
            )

            if isinstance(event, Message):
                await event.answer(
                    text,
                    reply_markup=keyboard
                )

            elif isinstance(event, CallbackQuery):
                await event.message.answer(
                    text,
                    reply_markup=keyboard
                )
                await event.answer()

            return

        return await handler(event, data)