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
from keyboards.inline.leaderboard import leaderboard_keyboard

router = Router()

# =========================================================
# MENU
# =========================================================

@router.message(Command("leaderboard"))
async def leaderboard_command(message: Message):

    await message.answer(
        "🏆 <b>VIZU Leaderboard</b>\n\n"
        "Kerakli reyting turini tanlang.",
        reply_markup=leaderboard_keyboard(),
    )


@router.message(F.text == "🏆 Reytinglar")
async def leaderboard_menu(message: Message):

    await message.answer(
        "🏆 <b>VIZU Leaderboard</b>\n\n"
        "Kerakli reyting turini tanlang.",
        reply_markup=leaderboard_keyboard(),
    )
# =========================================================
# DAILY
# =========================================================

@router.callback_query(F.data == "lb_daily")
async def daily_top(callback: CallbackQuery):

    top = get_daily_top()

    text = "📅 <b>Kunlik Reyting</b>\n\n"

    if not top:
        text += "Hozircha reyting mavjud emas."
    else:

        medals = ["🥇", "🥈", "🥉"]

        for index, row in enumerate(top, start=1):

            if index <= 3:
                place = medals[index - 1]
            else:
                place = f"{index}."

            text += (
                f"{place} "
                f"<b>{row['full_name']}</b>\n"
                f"⭐ {row['daily_score']} ball\n\n"
            )

    rank = get_user_rank(
        callback.from_user.id,
        "daily",
    )

    text += "━━━━━━━━━━━━━━\n\n"

    if rank:
        text += (
            f"👤 <b>Sizning o'rningiz:</b> #{rank}"
        )
    else:
        text += (
            "👤 Siz hali reytingda emassiz."
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

    top = get_weekly_top()

    text = "📆 <b>Haftalik Reyting</b>\n\n"

    if not top:
        text += "Hozircha reyting mavjud emas."
    else:

        medals = ["🥇", "🥈", "🥉"]

        for index, row in enumerate(top, start=1):

            if index <= 3:
                place = medals[index - 1]
            else:
                place = f"{index}."

            text += (
                f"{place} "
                f"<b>{row['full_name']}</b>\n"
                f"⭐ {row['weekly_score']} ball\n\n"
            )

    rank = get_user_rank(
        callback.from_user.id,
        "weekly",
    )

    text += "\n━━━━━━━━━━━━━━\n\n"

    if rank:
        text += f"👤 <b>Sizning o'rningiz:</b> #{rank}"
    else:
        text += "👤 Siz hali reytingda emassiz."

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

    top = get_monthly_top()

    text = "🗓 <b>Oylik Reyting</b>\n\n"

    if not top:
        text += "Hozircha reyting mavjud emas."
    else:

        medals = ["🥇", "🥈", "🥉"]

        for index, row in enumerate(top, start=1):

            if index <= 3:
                place = medals[index - 1]
            else:
                place = f"{index}."

            text += (
                f"{place} "
                f"<b>{row['full_name']}</b>\n"
                f"⭐ {row['monthly_score']} ball\n\n"
            )

    rank = get_user_rank(
        callback.from_user.id,
        "monthly",
    )

    text += "\n━━━━━━━━━━━━━━\n\n"

    if rank:
        text += f"👤 <b>Sizning o'rningiz:</b> #{rank}"
    else:
        text += "👤 Siz hali reytingda emassiz."

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

    top = get_global_top()

    text = "🌍 <b>Global Reyting</b>\n\n"

    if not top:
        text += "Hozircha reyting mavjud emas."
    else:

        medals = ["🥇", "🥈", "🥉"]

        for index, row in enumerate(top, start=1):

            if index <= 3:
                place = medals[index - 1]
            else:
                place = f"{index}."

            text += (
                f"{place} "
                f"<b>{row['full_name']}</b>\n"
                f"⭐ {row['global_score']} ball\n\n"
            )

    rank = get_user_rank(
        callback.from_user.id,
        "global",
    )

    text += "\n━━━━━━━━━━━━━━\n\n"

    if rank:
        text += f"👤 <b>Sizning o'rningiz:</b> #{rank}"
    else:
        text += "👤 Siz hali reytingda emassiz."

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

    champions = get_monthly_champions(2026)

    text = "👑 <b>VIZU Champions</b>\n\n"

    text += "🏆 <b>2026 Champions</b>\n\n"

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

    if not champions:

        text += "Hozircha Champion mavjud emas."

    else:

        for champion in champions:

            text += (
                f"👑 <b>{months.get(champion['month'])}</b>\n"
                f"🥇 {champion['full_name']}\n"
                f"⭐ {champion['score']} ball\n\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=leaderboard_keyboard(),
    )

    await callback.answer()
# =========================================================
# CHAMPIONS YEARS
# =========================================================

@router.callback_query(F.data == "champions")
async def champions(callback: CallbackQuery):

    text = (
        "👑 <b>VIZU Champions</b>\n\n"
        "Quyidagi yillardan birini tanlang."
    )

    await callback.message.edit_text(
        text,
        reply_markup=champions_years_keyboard(),
    )

    await callback.answer()


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

        text += "Hozircha Champion mavjud emas."

    else:

        for champion in champions:

            text += (
                f"🥇 <b>{months[champion['month']]}</b>\n"
                f"👤 {champion['full_name']}\n"
                f"⭐ {champion['score']} ball\n\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=champions_back_keyboard(),
    )

    await callback.answer()


# =========================================================
# BACK
# =========================================================

@router.callback_query(F.data == "leaderboard")
async def leaderboard(callback: CallbackQuery):

    await callback.message.edit_text(
        "🏆 <b>VIZU Leaderboard</b>\n\n"
        "Kerakli reyting turini tanlang.",
        reply_markup=leaderboard_keyboard(),
    )

    await callback.answer()