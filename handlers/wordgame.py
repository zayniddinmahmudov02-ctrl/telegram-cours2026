import re

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from database import db_execute
from states.register import RegisterStates

from config import (
    LEVEL_ORDER,
    LEVEL_CONFIG,
)

from services.quiz import start_quiz_block

router = Router()

async def build_level_menu(user_id):
    result = db_execute(
        """
        SELECT unlocked_level
        FROM users
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    unlocked = result[0] if result and result[0] else "A1"

    if unlocked in LEVEL_ORDER:
        unlocked_index = LEVEL_ORDER.index(unlocked)
    else:
        unlocked_index = 0

    rows = []
    current = []

    for level in LEVEL_ORDER:
        current.append(
            KeyboardButton(text=f"🎯 {level}")
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
        resize_keyboard=True
    )

def build_block_keyboard(level, user_id):

    config = LEVEL_CONFIG.get(level)

    if not config:

        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text="⬅️ Orqaga"
                    )
                ]
            ],
            resize_keyboard=True
        )

    rows = []
    current = []

    for i in range(
        1,
        config["blocks"] + 1
    ):

        progress = db_execute(
            """
            SELECT best_score
            FROM quiz_progress
            WHERE user_id = %s
            AND level = %s
            AND block_number = %s
            """,
            (
                user_id,
                level,
                i
            ),
            fetchone=True
        )

        if progress:

            score = progress[0] or 0

            block_size = config["size"]

            percent = round(
                (score / block_size) * 100
            ) if block_size > 0 else 0

            if percent >= 100:

                text = (
                    f"🏆 "
                    f"{level}-{i}-Blok "
                    f"(100%)"
                )

            else:

                text = (
                    f"✅ "
                    f"{level}-{i}-Blok "
                    f"({percent}%)"
                )

        else:

            text = (
                f"📚 "
                f"{level}-{i}-Blok"
            )

        current.append(
            KeyboardButton(text=text)
        )

        if len(current) == 2:
            rows.append(current)
            current = []

    if current:
        rows.append(current)

    rows.append(
        [
            KeyboardButton(
                text="⬅️ Darajalar"
            )
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True
    )
@router.message(F.text == "🎮 So'z O'yini")
async def word_game_handler(
    message: Message,
    state: FSMContext
):
    user_id = message.from_user.id

    await state.clear()

    result = db_execute(
        """
        SELECT full_name
        FROM users
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    full_name = result[0] if result else None

    if not full_name or full_name in {"Unknown", ""}:

        await message.answer(
            "📝 To'liq ism familiyangizni kiriting.\n\n"
            "Masalan:\n"
            "Zayniddinkhuja Makhmudov"
        )

        await state.set_state(
            RegisterStates.waiting_full_name
        )

        return

    menu = await build_level_menu(user_id)

    await message.answer(
        "🎮 WortSpiel\n\n"
        "Darajani tanlang:",
        reply_markup=menu
    )
# =========================================================
# SAVE FULL NAME
# =========================================================

@router.message(RegisterStates.waiting_full_name)
async def save_full_name(
    message: Message,
    state: FSMContext
):
    user_id = message.from_user.id
    full_name = message.text.strip()

    # =====================================================
    # VALIDATION
    # =====================================================

    if len(full_name) < 5:
        await message.answer(
            "❌ Juda qisqa ism. Kamida 5 ta harf bo'lishi kerak."
        )
        return

    if len(full_name) > 50:
        await message.answer(
            "❌ Juda uzun ism. Maksimal 50 ta harf bo'lishi mumkin."
        )
        return

    if len(full_name.split()) < 2:
        await message.answer(
            "❌ Ism va familiyani to'liq kiriting.\n\n"
            "Masalan:\n"
            "Zayniddinkhuja Makhmudov"
        )
        return

    # =====================================================
    # SAVE DATABASE
    # =====================================================

    db_execute(
        """
        UPDATE users
        SET full_name = %s
        WHERE user_id = %s
        """,
        (
            full_name,
            user_id
        )
    )

    await state.clear()

    await message.answer(
        f"✅ Saqlandi:\n{full_name}"
    )

    menu = await build_level_menu(user_id)

    await message.answer(
        "🎮 WortSpiel\n\n"
        "Darajani tanlang:",
        reply_markup=menu
    )


# =========================================================
# OPEN LEVEL
# =========================================================

@router.message(
    F.text.regexp(
        r"🎯 (A1|A2|B1|B2|C1)"
    )
)
async def open_level_handler(
    message: Message
):

    level = (
        message.text
        .replace("🎯 ", "")
        .strip()
    )

    await message.answer(
        f"📚 {level} bloklari",
        reply_markup=build_block_keyboard(
            level,
            message.from_user.id
        )
    )


# =========================================================
# START BLOCK
# =========================================================

@router.message(
    F.text.regexp(
        r"(📚|✅|🏆)\s?(A1|A2|B1|B2|C1)-(\d+)-Blok"
    )
)
async def start_block(
    message: Message
):

    match = re.search(
        r"(A1|A2|B1|B2|C1)-(\d+)-Blok",
        message.text
    )

    if not match:
        return

    level = match.group(1)
    block = int(match.group(2))
    user_id = message.from_user.id

    # =====================================================
    # FIRST BLOCK
    # =====================================================

    if block == 1:

        await start_quiz_block(
            message,
            level,
            block
        )

        return

    # =====================================================
    # USER
    # =====================================================

    user_data = db_execute(
        """
        SELECT unlocked_level
        FROM users
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True
    )

    current_unlocked = (
        user_data[0]
        if user_data
        else "A1"
    )

    # =====================================================
    # OLD RESULT
    # =====================================================

    row = db_execute(
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
            block
        ),
        fetchone=True
    )

    if row:

        best_score = row[0] or 0

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Ha, qayta ishlash",
                        callback_data=f"restartquiz:{level}:{block}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Yo'q",
                        callback_data="cancelquiz"
                    )
                ]
            ]
        )

        await message.answer(
            f"📊 Oxirgi natijangiz\n\n"
            f"🇩🇪 Daraja: {level}\n"
            f"📚 Blok: {block}\n\n"
            f"🏆 Eng yaxshi natija: {best_score}%\n\n"
            f"Qayta ishlamoqchimisiz?",
            reply_markup=keyboard
        )

        return

    # =====================================================
    # START
    # =====================================================

    await start_quiz_block(
        message,
        level,
        block
    )