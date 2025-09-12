from aiogram import Router, html
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.handlers.sc_download.commands import process_sc_track_url
from app.handlers.yt_download.commands import process_yt_track_url

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message):
    """
    This handler receives messages with `/start` command
    """
    await message.answer(
        f"Hey there! 👋\nI'm a bot designed to process YouTube and SoundCloud links.\nJust send me a link to a {html.bold('YouTube video')} or {html.bold('SoundCloud track')}, and I'll respond with audio file! 🎶"
    )


@router.message()
async def any_message(message: Message):
    """Handler for any messages"""
    if not message.text:
        await message.answer(
            f"I see that! 👀 But I'm only built to handle links. Send me a {html.bold('YouTube video')} or {html.bold('SoundCloud track')} link, please!"
        )
        return

    if "soundcloud.com" in message.text:
        await process_sc_track_url(message=message)
    elif "youtube.com" in message.text or "youtu.be" in message.text:
        await process_yt_track_url(message=message)
    else:
        await message.answer(
            f"I can't process that text. 🤔 Please send me a direct link to a {html.bold('YouTube video')} or a {html.bold('SoundCloud track')}."
        )
