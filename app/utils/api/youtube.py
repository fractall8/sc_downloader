import yt_dlp
from io import BytesIO
from pathlib import Path
import tempfile


def get_video_metadata(url: str):
    ydl_opts = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if info is None:
            raise RuntimeError("Failed to download track")

        fmt = (info.get("requested_downloads") or [None])[0] or {}
        upload_date = info.get("upload_date")
        year = upload_date[:4] if upload_date else None

        metadata = {
            "id": info.get("id"),
            "title": info.get("title", "Untitled"),
            "author": info.get("uploader", "Unknown"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "bitrate": fmt.get("abr"),
            "sample_rate": fmt.get("asr"),
            "year": year,
        }

        return metadata


def download_yt_audio(url: str):
    buffer = BytesIO()
    buffer.name = "audio.mp3"

    with tempfile.TemporaryDirectory() as tmpdir:
        outtmpl = str(Path(tmpdir) / "%(id)s.%(ext)s")

        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "outtmpl": outtmpl,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                raise RuntimeError("Failed to download track")

            mp3_path = Path(tmpdir) / f"{info['id']}.mp3"
            if not mp3_path.exists():
                raise FileNotFoundError("Finished MP3 not found after post processing")

            with open(mp3_path, "rb") as f:
                buffer.write(f.read())
            buffer.seek(0)

    fmt = (info.get("requested_downloads") or [None])[0] or {}
    upload_date = info.get("upload_date")
    year = upload_date[:4] if upload_date else None

    metadata = {
        "id": info.get("id"),
        "title": info.get("title", "Untitled"),
        "author": info.get("uploader", "Unknown"),
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),
        "bitrate": fmt.get("abr"),
        "sample_rate": fmt.get("asr"),
        "year": year,
    }

    return buffer, metadata
