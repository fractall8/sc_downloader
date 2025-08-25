import re
import aiohttp
import os


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


async def resolve_on_soundcloud_url(short_url: str) -> str:
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
            if response["kind"] == "playlist":
                raise Exception(f"A link to a playlist was provided, not to a track.")
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
    return None


# handle the case if the track is already saved (maybe handle not here)
async def download_file(url: str, filename: str, download_dir: str):
    """Download track with download url or stream url"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to download file: HTTP {resp.status}")
            path = os.path.join(download_dir, filename)
            with open(path, "wb") as f:
                while True:
                    chunk = await resp.content.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
            return path
