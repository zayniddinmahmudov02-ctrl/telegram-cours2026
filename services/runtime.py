import asyncio
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from config import (
    APP_TIMEZONE,
    GENERATED_DIR,
    active_questions,
    answered_users,
    quiz_sessions,
    quiz_running,
)

from loader import bot
from services.ranking import (
    process_daily_champion,
    process_weekly_champion,
    process_monthly_champion,
)
from services.logger import logger

TZ = ZoneInfo(APP_TIMEZONE)


# =========================================================
# BOUNDARY HELPERS
# =========================================================
# Each _next_*_boundary() returns the next upcoming reset
# instant strictly in the future relative to `now` - used both
# to know how long to sleep, and (via the *_start companions
# below) to know which period just ended, for restart catch-up.

def _next_daily_boundary(now: datetime) -> datetime:
    target = now.replace(hour=0, minute=0, second=5, microsecond=0)

    if now >= target:
        target += timedelta(days=1)

    return target


def _next_weekly_boundary(now: datetime) -> datetime:
    days_until_monday = (7 - now.weekday()) % 7

    target = (
        now + timedelta(days=days_until_monday)
    ).replace(hour=0, minute=0, second=5, microsecond=0)

    if target <= now:
        target += timedelta(days=7)

    return target


def _next_monthly_boundary(now: datetime) -> datetime:
    # Start with THIS month's boundary, not next month's - if
    # `now` is still before it (e.g. it's the 1st at 00:00:02),
    # that is the correct target. Only advance to next month if
    # this month's boundary has already passed. The previous
    # version always jumped straight to next month, which meant
    # a scheduler that happened to (re)start in the first few
    # seconds of a new month would skip that month's own reset
    # entirely and wait a full month too long.
    target = now.replace(
        day=1, hour=0, minute=0, second=5, microsecond=0,
    )

    if target <= now:

        if target.month == 12:
            target = target.replace(year=target.year + 1, month=1)
        else:
            target = target.replace(month=target.month + 1)

    return target


def _current_day_start(now: datetime) -> datetime:
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _current_week_start(now: datetime) -> datetime:
    return _current_day_start(now) - timedelta(days=now.weekday())


def _current_month_start(now: datetime) -> datetime:
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


# =========================================================
# AUTO MEMORY CLEANUP
# =========================================================

async def cleanup_quiz_memory():

    while True:

        # Xotira to'lib ketmasligi uchun
        if len(active_questions) > 2000:
            active_questions.clear()

        if len(answered_users) > 2000:
            answered_users.clear()

        # O'lik sessiyalarni tozalash
        for uid in list(quiz_sessions.keys()):

            if uid not in quiz_running:

                quiz_sessions.pop(uid, None)

        # Eski PNG fayllarni tozalash
        if os.path.exists(GENERATED_DIR):

            for file in os.listdir(GENERATED_DIR):

                if file.endswith(".png"):

                    try:
                        os.remove(
                            os.path.join(
                                GENERATED_DIR,
                                file
                            )
                        )
                    except OSError:
                        pass

        await asyncio.sleep(3600)


# =========================================================
# DAILY CHAMPION
# =========================================================
# Daily ranking never needs a reset - it is always computed
# from xp_events filtered to "today". This scheduler determines
# and permanently stores yesterday's champion (no broadcast -
# see process_daily_champion) once every midnight.

async def daily_champion_scheduler():

    now = datetime.now(TZ)

    # Catch-up: if the bot was offline when today's midnight
    # passed, yesterday's champion would otherwise never be
    # recorded. process_daily_champion() is idempotent, so this
    # is safe even if nothing was actually missed.
    try:
        await process_daily_champion(_current_day_start(now))
    except Exception as e:
        logger.error(f"Daily champion catch-up failed: {e}")

    while True:

        now = datetime.now(TZ)
        target = _next_daily_boundary(now)

        await asyncio.sleep(
            (target - now).total_seconds()
        )

        try:
            await process_daily_champion(target)

        except Exception as e:
            logger.error(
                f"Daily champion processing failed: {e}"
            )

        logger.info(
            "New daily ranking started automatically "
            "(no data reset - date-filtered) ✅"
        )


# =========================================================
# WEEKLY CHAMPION
# =========================================================

async def weekly_champion_scheduler():

    now = datetime.now(TZ)

    # Catch-up for a week that fully ended while the bot was
    # offline (e.g. down over a weekend and restarted Tuesday).
    try:
        await process_weekly_champion(bot, _current_week_start(now))
    except Exception as e:
        logger.error(f"Weekly champion catch-up failed: {e}")

    while True:

        now = datetime.now(TZ)
        target = _next_weekly_boundary(now)

        await asyncio.sleep(
            (target - now).total_seconds()
        )

        try:
            await process_weekly_champion(bot, target)

        except Exception as e:
            logger.error(
                f"Weekly champion processing failed: {e}"
            )

        logger.info(
            "New weekly ranking started automatically ✅"
        )


# =========================================================
# MONTHLY CHAMPION
# =========================================================

async def monthly_champion_scheduler():

    now = datetime.now(TZ)

    # Catch-up for a month that fully ended while the bot was
    # offline.
    try:
        await process_monthly_champion(bot, _current_month_start(now))
    except Exception as e:
        logger.error(f"Monthly champion catch-up failed: {e}")

    while True:

        now = datetime.now(TZ)
        target = _next_monthly_boundary(now)

        await asyncio.sleep(
            (target - now).total_seconds()
        )

        try:
            await process_monthly_champion(bot, target)

        except Exception as e:
            logger.error(
                f"Monthly champion processing failed: {e}"
            )

        logger.info(
            "New monthly ranking started automatically ✅"
        )
# =========================================================
# RUNTIME VARIABLES
# =========================================================

# Quiz
QUIZ_DATA = {}
quiz_running = set()
quiz_sessions = {}
active_questions = {}
answered_users = {}

# Admin
approved_users = set()
admin_sessions = {}

# Daily Reset
last_daily_reset = None
# Artikel Search
artikel_data = {}
artikel_users = {}
