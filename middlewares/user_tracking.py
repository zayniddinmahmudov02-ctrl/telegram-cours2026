# =========================================================
# GLOBAL USER TRACKING MIDDLEWARE
# =========================================================
# Registered as an outer middleware on the dispatcher's Update
# observer (see bot.py), so it runs before ANY inner middleware
# or handler, for EVERY update type - not just /start. This is
# what guarantees a user is registered/updated on their very
# first interaction, whatever form it takes.

from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, User

from database.users import upsert_user

# =========================================================
# USER EXTRACTION
# =========================================================
# Every one of these Update fields carries a `from_user` when
# populated - covers messages, edited messages, callback
# queries, inline queries, chosen inline results, shipping /
# pre-checkout queries, poll answers, chat member updates
# (including my_chat_member/block-unblock) and join requests.

_USER_EVENT_FIELDS = (
    "message",
    "edited_message",
    "callback_query",
    "inline_query",
    "chosen_inline_result",
    "shipping_query",
    "pre_checkout_query",
    "poll_answer",
    "my_chat_member",
    "chat_member",
    "chat_join_request",
)


def extract_telegram_user(update: Update) -> Optional[User]:
    for field in _USER_EVENT_FIELDS:
        event = getattr(update, field, None)

        if event is None:
            continue

        user = getattr(event, "from_user", None)

        if user is not None:
            return user

    return None


# =========================================================
# MIDDLEWARE
# =========================================================

class UserTrackingMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ):

        user = extract_telegram_user(event)

        if user is not None and not user.is_bot:
            upsert_user(
                user_id=user.id,
                full_name=user.full_name,
                first_name=user.first_name,
                last_name=user.last_name,
                username=user.username,
                language_code=user.language_code,
                is_premium=bool(user.is_premium),
            )

        return await handler(event, data)
