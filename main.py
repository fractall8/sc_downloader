import asyncio
import logging
import sys
from dotenv import load_dotenv
from os import getenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.handlers.sc_download.commands import sc_download
from app.handlers.index import router

load_dotenv()
TOKEN = getenv("BOT_TOKEN")


async def main() -> None:
    if TOKEN is None:
        raise ValueError("BOT_TOKEN env variable is missing!")

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_routers(router, sc_download)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Shutting down...")
