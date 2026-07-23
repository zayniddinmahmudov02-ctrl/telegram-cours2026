import asyncio
import logging
import os
from threading import Thread

from flask import Flask

from loader import bot, dp

import bot as register_bot

from database import init_database

from handlers.artikel import load_artikel

from services.loader import load_all
from services.runtime import (
    cleanup_quiz_memory,
    daily_reset_scheduler,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.get("/")
def home():
    return "Bot is running ✅"


def run_web():
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        debug=False,
        use_reloader=False,
    )


async def main():

    init_database()

    load_artikel()

    load_all()

    asyncio.create_task(
        cleanup_quiz_memory()
    )

    asyncio.create_task(
        daily_reset_scheduler()
    )

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    Thread(
        target=run_web,
        daemon=True,
    ).start()

    logger.info("VIZU BOT STARTED ✅")

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types(),
    )


if __name__ == "__main__":
    asyncio.run(main())