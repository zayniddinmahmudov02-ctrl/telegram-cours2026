from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from database.leaderboard import (
    get_daily_top,
    get_weekly_top,
    get_monthly_top,
    get_global_top,
    get_monthly_champions,
    get_user_rank,
)

from keyboards.inline.leaderboard import leaderboard_keyboard
from keyboards.inline.champions import champions_years_keyboard
from keyboards.inline.back import champions_back_keyboard

router = Router()

# =========================================================
# MENU
# =========================================================

LEADERBOARD_TEXT = (
    "🏆 <b>VIZU Leaderboard</b>\n\n"
    "Kerakli reyting turini tanlang."
)


@router.message(Command("leaderboard"))
async def leaderboard_command(message: Message):

    await message.answer(
        LEADERBOARD_TEXT,
        reply_markup=leaderboard_keyboard(),
    )


@router.message(F.text == "🏆 Reytinglar")
async def leaderboard_menu(message: Message):

    await message.answer(
        LEADERBOARD_TEXT,
        reply_markup=leaderboard_keyboard(),
    )


# =========================================================
# HELPER
# =========================================================

def build_leaderboard_text(
    *,
    title: str,
    score_field: str,
    period: str,
    top: list,
    user_id: int,
) -> str:

    text = f"{title}\n\n"

    if not top:
        return (
            text
            + "📭 Hozircha reyting mavjud emas.\n\n"
            + "🎮 Birinchi bo'lib Word Game o'ynang!"
        )

    medals = ["🥇", "🥈", "🥉"]

    for index, row in enumerate(top, start=1):

        place = medals[index - 1] if index <= 3 else f"{index}."

        text += (
            f"{place} "
            f"<b>{row['full_name']}</b>\n"
            f"⭐ {row[score_field]} ball\n\n"
        )

    rank = get_user_rank(
        user_id,
        period,
    )

    text += "━━━━━━━━━━━━━━\n\n"

    if rank:

        text += (
            f"👤 <b>Sizning o'rningiz:</b> #{rank}"
        )

    else:

        text += "👤 Siz hali reytingda emassiz."

    return text
# =========================================================
# DAILY
# =========================================================

@router.callback_query(F.data == "lb_daily")
async def daily_top(callback: CallbackQuery):

    text = build_leaderboard_text(
        title="📅 <b>Kunlik Reyting</b>",
        score_field="daily_score",
        period="daily",
        top=get_daily_top(),
        user_id=callback.from_user.id,
    )

    await callback.message.edit_text(
        text,
        reply_markup=leaderboard_keyboard(),
    )

    await callback.answer()


# =========================================================
# WEEKLY
# =========================================================

@router.callback_query(F.data == "lb_weekly")
async def weekly_top(callback: CallbackQuery):

    text = build_leaderboard_text(
        title="📆 <b>Haftalik Reyting</b>",
        score_field="weekly_score",
        period="weekly",
        top=get_weekly_top(),
        user_id=callback.from_user.id,
    )

    await callback.message.edit_text(
        text,
        reply_markup=leaderboard_keyboard(),
    )

    await callback.answer()
# =========================================================
# MONTHLY
# =========================================================

@router.callback_query(F.data == "lb_monthly")
async def monthly_top(callback: CallbackQuery):

    text = build_leaderboard_text(
        title="🗓 <b>Oylik Reyting</b>",
        score_field="monthly_score",
        period="monthly",
        top=get_monthly_top(),
        user_id=callback.from_user.id,
    )

    await callback.message.edit_text(
        text,
        reply_markup=leaderboard_keyboard(),
    )

    await callback.answer()


# =========================================================
# GLOBAL
# =========================================================

@router.callback_query(F.data == "lb_global")
async def global_top(callback: CallbackQuery):

    text = build_leaderboard_text(
        title="🌍 <b>Global Reyting</b>",
        score_field="global_score",
        period="global",
        top=get_global_top(),
        user_id=callback.from_user.id,
    )

    await callback.message.edit_text(
        text,
        reply_markup=leaderboard_keyboard(),
    )

    await callback.answer()
# =========================================================
# CHAMPIONS
# =========================================================

@router.callback_query(F.data == "lb_champions")
async def champions(callback: CallbackQuery):

    await callback.message.edit_text(
        "👑 <b>VIZU Champions</b>\n\n"
        "Ko'rmoqchi bo'lgan yilni tanlang.",
        reply_markup=champions_years_keyboard(),
    )

    await callback.answer()


# =========================================================
# CHAMPIONS YEAR
# =========================================================

@router.callback_query(F.data.startswith("champions_year_"))
async def champions_year(callback: CallbackQuery):

    year = int(callback.data.split("_")[-1])

    champions = get_monthly_champions(year)

    months = {
        1: "Yanvar",
        2: "Fevral",
        3: "Mart",
        4: "Aprel",
        5: "May",
        6: "Iyun",
        7: "Iyul",
        8: "Avgust",
        9: "Sentabr",
        10: "Oktabr",
        11: "Noyabr",
        12: "Dekabr",
    }

    text = f"👑 <b>{year} Champions</b>\n\n"

    if not champions:

        text += "📭 Hozircha Champion mavjud emas."

    else:

        for champion in champions:

            text += (
                f"🥇 <b>{months.get(champion['month'], champion['month'])}</b>\n"
                f"👤 {champion['full_name']}\n"
                f"⭐ {champion['score']} ball\n\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=champions_back_keyboard(),
    )

    await callback.answer()


# =========================================================
# BACK TO LEADERBOARD
# =========================================================

@router.callback_query(F.data == "lb_back")
async def back_to_leaderboard(callback: CallbackQuery):

    await callback.message.edit_text(
        LEADERBOARD_TEXT,
        reply_markup=leaderboard_keyboard(),
    )

    await callback.answer()