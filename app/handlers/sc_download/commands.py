from aiogram.types import Message, BufferedInputFile

from app.utils.api.api_integrations import get_sc_file
from app.utils.api.soundcloud import (
    get_track_info,
    get_stream_url,
    resolve_soundcloud_url,
)
from app.utils.database.requests import get_client_id_cached
from app.utils.helpers.track_metadata import get_cover
from logging_config import get_app_logger

logger = get_app_logger(name=__name__)


async def process_sc_track_url(message: Message):
    if not message.text:
        await message.answer("Link must be a string!")
        return
    try:
        track_url_input = message.text
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
            file_bytes = await get_sc_file(
                track_id=track_info["id"],
                url=download_url,
                filename=filename,
                track_info=track_info,
            )
        else:
            stream_url = await get_stream_url(track=track_info, client_id=client_id)
            if stream_url:
                file_bytes = await get_sc_file(
                    track_id=track_info["id"],
                    url=stream_url,
                    filename=filename,
                    track_info=track_info,
                )
            else:
                await message.answer(
                    "Could not find a downloadable link for this track :("
                )
                await loading_state_message.delete()
                return

        thumb = None
        apic = get_cover(audio_bytes=file_bytes)
        if apic:
            thumb = BufferedInputFile(apic, filename="cover.jpg")

        await loading_state_message.edit_text("Done, sending your file ;)")

        await message.reply_audio(
            audio=BufferedInputFile(file=file_bytes, filename=filename), thumb=thumb
        )
        await loading_state_message.delete()

    except Exception as e:
        logger.error("Error while downloading track: %s", e)
        await message.answer(
            f"Oops, failed to download track. Maybe the link is incorrect or the track does not have available audio. Try again or if the error persists another URL."
        )
