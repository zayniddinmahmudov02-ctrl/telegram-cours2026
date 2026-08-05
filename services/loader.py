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
# MEDIA STORAGE
# =========================================================

FILME = []
BUCHER = []
MUSIK = []


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
# LOAD BUCHER
# =========================================================

def load_bucher():

    BUCHER.clear()

    try:

        with open(
            "Bucher.csv",
            encoding="utf-8"
        ) as f:

            reader = csv.DictReader(f)

            for row in reader:

                BUCHER.append(
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
            f"BUCHER LOADED: {len(BUCHER)}"
        )

    except Exception as e:

        logger.error(
            f"BUCHER LOAD ERROR: {e}"
        )


# =========================================================
# LOAD MUSIK
# =========================================================

def load_musik():

    MUSIK.clear()

    try:

        with open(
            "Musik.csv",
            encoding="utf-8"
        ) as f:

            reader = csv.DictReader(f)

            for row in reader:

                MUSIK.append(
                    {
                        "track_number":
                            row["track_number"].strip(),

                        "title":
                            row["title"].strip(),

                        "message_id":
                            int(
                                row["message_id"]
                            )
                    }
                )

        logger.info(
            f"MUSIK LOADED: {len(MUSIK)}"
        )

    except Exception as e:

        logger.error(
            f"MUSIK LOAD ERROR: {e}"
        )


# =========================================================
# LOAD EVERYTHING
# =========================================================

def load_all():

    load_filme()

    load_bucher()

    load_musik()

    load_all_quizzes()

    logger.info("All loaders completed ✅")