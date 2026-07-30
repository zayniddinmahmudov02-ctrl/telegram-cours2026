import asyncio
import os
from datetime import datetime, timedelta

from config import (
    GENERATED_DIR,
    active_questions,
    answered_users,
    quiz_sessions,
    quiz_running,
)

from loader import bot
from services.ranking import (
    process_weekly_champion,
    process_monthly_champion,
)
from services.logger import logger


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
# from xp_events filtered to "today". This scheduler just logs
# the day's rollover (and, optionally, the previous day's top
# player) once every midnight.

async def daily_champion_scheduler():

    while True:

        now = datetime.now()

        target = now.replace(
            hour=0,
            minute=0,
            second=5,
            microsecond=0
        )

        if now >= target:

            target += timedelta(days=1)

        await asyncio.sleep(
            (target - now).total_seconds()
        )

        logger.info(
            "New daily ranking started automatically "
            "(no data reset - date-filtered) ✅"
        )


# =========================================================
# WEEKLY CHAMPION
# =========================================================

async def weekly_champion_scheduler():

    while True:

        now = datetime.now()

        days_until_monday = (7 - now.weekday()) % 7

        target = (
            now + timedelta(days=days_until_monday)
        ).replace(
            hour=0,
            minute=0,
            second=5,
            microsecond=0,
        )

        if target <= now:
            target += timedelta(days=7)

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

    while True:

        now = datetime.now()

        if now.month == 12:
            target = now.replace(
                year=now.year + 1,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=5,
                microsecond=0,
            )
        else:
            target = now.replace(
                month=now.month + 1,
                day=1,
                hour=0,
                minute=0,
                second=5,
                microsecond=0,
            )

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
