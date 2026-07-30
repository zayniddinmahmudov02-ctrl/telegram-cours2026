from datetime import datetime, timedelta

from aiogram import Bot

from database.leaderboard import (
    get_period_champion,
    save_weekly_champion,
    save_monthly_champion,
)
from database.users import get_all_users
from services.logger import logger


# =========================================================
# BROADCAST
# =========================================================

async def broadcast_to_all(bot: Bot, text: str):
    """
    Send a message to every non-blocked user. Reuses the same
    best-effort, per-user try/except pattern as the admin
    broadcast feature (handlers/broadcast.py).
    """

    users = get_all_users()

    sent = 0
    failed = 0

    for user in users:

        try:
            await bot.send_message(
                user["user_id"],
                text,
                parse_mode="HTML",
            )
            sent += 1

        except Exception:
            failed += 1

    return sent, failed


# =========================================================
# WEEKLY CHAMPION
# =========================================================

async def process_weekly_champion(bot: Bot, week_end: datetime):
    """
    Determine the champion of the week that just ended
    ([week_end - 7 days, week_end)), save it permanently and
    broadcast it to every user. Does not touch xp_events or
    user_scores - the new week's ranking starts "fresh" simply
    because it is computed from that point forward in time.
    """

    week_start = week_end.replace(
        hour=0, minute=0, second=0, microsecond=0,
    ) - timedelta(days=7)

    champion = get_period_champion(week_start, week_end)

    if not champion or not champion["score"]:
        logger.info("Weekly champion: no activity this week.")
        return None

    iso_year, iso_week, _ = week_start.isocalendar()

    save_weekly_champion(
        year=iso_year,
        week=iso_week,
        user_id=champion["user_id"],
        score=champion["score"],
    )

    text = (
        "🏆 <b>Weekly Champion</b>\n\n"
        f"🥇 {champion['full_name']}\n"
        f"⭐ XP: {champion['score']:,}\n\n"
        "Congratulations!\n"
        "A new week has begun.\n"
        "Fight to become the next champion!"
    )

    sent, failed = await broadcast_to_all(bot, text)

    logger.info(
        f"Weekly champion: {champion['full_name']} "
        f"({champion['score']} XP) - broadcast to {sent}, "
        f"failed {failed} ✅"
    )

    return champion


# =========================================================
# MONTHLY CHAMPION
# =========================================================

async def process_monthly_champion(bot: Bot, month_end: datetime):
    """
    Determine the champion of the calendar month that just
    ended, save it permanently and broadcast it to every user.
    """

    this_month_start = month_end.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0,
    )

    last_day_of_prev_month = this_month_start - timedelta(days=1)
    month_start = last_day_of_prev_month.replace(day=1)

    champion = get_period_champion(month_start, month_end)

    if not champion or not champion["score"]:
        logger.info("Monthly champion: no activity this month.")
        return None

    save_monthly_champion(
        year=month_start.year,
        month=month_start.month,
        user_id=champion["user_id"],
        score=champion["score"],
    )

    text = (
        "🏆 <b>Monthly Champion</b>\n\n"
        f"🥇 {champion['full_name']}\n"
        f"⭐ XP: {champion['score']:,}\n\n"
        "Congratulations!\n"
        "A new month has begun.\n"
        "Can you become the next champion?"
    )

    sent, failed = await broadcast_to_all(bot, text)

    logger.info(
        f"Monthly champion: {champion['full_name']} "
        f"({champion['score']} XP) - broadcast to {sent}, "
        f"failed {failed} ✅"
    )

    return champion
