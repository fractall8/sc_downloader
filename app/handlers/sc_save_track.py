import os

import logging
from aiogram import Router, html
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.helpers import (
    get_client_id,
    get_track_info,
    get_stream_url,
    download_file,
    resolve_on_soundcloud_url,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sc_save_track = Router()


DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


class TrackInfo(StatesGroup):
    track_url = State()


@sc_save_track.message(Command("sc_download_track"))
async def start_download(message: Message, state: FSMContext):
    await state.set_state(TrackInfo.track_url)
    await message.answer("Send a link to the track you want to download")


@sc_save_track.message(TrackInfo.track_url)
async def process_track_url(message: Message, state: FSMContext):
    if not message.text:
        message.answer("Link must be a string!")
        return
    await state.update_data(track_url=message.text.strip())
    try:
        state_data = await state.get_data()
        track_url_input = state_data.get("track_url")
        if track_url_input is None:
            raise ValueError("Track url not provided")
        track_url = await resolve_on_soundcloud_url(short_url=track_url_input)

        client_id = await get_client_id()
        track_info = await get_track_info(client_id=client_id, track_url=track_url)
        await message.answer(
            f"Starting downloading track... Provided track: {html.link(link=track_url, value=f"{track_info["title"] or "your track"}")}"
        )

        # check if file name is safe for file system
        title_safe = "".join(
            c for c in track_info["title"] if c.isalnum() or c in " _-"
        )
        filename = f"{title_safe}.mp3"

        if track_info.get("downloadable") and "download_url" in track_info:
            download_url = f"{track_info['download_url']}?client_id={client_id}"
            await message.answer("⬇️ Downloading via official download_url")
            file_path = await download_file(
                url=download_url, filename=filename, download_dir=DOWNLOAD_DIR
            )
        else:
            stream_url = await get_stream_url(track=track_info, client_id=client_id)
            if stream_url:
                await message.answer("⬇️ Downloading via progressive stream")
                file_path = await download_file(
                    url=stream_url, filename=filename, download_dir=DOWNLOAD_DIR
                )
            else:
                await message.answer(
                    "❌ Could not find a downloadable link for this track"
                )
                return

        audio_file = FSInputFile(path=file_path, filename=filename)
        await message.reply_audio(audio_file)

    except Exception as e:
        logging.error("Error while downloading track:", e)
        await message.answer(f"Failed to download your track. Error: {str(e)}")
