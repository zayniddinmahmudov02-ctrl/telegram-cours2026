# =========================================================
# BROADCAST SERVICE
# =========================================================
# Sends one already-composed message (via copy_message) to every
# active user, sequentially, with flood-safe pacing. A single
# failed/blocked/deleted user never stops the run - each send is
# isolated in its own try/except and the loop always continues.

import asyncio
import time
from typing import Awaitable, Callable, Optional

from aiogram import Bot
from aiogram.exceptions import (
    TelegramForbiddenError,
    TelegramNotFound,
    TelegramRetryAfter,
)

from database.users import (
    block_user,
    get_all_users,
    mark_user_deleted,
)
from services.logger import logger

# =========================================================
# FLOOD CONTROL
# =========================================================

CHUNK_SIZE = 100
CHUNK_PAUSE_SECONDS = 3
PER_MESSAGE_DELAY_SECONDS = 0.05
PROGRESS_UPDATE_EVERY = 20

ProgressCallback = Callable[[int, int], Awaitable[None]]


# =========================================================
# RUN BROADCAST
# =========================================================

async def run_broadcast(
    bot: Bot,
    from_chat_id: int,
    message_id: int,
    progress_callback: Optional[ProgressCallback] = None,
):
    users = get_all_users()
    total = len(users)

    stats = {
        "total": total,
        "success": 0,
        "blocked": 0,
        "deleted": 0,
        "failed": 0,
    }

    started_at = time.monotonic()

    for index, user in enumerate(users, start=1):

        user_id = user["user_id"]

        while True:
            try:
                await bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=from_chat_id,
                    message_id=message_id,
                )

                stats["success"] += 1
                break

            except TelegramRetryAfter as e:
                # Telegram itself is asking us to slow down - obey
                # it and retry the same user instead of skipping.
                await asyncio.sleep(e.retry_after + 0.5)
                continue

            except TelegramForbiddenError as e:
                if "deactivated" in str(e).lower():
                    mark_user_deleted(user_id)
                    stats["deleted"] += 1
                else:
                    block_user(user_id)
                    stats["blocked"] += 1
                break

            except TelegramNotFound:
                mark_user_deleted(user_id)
                stats["deleted"] += 1
                break

            except Exception as e:
                stats["failed"] += 1
                logger.warning(
                    f"Broadcast: failed to send to {user_id}: {e}"
                )
                break

        if progress_callback and (
            index % PROGRESS_UPDATE_EVERY == 0 or index == total
        ):
            await progress_callback(index, total)

        if index != total:
            if index % CHUNK_SIZE == 0:
                await asyncio.sleep(CHUNK_PAUSE_SECONDS)
            else:
                await asyncio.sleep(PER_MESSAGE_DELAY_SECONDS)

    stats["elapsed_seconds"] = time.monotonic() - started_at

    return stats


# =========================================================
# FORMATTING HELPERS
# =========================================================

def format_elapsed(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)

    if minutes:
        return f"{minutes}m {secs}s"

    return f"{secs}s"
