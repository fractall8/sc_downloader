import asyncio
from dotenv import load_dotenv
from os import getenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.handlers.sc_download.commands import sc_download
from app.handlers.index import router
from logging_config import get_app_logger
from app.utils.database.requests import init_db

load_dotenv()
TOKEN = getenv("BOT_TOKEN")
main_logger = get_app_logger(name="main")


async def main() -> None:
    if TOKEN is None:
        main_logger.error("BOT_TOKEN env variable is missing!")
        raise ValueError("BOT_TOKEN env variable is missing!")

    await init_db()

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_routers(router, sc_download)
    main_logger.info("Starting polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        main_logger.info("Shutting down...")
