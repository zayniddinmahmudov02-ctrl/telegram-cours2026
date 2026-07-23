# =========================================================
# STANDARD LIBRARY
# =========================================================

import asyncio
import logging
import os
from threading import Thread

# =========================================================
# FLASK
# =========================================================

from flask import Flask

# =========================================================
# AIOGRAM
# =========================================================

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# =========================================================
# CONFIG
# =========================================================

from config import TOKEN

# =========================================================
# DATABASE
# =========================================================

from database import init_database

# =========================================================
# MIDDLEWARES
# =========================================================

from middlewares import SubscriptionMiddleware

# =========================================================
# SERVICES
# =========================================================

from services.loader import load_all
from services.runtime import (
    cleanup_quiz_memory,
    daily_reset_scheduler,
)

# =========================================================
# HANDLERS
# =========================================================

from handlers.start import router as start_router
from handlers.artikel import (
    router as artikel_router,
    load_artikel,
)
from handlers.profile import router as profile_router
from handlers.wordgame import router as wordgame_router
from handlers.quiz_callback import router as quiz_router
from handlers.ranking import router as ranking_router
from handlers.xp import router as xp_router

from handlers.certificate import router as certificate_router

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================================================
# BOT
# =========================================================

bot = Bot(token=TOKEN)

storage = MemoryStorage()

dp = Dispatcher(storage=storage)

# =========================================================
# ROUTERS
# =========================================================

dp.include_router(start_router)
dp.include_router(artikel_router)
dp.include_router(profile_router)
dp.include_router(wordgame_router)
dp.include_router(quiz_router)
dp.include_router(ranking_router)
dp.include_router(xp_router)
dp.include_router(certificate_router)

# =========================================================
# MIDDLEWARE
# =========================================================

subscription = SubscriptionMiddleware()

dp.message.middleware(subscription)
dp.callback_query.middleware(subscription)

# =========================================================
# WEB SERVER
# =========================================================

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

# =========================================================
# MAIN
# =========================================================

async def main():

    init_database()

    load_artikel()
    load_all()

    asyncio.create_task(cleanup_quiz_memory())
    asyncio.create_task(daily_reset_scheduler())

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    Thread(
        target=run_web,
        daemon=True,
    ).start()

    logger.info("BOT ISHGA TUSHDI ✅")

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types(),
    )


if __name__ == "__main__":
    asyncio.run(main())