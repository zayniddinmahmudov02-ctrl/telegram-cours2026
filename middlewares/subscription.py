from typing import Any, Callable, Dict

from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from aiogram import BaseMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import ADMIN_ID, CHANNEL_USERNAME


async def check_subscription(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(
            CHANNEL_USERNAME,
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

        if event.from_user.id == ADMIN_ID:
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

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📢 Kanalga A'zo Bo'lish",
                            url="https://t.me/vizu_deutsch"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="✅ Tekshirish",
                            callback_data="check_sub"
                        )
                    ]
                ]
            )

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