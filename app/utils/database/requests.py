import re
import aiohttp
from datetime import datetime, timedelta
from sqlalchemy import select

from app.utils.database.models import (
    Base,
    engine,
    SoundCloud_Api_Settings,
    File,
    async_session,
    engine,
)
from logging_config import get_app_logger

logger = get_app_logger(name=__name__)
CACHE_EXPIRATION_HOURS = 24


async def get_client_id() -> str:
    """Parse SoundCloud main page and receive client_id"""
    async with aiohttp.ClientSession() as session:
        async with session.get("https://soundcloud.com/") as resp:
            html_text = await resp.text()
            js_urls = re.findall(
                r'src="(https://a-v2\.sndcdn\.com/assets/[^"]+\.js)"', html_text
            )
            for js_url in js_urls:
                async with session.get(js_url) as js_resp:
                    js_text = await js_resp.text()
                    match = re.search(r'client_id\s*:\s*"([a-zA-Z0-9]{32})"', js_text)
                    if match:
                        return match.group(1)
    raise Exception("Client ID not found")


async def get_client_id_cached():
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(SoundCloud_Api_Settings).limit(1))
            row = result.scalar_one_or_none()

            now = datetime.now()
            if (
                row
                and row.updated_at
                and (now - row.updated_at) < timedelta(hours=CACHE_EXPIRATION_HOURS)
            ):
                logger.info("Receive client id from cache")
                return row.client_id

            logger.info("Update and save client id in cache")
            new_client_id = await get_client_id()

            if row:
                row.client_id = new_client_id
                row.updated_at = now
            else:
                session.add(
                    SoundCloud_Api_Settings(client_id=new_client_id, updated_at=now)
                )

            return new_client_id


async def get_file_by_track_id(track_id: str) -> File | None:
    async with async_session() as session:
        return await session.scalar(select(File).where(File.track_id == track_id))


async def set_file_by_track_id(
    filename: str, track_id: str, drive_file_id: str
) -> None:
    async with async_session() as session:
        async with session.begin():
            new_file = File(
                filename=filename, track_id=track_id, drive_file_id=drive_file_id
            )
            session.add(new_file)
            await session.commit()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database alive")
