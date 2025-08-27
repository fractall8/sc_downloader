from dotenv import load_dotenv
from aiogram import Router, html
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.utils.api.api_integrations import (
    get_track_info,
    get_stream_url,
    get_file,
    resolve_soundcloud_url,
)
from app.utils.database.requests import get_client_id_cached
from logging_config import get_app_logger

load_dotenv()
logger = get_app_logger(name=__name__)
sc_download = Router()


class TrackInfo(StatesGroup):
    track_url = State()


@sc_download.message(Command("sc_download_track"))
async def start_download(message: Message, state: FSMContext):
    await state.set_state(TrackInfo.track_url)
    await message.answer("Send a link to the track you want to download")


@sc_download.message(TrackInfo.track_url)
async def process_track_url(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Link must be a string!")
        return
    await state.update_data(track_url=message.text.strip())
    try:
        state_data = await state.get_data()
        track_url_input = state_data.get("track_url")

        if track_url_input is None:
            await message.answer("Track url not provided")
            return

        if not "soundcloud.com" in track_url_input:
            await message.answer(
                "This doesn't appear to be a SoundCloud link. Please provide the correct URL."
            )
            return

        loading_state_message = await message.answer("Checking your link...")
        track_url = await resolve_soundcloud_url(short_url=track_url_input)

        client_id = await get_client_id_cached()
        track_info = await get_track_info(client_id=client_id, track_url=track_url)
        await loading_state_message.edit_text("Downloading audio...")

        # check if file name is safe for file system
        title_safe = "".join(
            c for c in track_info["title"] if c.isalnum() or c in " _-"
        )
        filename = f"{title_safe}.mp3"

        if track_info.get("downloadable") and "download_url" in track_info:
            download_url = f"{track_info['download_url']}?client_id={client_id}"
            file_bytes = await get_file(
                track_id=track_info["id"], url=download_url, filename=filename
            )
        else:
            stream_url = await get_stream_url(track=track_info, client_id=client_id)
            if stream_url:
                file_bytes = await get_file(
                    track_id=track_info["id"], url=stream_url, filename=filename
                )
            else:
                await message.answer(
                    "Could not find a downloadable link for this track :("
                )
                return

        await loading_state_message.edit_text("Done, sending your file ;)")
        await message.reply_audio(BufferedInputFile(file=file_bytes, filename=filename))
        await loading_state_message.delete()

    except Exception as e:
        logger.error("Error while downloading track: %s", e)
        await message.answer(
            f"Oops, failed to download track. Maybe the link is incorrect or the track does not have available audio. Try again or if the error persists another URL."
        )
