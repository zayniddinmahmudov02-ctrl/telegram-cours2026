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

from services.ranking import reset_daily_scores
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
# DAILY RESET
# =========================================================

async def daily_reset_scheduler():

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

        reset_daily_scores()

        logger.info(
            "Daily scores reset ✅"
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