from aiogram import Router
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from logging_config import get_app_logger
from app.utils.api.api_integrations import get_yt_file
from app.utils.helpers.track_metadata import get_cover

logger = get_app_logger()

yt_download = Router()


class YouTubeAudio(StatesGroup):
    video_url = State()


@yt_download.message(Command("yt_download_track"))
async def start_download(message: Message, state: FSMContext):
    await state.set_state(YouTubeAudio.video_url)
    await message.answer("Send me YouTube video link and I will download the audio!")


@yt_download.message(YouTubeAudio.video_url)
async def process_track_url(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Link must be a string!")
        return
    await state.update_data(track_url=message.text.strip())
    try:
        state_data = await state.get_data()
        track_url_input = state_data.get("track_url")

        loading_state_message = await message.answer("Checking your link...")
        if track_url_input is None:
            await message.answer("Track url not provided")
            await loading_state_message.delete()
            return

        if not "youtube.com" in track_url_input and not "youtu.be" in track_url_input:
            await message.answer(
                "This doesn't appear to be a YouTube link. Please provide the correct URL."
            )
            await loading_state_message.delete()
            return

        await loading_state_message.edit_text("Downloading audio...")
        file_bytes, meta = await get_yt_file(url=track_url_input)

        thumb = None
        apic = get_cover(audio_bytes=file_bytes)
        if apic:
            thumb = BufferedInputFile(apic, filename="cover.jpg")

        await loading_state_message.edit_text("Done! Sending your file...")
        await message.reply_audio(
            audio=BufferedInputFile(file=file_bytes, filename=meta.get("filename", "")),
            duration=meta.get("duration", 0),
            thumb=thumb,
        )
        loading_state_message.delete()

    except Exception as e:
        logger.error("Error while downloading track: %s", e)
        await message.answer(
            f"Oops, failed to download track. Maybe the link is incorrect or the track does not have available audio. Try again or if the error persists another URL."
        )
