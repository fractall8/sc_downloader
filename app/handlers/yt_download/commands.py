from aiogram.types import Message, BufferedInputFile

from logging_config import get_app_logger
from app.utils.api.api_integrations import get_yt_file
from app.utils.helpers.track_metadata import get_cover

logger = get_app_logger()


async def process_yt_track_url(message: Message):
    if not message.text:
        await message.answer("Link must be a string!")
        return
    try:
        track_url_input = message.text

        loading_state_message = await message.answer("Checking your link...")

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
