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
# =========================================================
# WORD GAME MENU
# =========================================================

@router.message(F.text == "🎮 So'z Oyini")
@router.message(F.text == "🎮 So'z O'yini")
async def word_game_handler(
    message: Message,
):

    user = get_user(message.from_user.id)

    if not user:

        await message.answer(
            "❌ Avval ro'yxatdan o'ting."
        )

        return

    menu = await build_level_menu(
        message.from_user.id
    )

    await message.answer(
        (
            "🎮 <b>WortSpiel</b>\n\n"
            "Kerakli darajani tanlang."
        ),
        parse_mode="HTML",
        reply_markup=menu,
    )


# =========================================================
# LEVEL SELECT
# =========================================================

@router.message(
    F.text.in_(LEVEL_BUTTONS.keys())
)
async def level_selected(
    message: Message,
):

    level = LEVEL_BUTTONS[
        message.text
    ]

    keyboard = build_block_keyboard(
        level=level,
        user_id=message.from_user.id,
    )

    await message.answer(
        (
            f"📚 <b>{level}</b>\n\n"
            "Bloklardan birini tanlang."
        ),
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# =========================================================
# BACK TO LEVELS
# =========================================================

@router.message(
    F.text == "⬅️ Darajalar"
)
async def back_to_levels(
    message: Message,
):

    menu = await build_level_menu(
        message.from_user.id
    )

    await message.answer(
        "🎯 Darajani tanlang.",
        reply_markup=menu,
    )


# =========================================================
# BLOCK SELECT
# =========================================================

BLOCK_PATTERN = re.compile(
    r"^(?:🏆|✅|📖|🔒)\s*([A-Z0-9]+)-(\d+)-Blok"
)


@router.message()
async def open_block(
    message: Message,
):

    match = BLOCK_PATTERN.match(
        message.text
    )

    if not match:
        return

    level = match.group(1)
    block = int(
        match.group(2)
    )

    if not can_open_block(
        message.from_user.id,
        level,
        block,
    ):

        await send_locked_message(
            message
        )

        return

    await start_quiz_block(
        message=message,
        level=level,
        block=block,
    )


# =========================================================
# CHANGE FULL NAME
# =========================================================

@router.message(
    F.text == "✏️ Ism va familiyani o'zgartirish"
)
async def change_full_name(
    message: Message,
    state: FSMContext,
):

    await state.set_state(
        RegisterStates.waiting_full_name
    )

    await message.answer(
        "📝 Yangi ism va familiyangizni yuboring."
    )


# =========================================================
# SAVE FULL NAME
# =========================================================

@router.message(
    RegisterStates.waiting_full_name
)
async def save_full_name(
    message: Message,
    state: FSMContext,
):

    full_name = message.text.strip()

    db_execute(
        """
        UPDATE users
        SET full_name=%s
        WHERE user_id=%s
        """,
        (
            full_name,
            message.from_user.id,
        ),
    )

    await state.clear()

    await message.answer(
        "✅ Ism va familiya muvaffaqiyatli saqlandi.",
        reply_markup=main_menu,
    )

# =========================================================
# BACK TO MAIN MENU
# =========================================================

@router.message(F.text == "⬅️ Orqaga")
async def back_main_menu(
    message: Message,
):

    await message.answer(
        "🏠 Asosiy menyu",
        reply_markup=main_menu,
    )

# =========================================================
# UNKNOWN BLOCK MESSAGE
# =========================================================

@router.message(
    F.text.regexp(r"^(📖|✅|🏆|🔒)")
)
async def unknown_block(
    message: Message,
):

    await message.answer(
        "❌ Blok aniqlanmadi."
    )
