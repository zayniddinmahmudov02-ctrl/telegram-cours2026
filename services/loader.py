# =========================================================
# IMPORTS
# =========================================================

import asyncio
import csv
import os

from config import (
    ADMIN_ID,
    LEVEL_CONFIG,
    QUIZ_DATA,
)

from loader import bot
from services.logger import logger


# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = BASE_DIR


# =========================================================
# FILME STORAGE
# =========================================================

FILME = []


# =========================================================
# LOAD LEVEL CSV
# =========================================================

def load_level_csv(level, filename):
    data = []

    # =====================================================
    # FILE CHECK
    # =====================================================

    if not os.path.exists(filename):

        logger.warning(f"{filename} topilmadi")

        loop = asyncio.get_event_loop()

        if loop.is_running():

            loop.create_task(
                bot.send_message(
                    ADMIN_ID,
                    f"⚠️ CSV topilmadi:\n{filename}"
                )
            )

        return

    # =====================================================
    # LOAD FILE
    # =====================================================

    try:

        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as f:

            reader = csv.reader(f)

            next(reader, None)

            for row in reader:

                try:

                    if len(row) < 5:
                        continue

                    data.append(
                        {
                            "id": int(row[0]),
                            "german": row[1].strip(),
                            "correct": row[2].strip(),
                            "wrong1": row[3].strip(),
                            "wrong2": row[4].strip(),
                        }
                    )

                except Exception as e:

                    logger.error(
                        f"CSV row error in {level}: {e}"
                    )

    except Exception as e:

        logger.error(
            f"CSV load error for {level}: {e}"
        )

        return

    # =====================================================
    # SAVE
    # =====================================================

    QUIZ_DATA[level] = data

    logger.info(
        f"{level}: {len(data)} loaded ✅"
    )


# =========================================================
# LOAD ALL QUIZZES
# =========================================================

def load_all_quizzes():

    QUIZ_DATA.clear()

    for level, config in LEVEL_CONFIG.items():

        try:

            load_level_csv(
                level,
                config["file"]
            )

        except Exception as e:

            logger.error(
                f"{level} load failed: {e}"
            )

    logger.info("All quizzes loaded ✅")


# =========================================================
# LOAD FILME
# =========================================================

def load_filme():

    FILME.clear()

    try:

        with open(
            "Filme.csv",
            encoding="utf-8"
        ) as f:

            reader = csv.DictReader(f)

            for row in reader:

                FILME.append(
                    {
                        "level":
                            row["level"].strip(),

                        "category":
                            row["category"].strip(),

                        "title":
                            row["title"].strip(),

                        "message_id":
                            int(
                                row["message_id"]
                            )
                    }
                )

        logger.info(
            f"FILME LOADED: {len(FILME)}"
        )

    except Exception as e:

        logger.error(
            f"FILME LOAD ERROR: {e}"
        )


# =========================================================
# LOAD EVERYTHING
# =========================================================

def load_all():

    load_filme()

    load_all_quizzes()

    logger.info("All loaders completed ✅")