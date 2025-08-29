import requests
from datetime import datetime
from io import BytesIO
from mutagen.id3._frames import TIT2, TPE1, TALB, TYER, APIC, TCON
from mutagen.mp3 import MP3

from logging_config import get_app_logger

logger = get_app_logger(name=__name__)


def add_metadata(
    audio_file: BytesIO,
    track_info: dict,
) -> BytesIO | None:
    try:
        album = track_info.get("publisher_metadata", {}).get("album_title", "")
        artist = track_info.get("publisher_metadata", {}).get("artist", "")
        title = track_info.get("title", "")
        genre = track_info.get("genre", "")

        dt = datetime.strptime(track_info.get("display_date", ""), "%Y-%m-%dT%H:%M:%SZ")
        year = str(dt.year)

        # download cover
        response = requests.get(track_info.get("artwork_url", ""))
        response.raise_for_status()

        cover_bytes = BytesIO(response.content).read()

        audio_file.seek(0)

        mp3 = MP3(fileobj=audio_file)
        if mp3.tags is None:
            mp3.add_tags()

        if mp3.tags is None:
            return

        mp3.tags.add(TIT2(encoding=3, text=title))
        mp3.tags.add(TPE1(encoding=3, text=artist))
        mp3.tags.add(TALB(encoding=3, text=album))
        mp3.tags.add(TCON(encoding=3, text=genre))
        mp3.tags.add(TYER(encoding=3, text=year))

        if cover_bytes:
            mp3.tags.add(
                APIC(
                    encoding=3,
                    mime="image/jpeg",
                    type=3,
                    desc="Cover",
                    data=cover_bytes,
                )
            )

        mp3.save(fileobj=audio_file)
        audio_file.seek(0)
        return audio_file
    except Exception as e:
        logger.error("Failed to add metadata: %s", e)


def get_cover(audio_bytes: bytes) -> bytes | None:
    try:
        audio_file = BytesIO(audio_bytes)
        mp3 = MP3(fileobj=audio_file)
        if mp3.tags is None:
            return
        apic = mp3.tags.get("APIC:Cover")
        return apic.data
    except Exception as e:
        logger.error("Failed to get cover: %s", e)
