import re
import aiohttp
from io import BytesIO
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload


# invoked on every request, cache for future
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


async def resolve_soundcloud_url(short_url: str) -> str:
    """If user provides short url, resolve full url"""
    async with aiohttp.ClientSession() as session:
        async with session.get(short_url, allow_redirects=True) as resp:
            return str(resp.url)


async def get_track_info(client_id: str, track_url: str) -> dict:
    """Receive SoundCloud track info"""
    api_url = (
        f"https://api-v2.soundcloud.com/resolve?url={track_url}&client_id={client_id}"
    )
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to resolve track: HTTP {resp.status}")
            response = await resp.json()
            if response.get("kind") != "track":
                raise ValueError("Provided URL does not resolve to a track")
            return response


async def get_stream_url(track: dict, client_id: str) -> str | None:
    """Return progressive stream"""
    for transcoding in track.get("media", {}).get("transcodings", []):
        if transcoding["format"]["protocol"] == "progressive":
            url = transcoding["url"] + f"?client_id={client_id}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    data = await resp.json()
                    return data.get("url")
    raise Exception("No progressive stream url found")


def get_drive_service():
    creds = None

    # full access to files created by the application
    SCOPES = ["https://www.googleapis.com/auth/drive.file"]

    # Read access token from file (if exists)
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


async def download_file(url: str) -> BytesIO:
    """Download track with download url or stream url and return file (BytesIO)"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to download file: HTTP {resp.status}")

            fh = BytesIO()
            while True:
                chunk = await resp.content.read(8192)
                if not chunk:
                    break
                fh.write(chunk)

            fh.seek(0)

            return fh


async def upload_file_to_drive(file: BytesIO, filename: str, folder_id: str) -> dict:
    """Upload file to Google Drive"""
    drive_service = get_drive_service()

    file_metadata = {
        "name": filename,
        "parents": [folder_id],
    }
    media = MediaIoBaseUpload(file, mimetype="audio/mpeg", resumable=True)

    uploaded_file = (
        drive_service.files()
        .create(body=file_metadata, media_body=media, fields="id, name, webViewLink")
        .execute()
    )

    return uploaded_file


async def save_file(url: str, filename: str) -> bytes:
    fh = await download_file(url=url)

    FOLDER_ID = os.getenv("FOLDER_ID")
    if FOLDER_ID is None:
        raise ValueError("FOLDER_ID env variable is not set")

    await upload_file_to_drive(file=fh, filename=filename, folder_id=FOLDER_ID)
    # upload file to drive reads fh, so after this func call fh.read() is empty. Manually set pointer to the start.
    fh.seek(0)

    file_bytes = fh.read()
    return file_bytes


async def download_file_from_drive(file_id: str) -> dict:
    drive_service = get_drive_service()
    request = drive_service.files().get_media(fileId=file_id)
    fh = BytesIO()

    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()

    fh.seek(0)

    file_bytes = fh.read()

    file_info = (
        drive_service.files()
        .get(fileId=file_id, fields="id, name, mimeType, size, webViewLink")
        .execute()
    )

    return {"file": file_bytes, "name": file_info["name"]}
