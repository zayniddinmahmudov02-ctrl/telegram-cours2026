from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from database.leaderboard import (
    get_daily_top,
    get_weekly_top,
    get_monthly_top,
    get_global_top,
    get_monthly_champions,
    get_user_rank,
)

router = Router()

# =========================================================
# KEYBOARDS
# =========================================================

rating_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📅 Kunlik"),
            KeyboardButton(text="📆 Haftalik"),
        ],
        [
            KeyboardButton(text="🗓 Oylik"),
            KeyboardButton(text="🌍 Global"),
        ],
        [
            KeyboardButton(text="👑 Champions"),
        ],
        [
            KeyboardButton(text="⬅️ Darajalar"),
        ],
    ],
    resize_keyboard=True,
)

# =========================================================
# MENU
# =========================================================

@router.message(F.text == "🏆 Reytinglar")
async def open_rating_menu(message: Message):

    await message.answer(
        "🏆 Reyting bo'limiga xush kelibsiz!\n\n"
        "Kerakli bo'limni tanlang.",
        reply_markup=rating_menu,
    )
# =========================================================
# HELPERS
# =========================================================

async def build_ranking_text(
    title: str,
    score_type: str,
    top: list,
    user_id: int,
):

    text = f"🏆 <b>{title}</b>\n\n"

    if not top:
        return (
            text +
            "📭 Hozircha reyting mavjud emas.\n\n"
            "🎮 Birinchi bo'lib Word Game o'ynang!"
        )

    medals = {
        1: "🥇",
        2: "🥈",
        3: "🥉",
    }

    for index, row in enumerate(top, start=1):

        medal = medals.get(index, f"{index}.")

        text += (
            f"{medal} "
            f"<b>{row['full_name']}</b>\n"
            f"⭐ {row[f'{score_type}_score']} ball\n\n"
        )

    rank = get_user_rank(
        user_id,
        score_type,
    )

    text += "━━━━━━━━━━━━━━\n\n"

    if rank:

        user = next(
            (
                x
                for x in top
                if x["user_id"] == user_id
            ),
            None,
        )

        score = (
            user[f"{score_type}_score"]
            if user
            else 0
        )

        text += (
            f"👤 <b>Siz</b>\n"
            f"🏅 O'rningiz: #{rank}\n"
            f"⭐ Ballingiz: {score}"
        )

    else:

        text += (
            "👤 Siz hali reytingda emassiz."
        )

    return text
