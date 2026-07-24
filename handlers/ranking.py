from aiogram import Router, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from database import db_execute

router = Router()

# =========================================================
# GLOBAL MENU
# =========================================================

rating_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🏆 Umumiy Reyting"),
            KeyboardButton(text="⚡ Kunlik Reyting"),
        ],
        [
            KeyboardButton(text="⬅️ Darajalar")
        ]
    ],
    resize_keyboard=True
)

# =========================================================
# OPEN RANKING MENU
# =========================================================

@router.message(F.text == "🏆 Reytinglar")
async def open_rating_menu(message: Message):

    await message.answer(
        "🏆 Reyting bo'limi",
        reply_markup=rating_menu
    )

# =========================================================
# RANKING TEXT
# =========================================================

async def _get_ranking_text(
    query_type: str,
    message: Message
):

    col = (
        "total_score"
        if query_type == "total"
        else "daily_score"
    )

    title = (
        "🏆 TOP 100 UMUMIY REYTING"
        if query_type == "total"
        else "⚡ TOP 100 KUNLIK REYTING"
    )

    rankings = db_execute(
        f"""
        SELECT
            COALESCE(full_name, 'Unknown') AS full_name,
            {col}
        FROM users
        WHERE {col} > 0
        ORDER BY {col} DESC
        LIMIT 100
        """,
        fetchall=True
    )

    if not rankings:
        return (
            f"📭 {title} hali bo'sh.\n\n"
            "🎮 Birinchi bo'lib test ishlang!"
        )

    text = f"{title}\n\n"

    medals = {
        1: "🥇",
        2: "🥈",
        3: "🥉",
    }

    for i, row in enumerate(rankings, start=1):

        name = row["full_name"]
        score = row[col]

        medal = medals.get(i, f"{i}.")

        text += (
            f"{medal} "
            f"{name} "
            f"— "
            f"{score} XP\n"
        )

    my_score_row = db_execute(
        f"""
        SELECT {col}
        FROM users
        WHERE user_id = %s
        """,
        (message.from_user.id,),
        fetchone=True
    )

    my_score = (
        my_score_row[col]
        if my_score_row
        else 0
    )

    my_rank = db_execute(
        f"""
        SELECT
            COUNT(*) + 1 AS position
        FROM users
        WHERE {col} > %s
        """,
        (my_score,),
        fetchone=True
    )

    my_position = (
        my_rank["position"]
        if my_rank
        else "-"
    )

    text += "\n━━━━━━━━━━━━━━\n"

    if my_score > 0:

        text += (
            f"👤 Sizning o'rningiz: #{my_position}\n"
            f"⭐ Ballingiz: {my_score} XP"
        )

    else:

        text += "🎮 Siz hali test ishlamagansiz."

    return text
# =========================================================
# TOTAL RANKING
# =========================================================

@router.message(F.text == "🏆 Umumiy Reyting")
async def total_ranking(
    message: Message
):

    text = await _get_ranking_text(
        query_type="total",
        message=message,
    )

    await message.answer(
        text,
        reply_markup=rating_menu,
    )


# =========================================================
# DAILY RANKING
# =========================================================

@router.message(F.text == "⚡ Kunlik Reyting")
async def daily_ranking(
    message: Message
):

    text = await _get_ranking_text(
        query_type="daily",
        message=message,
    )

    await message.answer(
        text,
        reply_markup=rating_menu,
    )


# =========================================================
# BACK TO LEVELS
# =========================================================

@router.message(F.text == "⬅️ Darajalar")
async def back_to_levels(
    message: Message
):
    from handlers.wordgame import build_level_menu

    menu = await build_level_menu(
        message.from_user.id
    )

    await message.answer(
        "🎯 Darajani tanlang.",
        reply_markup=menu,
    )