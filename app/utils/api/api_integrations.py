from os import getenv

from app.utils.database.requests import get_file_by_track_id, set_file_by_track_id
from app.utils.api.soundcloud import download_file
from app.utils.api.youtube import download_yt_audio, get_video_metadata
from app.utils.api.google_drive import download_file_from_drive, upload_file_to_drive
from app.utils.helpers.track_metadata import add_metadata
from logging_config import get_app_logger

logger = get_app_logger(name=__name__)


async def get_sc_file(
    track_id: str, url: str, filename: str, track_info: dict
) -> bytes:
    cached_file = await get_file_by_track_id(track_id=track_id)
    if cached_file:
        logger.info(f"Download file for {track_id} id from drive")
        return await download_file_from_drive(cached_file.drive_file_id)

    fh = await download_file(url=url)

    audio_file = add_metadata(
        audio_file=fh,
        track_info=track_info,
    )
    if audio_file is None:
        audio_file = fh

    FOLDER_ID = getenv("FOLDER_ID")
    if FOLDER_ID is None:
        raise ValueError("FOLDER_ID env variable is not set")

    uploaded_file_metadata = await upload_file_to_drive(
        file=audio_file, filename=filename, folder_id=FOLDER_ID
    )
    logger.info(f"Save file for {track_id} id in db")
    await set_file_by_track_id(
        filename=filename, track_id=track_id, drive_file_id=uploaded_file_metadata["id"]
    )
    # upload file to drive reads audio_file, so after this func call audio_file.read() is empty. Manually set pointer to the start.
    audio_file.seek(0)

    return audio_file.read()


async def get_yt_file(url: str):
    meta = get_video_metadata(url=url)
    video_id = meta.get("id", "")
    cached_file = await get_file_by_track_id(track_id=video_id)

    if cached_file:
        logger.info(f"Download file for {video_id} id from drive")
        return await download_file_from_drive(cached_file.drive_file_id), meta

    fh, meta = download_yt_audio(url=url)
    audio_file = add_metadata(audio_file=fh, track_info=meta)
    if audio_file is None:
        audio_file = fh

    FOLDER_ID = getenv("FOLDER_ID")
    if FOLDER_ID is None:
        raise ValueError("FOLDER_ID env variable is not set")

    uploaded_file_metadata = await upload_file_to_drive(
        file=audio_file,
        filename=meta.get("title", ""),
        folder_id=FOLDER_ID,
    )
    logger.info(f"Save file for {video_id} id in db")
    await set_file_by_track_id(
        filename=meta.get("title", ""),
        track_id=video_id,
        drive_file_id=uploaded_file_metadata["id"],
    )
    # upload file to drive reads audio_file, so after this func call audio_file.read() is empty. Manually set pointer to the start.
    audio_file.seek(0)

    return audio_file.read(), meta
