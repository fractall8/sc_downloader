import aiohttp
from io import BytesIO


async def resolve_soundcloud_url(short_url: str) -> str:
    """If user provides short url, resolve full url"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(short_url, allow_redirects=True) as resp:
                return str(resp.url)
    except Exception as e:
        raise Exception(f"Failed to resolve track url, provided url: {short_url}")


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
