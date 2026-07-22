import asyncio
import logging

from aiogram import Bot

from bot import bot, dp

# Handlers
import handlers.media


async def main():
    logging.info("VIZU Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())