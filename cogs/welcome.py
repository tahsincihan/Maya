import asyncio
import logging
import random

import discord
from discord.ext import commands

log = logging.getLogger(__name__)


_WELCOME_GREETINGS = [
    "hiiii {name} 🩷 omg you actually joined!! welcome to the server bestie!!",
    "omg omg omg {name}!! welcome welcome welcome 🫶 so happy you're here!!",
    "heyy {name}!! welcome to the chaos, you're gonna fit right in 💗",
    "HIII {name} 🩷 welcome to the server!! honestly so glad you made it",
    "omg {name} just joined!! welcome bestie 🎉 this place just got way more fun",
    "hey hey hey {name}!! welcome 🫶 don't be shy, say hi!!",
    "omg {name}!! you're here!! welcome welcome 🩷 we've been waiting for you",
    "hiii {name} welcome!! 👀 i have a good feeling about you already",
    "yayy {name} is here!! welcome to the server 💗 so happy you're in here with us",
    "omg hi {name}!! 🫶 welcome!! you're gonna love it here i promise",
]


class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _get_welcome_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        target_name = "ajira-chat"
        for channel in guild.text_channels:
            if target_name in channel.name:
                log.info(f"Found welcome channel: {channel.name} (ID: {channel.id})")
                return channel
        log.warning(f"Welcome channel not found in {guild.name}. Available channels: {[c.name for c in guild.text_channels]}")
        return None

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        log.info(f"Member joined: {member.name} (ID: {member.id})")
        if member.bot:
            log.info(f"Skipping bot: {member.name}")
            return

        channel = self._get_welcome_channel(member.guild)
        if channel is None:
            log.warning(f"No welcome channel found for {member.guild.name}")
            return

        log.info(f"Waiting 30 seconds before greeting {member.name}")
        await asyncio.sleep(30)

        if member.guild.get_member(member.id) is None:
            log.info(f"Member {member.name} left before greeting")
            return

        greeting = random.choice(_WELCOME_GREETINGS).format(name=member.mention)
        await channel.send(greeting)
        log.info(f"Greeted {member.name} in {channel.name}")
