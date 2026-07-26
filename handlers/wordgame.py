import re

from aiogram import F, Router
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from config import LEVEL_CONFIG, LEVEL_ORDER
from database import db_execute
from keyboards import main_menu
from services.quiz import start_quiz_block

router = Router()

# =========================================================
# CONSTANTS
# =========================================================

LEVEL_BUTTONS = {
    f"🎯 {level}": level
    for level in LEVEL_ORDER
}

BLOCK_PATTERN = re.compile(
    r"^(?:🏆|✅|📖|🔒)\s*([A-Z0-9]+)-(\d+)-Blok"
)

# =========================================================
# DATABASE HELPERS
# =========================================================

def get_user(user_id: int):

    return db_execute(
        """
        SELECT
            full_name,
            unlocked_level
        FROM users
        WHERE user_id=%s
        """,
        (user_id,),
        fetchone=True,
    )


def get_progress(
    user_id: int,
    level: str,
    block: int,
):

    return db_execute(
        """
        SELECT best_score
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

# =========================================================
# LEVEL MENU
# =========================================================

async def build_level_menu(
    user_id: int,
) -> ReplyKeyboardMarkup:

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

    rows.extend(
        [
            [
                KeyboardButton(
                    text="🏆 Reytinglar",
                )
            ],
            [
                KeyboardButton(
                    text="🏅 W-Zertifikat",
                )
            ],
            [
                KeyboardButton(
                    text="⬅️ Orqaga",
                )
            ],
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
    )
# =========================================================
# BLOCK HELPERS
# =========================================================

def previous_block_completed(
    user_id: int,
    level: str,
    block: int,
) -> bool:

    if block == 1:
        return True

    progress = get_progress(
        user_id,
        level,
        block - 1,
    )

    return bool(
        progress and (progress["best_score"] or 0) >= 60
    )


def get_best_score(
    user_id: int,
    level: str,
    block: int,
) -> int:

    progress = get_progress(
        user_id,
        level,
        block,
    )

    if not progress:
        return 0

    return progress["best_score"] or 0


def can_open_block(
    user_id: int,
    level: str,
    block: int,
) -> bool:

    return previous_block_completed(
        user_id,
        level,
        block,
    )


# =========================================================
# BLOCK STATUS
# =========================================================

def get_block_title(
    user_id: int,
    level: str,
    block: int,
) -> str:

    block_size = LEVEL_CONFIG[level]["size"]

    score = get_best_score(
        user_id,
        level,
        block,
    )

    if score > 0:

        percent = round(
            score / block_size * 100
        )

        if percent >= 100:

            return (
                f"🏆 {level}-{block}-Blok (100%)"
            )

        return (
            f"✅ {level}-{block}-Blok ({percent}%)"
        )

    if can_open_block(
        user_id,
        level,
        block,
    ):

        return (
            f"📖 {level}-{block}-Blok"
        )

    return (
        f"🔒 {level}-{block}-Blok"
    )

# =========================================================
# LEVEL COMPLETE
# =========================================================

def level_completed(
    user_id: int,
    level: str,
) -> bool:

    config = LEVEL_CONFIG[level]

    for block in range(
        1,
        config["blocks"] + 1,
    ):

        score = get_best_score(
            user_id,
            level,
            block,
        )

        if score < config["size"]:
            return False

    return True

# =========================================================
# BLOCK KEYBOARD
# =========================================================

def build_block_keyboard(
    level: str,
    user_id: int,
) -> ReplyKeyboardMarkup:

    config = LEVEL_CONFIG.get(level)

    if not config:

        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text="⬅️ Darajalar",
                    )
                ]
            ],
            resize_keyboard=True,
        )

    rows = []

    current = []

    for block in range(
        1,
        config["blocks"] + 1,
    ):

        current.append(
            KeyboardButton(
                text=get_block_title(
                    user_id,
                    level,
                    block,
                )
            )
        )

        if len(current) == 2:

            rows.append(current)
            current = []

    if current:
        rows.append(current)

    rows.extend(
        [
            [
                KeyboardButton(
                    text="🏆 Reytinglar",
                )
            ],
            [
                KeyboardButton(
                    text="🏅 W-Zertifikat",
                )
            ],
            [
                KeyboardButton(
                    text="⬅️ Darajalar",
                )
            ],
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
    )

# =========================================================
# CERTIFICATE MENU
# =========================================================

def build_certificate_menu() -> ReplyKeyboardMarkup:

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🏅 A1 W-Zertifikat"),
                KeyboardButton(text="🏅 A2 W-Zertifikat"),
            ],
            [
                KeyboardButton(text="🏅 B1 W-Zertifikat"),
                KeyboardButton(text="🏅 B2 W-Zertifikat"),
            ],
            [
                KeyboardButton(text="🏅 C1 W-Zertifikat"),
            ],
            [
                KeyboardButton(text="⬅️ Darajalar"),
            ],
        ],
        resize_keyboard=True,
    )
# =========================================================
# LOCK MESSAGE
# =========================================================

async def send_locked_message(
    message: Message,
):

    await message.answer(
        "🔒 Bu blok hali ochilmagan.\n\n"
        "Avval oldingi blokni muvaffaqiyatli yakunlang."
    )
# =========================================================
# WORD GAME MENU
# =========================================================

WORD_GAME_TEXT = (
    "🎮 <b>WortSpiel</b>\n\n"
    "Kerakli darajani tanlang."
)


@router.message(F.text.in_(["🎮 So'z Oyini", "🎮 So'z O'yini"]))
async def word_game_handler(message: Message):

    if not get_user(message.from_user.id):

        await message.answer(
            "❌ Avval ro'yxatdan o'ting."
        )

        return

    await message.answer(
        WORD_GAME_TEXT,
        parse_mode="HTML",
        reply_markup=await build_level_menu(
            message.from_user.id,
        ),
    )


# =========================================================
# LEVEL SELECT
# =========================================================

@router.message(F.text.in_(LEVEL_BUTTONS))
async def level_selected(message: Message):

    level = LEVEL_BUTTONS[
        message.text
    ]

    await message.answer(
        f"📚 <b>{level}</b>\n\n"
        "Bloklardan birini tanlang.",
        parse_mode="HTML",
        reply_markup=build_block_keyboard(
            level,
            message.from_user.id,
        ),
    )
CERTIFICATE_BUTTONS = {
    "🏅 A1 W-Zertifikat": "A1",
    "🏅 A2 W-Zertifikat": "A2",
    "🏅 B1 W-Zertifikat": "B1",
    "🏅 B2 W-Zertifikat": "B2",
    "🏅 C1 W-Zertifikat": "C1",
}

# =========================================================
# BACK TO LEVELS
# =========================================================

@router.message(F.text == "⬅️ Darajalar")
async def back_to_levels(message: Message):

    await message.answer(
        WORD_GAME_TEXT,
        parse_mode="HTML",
        reply_markup=await build_level_menu(
            message.from_user.id,
        ),
    )

# =========================================================
# CERTIFICATE MENU
# =========================================================

@router.message(F.text == "🏅 W-Zertifikat")
async def certificate_menu(
    message: Message,
):

    await message.answer(
        "🏅 <b>W-Zertifikat</b>\n\n"
        "Qaysi daraja sertifikatini olishni xohlaysiz?",
        parse_mode="HTML",
        reply_markup=build_certificate_menu(),
    )
# =========================================================
# CERTIFICATE SELECT
# =========================================================

@router.message(
    F.text.in_(CERTIFICATE_BUTTONS)
)
async def certificate_selected(
    message: Message,
):

    level = CERTIFICATE_BUTTONS[
        message.text
    ]

    if not level_completed(
        message.from_user.id,
        level,
    ):

        await message.answer(
            f"❌ {level} darajasi hali yakunlanmagan.\n\n"
            "Barcha bloklarni 100% tugatganingizdan so'ng "
            "W-Zertifikat ochiladi."
        )

        return

    await message.answer(
        f"🏅 {level} W-Zertifikat tayyor.\n\n"
        "Keyingi bosqichda sertifikat oynasi ochiladi."
    )

# =========================================================
# BLOCK SELECT
# =========================================================

@router.message(
    F.text.regexp(r"^(🏆|✅|📖|🔒)\s*[A-Z0-9]+-\d+-Blok")
)
async def open_block(message: Message):

    match = BLOCK_PATTERN.match(message.text)

    if match is None:

        await message.answer(
            "❌ Blok aniqlanmadi."
        )

        return

    level = match.group(1)
    block = int(match.group(2))

    if not can_open_block(
        message.from_user.id,
        level,
        block,
    ):

        await send_locked_message(
            message,
        )

        return

    await start_quiz_block(
        message=message,
        level=level,
        block=block,
    )
# =========================================================
# BACK TO MAIN MENU
# =========================================================

@router.message(F.text == "⬅️ Orqaga")
async def back_main_menu(message: Message):

    await message.answer(
        "🏠 Asosiy menyu",
        reply_markup=main_menu,
    )
