from aiogram import Router, html
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(
        f"Hello, this bot is created to save tracks from {html.bold('SoundCloud')} or {html.bold('YouTube')}"
    )
    await message.answer(
        "Download tracks from SoundCloud with /sc_download_track\nand audio from YouTube with /yt_download_track"
    )
