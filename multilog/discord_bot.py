"""Bot for sending discord messages on a pre-configured computer.
Refer to the discord docs for additional information."""
import asyncio
import os
from os.path import expanduser
import logging

logger = logging.getLogger(__name__)
try:
    from dotenv import load_dotenv
except Exception as e:
    logger.warning("Could not import dotenv.", exc_info=True)
try:
    from discord.ext import commands
except Exception as e:
    logger.warning("Could not import discord.", exc_info=True)


logger = logging.getLogger(__name__)


def send_message(msg):
    logger.info(f"Sending discord message '{msg}'")
    asyncio.set_event_loop(asyncio.new_event_loop())
    load_dotenv(expanduser("~") + "/discord.env")
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    DISCORD_CHANNEL = int(os.getenv("DISCORD_CHANNEL"))

    bot = commands.Bot(command_prefix="cmd!", description="I am NemoOneBot")

    @bot.event
    async def on_ready():
        channel = bot.get_channel(DISCORD_CHANNEL)
        await channel.send(msg)
        await asyncio.sleep(0.5)
        await bot.close()

    bot.run(DISCORD_TOKEN)  # blocking call!
