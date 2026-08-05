from datetime import datetime, timedelta

from aiogram import Bot

from database.leaderboard import (
    get_period_champion,
    daily_champion_exists,
    weekly_champion_exists,
    monthly_champion_exists,
    save_daily_champion,
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

    users = await get_all_users()

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
# DAILY CHAMPION
# =========================================================

async def process_daily_champion(day_end: datetime):
    """
    Determine the champion of the day that just ended
    ([day_end - 1 day, day_end)) and save it permanently.

    No broadcast - a daily announcement to every user would be
    a much higher-frequency notification than weekly/monthly,
    which isn't asked for. History is still kept forever, same
    as weekly/monthly.

    Idempotent: does nothing if that date's champion has
    already been recorded (also enforced by a unique index on
    daily_champions.champion_date).
    """

    day_start = day_end - timedelta(days=1)
    champion_date = day_start.date()

    if await daily_champion_exists(champion_date):
        return None

    champion = await get_period_champion(day_start, day_end)

    if not champion or not champion["score"]:
        logger.info("Daily champion: no activity today.")
        return None

    await save_daily_champion(
        champion_date=champion_date,
        user_id=champion["user_id"],
        score=champion["score"],
    )

    logger.info(
        f"Daily champion ({champion_date}): "
        f"{champion['full_name']} ({champion['score']} XP) ✅"
    )

    return champion


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

    Idempotent: does nothing if that week's champion has
    already been recorded (also enforced by a unique index on
    weekly_champions(year, week)) - safe to call again from a
    restart catch-up check without double-broadcasting.
    """

    week_start = week_end.replace(
        hour=0, minute=0, second=0, microsecond=0,
    ) - timedelta(days=7)

    iso_year, iso_week, _ = week_start.isocalendar()

    if await weekly_champion_exists(iso_year, iso_week):
        return None

    champion = await get_period_champion(week_start, week_end)

    if not champion or not champion["score"]:
        logger.info("Weekly champion: no activity this week.")
        return None

    await save_weekly_champion(
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

    Idempotent: does nothing if that month's champion has
    already been recorded (also enforced by a unique index on
    monthly_champions(year, month)).
    """

    this_month_start = month_end.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0,
    )

    last_day_of_prev_month = this_month_start - timedelta(days=1)
    month_start = last_day_of_prev_month.replace(day=1)

    if await monthly_champion_exists(month_start.year, month_start.month):
        return None

    champion = await get_period_champion(month_start, month_end)

    if not champion or not champion["score"]:
        logger.info("Monthly champion: no activity this month.")
        return None

    await save_monthly_champion(
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
