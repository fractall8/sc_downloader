import os, base64, json
from io import BytesIO
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload


def get_drive_service():
    # full access to files created by the application
    SCOPES = ["https://www.googleapis.com/auth/drive.file"]
    CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS_B64")
    if CREDENTIALS is None:
        raise ValueError("Google Drive user is not authorized")

    creds_json = json.loads(base64.b64decode(CREDENTIALS).decode("utf-8"))
    creds = Credentials.from_authorized_user_info(creds_json, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception("Google Drive refresh token expired.")

    return build("drive", "v3", credentials=creds)


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


async def download_file_from_drive(file_id: str) -> bytes:
    drive_service = get_drive_service()
    request = drive_service.files().get_media(fileId=file_id)
    fh = BytesIO()

    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()

    fh.seek(0)

    return fh.read()
