# 🎵 Downloader Bot

This bot allows you to easily download tracks from SoundCloud and YouTube with automatic caching and storage.

## 🚀 Features

- Download tracks directly from **SoundCloud** and **YouTube**.
- Stores downloaded tracks in **Google Drive** for later use.
- Saves track metadata in a **SQLite**.
- On repeated requests for the same track, the bot **serves the file from Google Drive** instead of downloading it again from SoundCloud or YouTube (faster and saves bandwidth).
- Caches the **SoundCloud client_id** for one day to reduce API calls.

## ⚙️ How It Works

1. User sends a **SoundCloud** or **YouTube** track link.
2. The bot checks if the track is already saved in the database:
   - ✅ If yes → retrieves the track from **Google Drive** and sends it to the user.
   - ❌ If no → downloads the track from **SoundCloud/YouTube**, uploads it to **Google Drive**, saves track info in the database, and then sends it to the user.
3. For SoundCloud, the bot maintains a cached `client_id` for one day. If the client_id becomes invalid, it automatically fetches a new one.

## 🛠️ Tech Stack

- **Python**
- **Aiogram**
- **SQLite**
- **SQLAlchemy**
- **Google Drive API** (file storage)

## 📦 Installation (if you want to run it locally)

1. Clone the repository:

   ```bash
   git clone https://github.com/fractall8/sc_downloader.git
   cd sc_downloader

   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux / macOS
   venv\Scripts\activate     # Windows

   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt

   ```

4. Set up environment variables (.env file):

   ```.env
   BOT_TOKEN=your telegram bot token
   FOLDER_ID=id of folder where bot will save tracks

   ```

5. Receive your credentials from google cloud concole (OAuth Client Id)
   with Google Drive Api enabled. Save this in root and name credentials.json

6. Create docker image for bot
   ```bash
   docker build -t downloader_bot:latest .
   ```
7. Run docker container with your local .env file
   ```bash
   docker run -it --env-file .env downloader_bot
   ```

## 📝 Notes

By default, SoundCloud tracks are downloaded in 128kbps quality (due to API limitations).

YouTube track quality depends on the available source (usually higher than SoundCloud).

Using Google Drive ensures you don’t re-download the same track multiple times.

The bot is designed for personal use only. Distributing copyrighted content may violate SoundCloud’s or YouTube’s terms of service.

## ⚡ Future Improvements

- Support for higher audio quality if available.
- Ability to use the bot directly in the group
- Downloading audio from youtube videos (Done!)
