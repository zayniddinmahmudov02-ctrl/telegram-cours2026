import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from database import db_execute
from config import LEVEL_ORDER, LEVEL_CONFIG
from states.register import RegisterStates
from services.quiz import start_quiz_block
from keyboards import main_menu

router = Router()


# =========================================================
# CONSTANTS
# =========================================================

LEVEL_BUTTONS = {
    "🎯 A1": "A1",
    "🎯 A2": "A2",
    "🎯 B1": "B1",
    "🎯 B2": "B2",
    "🎯 C1": "C1",
}


# =========================================================
# HELPER
# =========================================================

def get_user(user_id: int):

    return db_execute(
        """
        SELECT
            full_name,
            unlocked_level,
            total_score,
            daily_score
        FROM users
        WHERE user_id=%s
        """,
        (user_id,),
        fetchone=True,
    )


def get_progress(user_id: int, level: str, block: int):

    return db_execute(
        """
        SELECT
            best_score
        FROM quiz_progress
        WHERE user_id=%s
        AND level=%s
        AND block_number=%s
        """,
        (
            user_id,
            level,
            block,
        ),
        fetchone=True,
    )


def previous_block_completed(
    user_id: int,
    level: str,
    block: int,
) -> bool:

    if block == 1:
        return True

    row = get_progress(
        user_id,
        level,
        block - 1,
    )

    if not row:
        return False

    score = row["best_score"] or 0

    return score >= 60


# =========================================================
# LEVEL MENU
# =========================================================

async def build_level_menu(user_id: int):

    rows = []

    current = []

    for level in LEVEL_ORDER:

        current.append(
            KeyboardButton(
                text=f"🎯 {level}"
            )
        )

        if len(current) == 2:
            rows.append(current)
            current = []

    if current:
        rows.append(current)

    rows.append(
        [
            KeyboardButton(
                text="🏆 Reytinglar"
            )
        ]
    )

    rows.append(
        [
            KeyboardButton(
                text="🏅 W-Zertifikat"
            )
        ]
    )

    rows.append(
        [
            KeyboardButton(
                text="⬅️ Orqaga"
            )
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
    )


# =========================================================
# BLOCK STATUS
# =========================================================

def get_block_title(
    user_id: int,
    level: str,
    block: int,
):

    config = LEVEL_CONFIG[level]

    progress = get_progress(
        user_id,
        level,
        block,
    )

    if progress:

        score = progress["best_score"] or 0

        percent = round(
            score / config["size"] * 100
        )

        if percent >= 100:

            return (
                f"🏆 "
                f"{level}-{block}-Blok "
                f"(100%)"
            )

        return (
            f"✅ "
            f"{level}-{block}-Blok "
            f"({percent}%)"
        )

    if previous_block_completed(
        user_id,
        level,
        block,
    ):

        return (
            f"📖 "
            f"{level}-{block}-Blok"
        )

    return (
        f"🔒 "
        f"{level}-{block}-Blok"
    )
# =========================================================
# BLOCK KEYBOARD
# =========================================================

def build_block_keyboard(
    level: str,
    user_id: int,
):

    config = LEVEL_CONFIG.get(level)

    if not config:

        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text="⬅️ Darajalar"
                    )
                ]
            ],
            resize_keyboard=True,
        )

    rows = []

    current = []

    total_blocks = config["blocks"]

    for block in range(1, total_blocks + 1):

        text = get_block_title(
            user_id=user_id,
            level=level,
            block=block,
        )

        current.append(
            KeyboardButton(
                text=text,
            )
        )

        if len(current) == 2:
            rows.append(current)
            current = []

    if current:
        rows.append(current)

    rows.append(
        [
            KeyboardButton(
                text="🏆 Reytinglar"
            )
        ]
    )

    rows.append(
        [
            KeyboardButton(
                text="🏅 W-Zertifikat"
            )
        ]
    )

    rows.append(
        [
            KeyboardButton(
                text="⬅️ Darajalar"
            )
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
    )


# =========================================================
# BLOCK ACCESS
# =========================================================

def can_open_block(
    user_id: int,
    level: str,
    block: int,
) -> bool:

    if block == 1:
        return True

    previous = get_progress(
        user_id=user_id,
        level=level,
        block=block - 1,
    )

    if not previous:
        return False

    score = previous["best_score"] or 0

    return score >= 60


# =========================================================
# BLOCK RESULT
# =========================================================

def get_best_score(
    user_id: int,
    level: str,
    block: int,
):

    row = get_progress(
        user_id=user_id,
        level=level,
        block=block,
    )

    if not row:
        return 0

    return row["best_score"] or 0


# =========================================================
# BLOCK COMPLETE
# =========================================================

def is_completed(
    user_id: int,
    level: str,
    block: int,
):

    score = get_best_score(
        user_id=user_id,
        level=level,
        block=block,
    )

    block_size = LEVEL_CONFIG[level]["size"]

    if block_size == 0:
        return False

    percent = round(
        score / block_size * 100
    )

    return percent >= 100


# =========================================================
# LOCK MESSAGE
# =========================================================

async def send_locked_message(
    message: Message,
):

    await message.answer(
        """
🔒 Bu blok hali ochilmagan.

Avval oldingi blokni muvaffaqiyatli yakunlang.

Keyin keyingi blok avtomatik ochiladi.
"""
    )
