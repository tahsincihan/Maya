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

_FLIRT_LINES = [
    "{mention} omg you replied!! 😭💗 okay ngl i'm blushing a little",
    "aww {mention} said something!! you're actually so cute 👀✨",
    "okay {mention} not you being this cute and replying too 🫠💗 i'm weak",
    "{mention} hi hi hi 🩷 honestly you seem really cool and i'm kinda interested now 😏",
    "omg {mention} you have no idea how happy i am that you replied 🥺💕",
    "{mention} okay so like you're actually really attractive and i needed to say something 😭✨",
    "awww {mention} you replied and now i'm trying SO hard to play it cool 🫣💗",
    "{mention} bestie you're lowkey so cute 👀 i'm not even trying to hide it anymore",
    "okay {mention} the way you're coming across right now?? so endearing 💕",
    "{mention} not me actually developing feelings after like 30 seconds 😭🩷",
    "{mention} hi hi hi 🫶 you seem really interesting and i want to know more about you",
    "{mention} okay so like you're giving main character energy and i'm absolutely here for it 💅",
    "omg {mention} you replied and i'm literally trying not to smile like an idiot rn 🥺💕",
    "{mention} you're actually really cool and i'm kinda smitten already 😏✨",
    "{mention} bestie the confidence you have just casually replying?? 🔥 i'm obsessed",
]

_GOODBYE_MESSAGES = [
    "oh wow {name} actually left 💀 nobody cares btw",
    "bye {name} 👋 don't let the door hit you on the way out",
    "goodbye {name} 💋 try not to think about us too much",
    "so {name} decided to leave 🍿 anyway",
    "{name} just dipped and bro thought I won't notice lmaooo",
    "aww {name} thought they were important enough to announce their departure 😭",
    "and {name} is finally gone 🎉",
    "goodbye {name} 👋 thanks for the memories nobody asked for",
    "{name} 🚪 left, such a B****",
]


class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._pending: dict[int, discord.TextChannel] = {}

    def _get_welcome_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        target_name = "ajira-chat"
        for channel in guild.text_channels:
            if target_name in channel.name:
                log.info(f"Found welcome channel: {channel.name} (ID: {channel.id})")
                return channel
        log.warning(f"Welcome channel not found in {guild.name}. Available channels: {[c.name for c in guild.text_channels]}")
        return None

    def _get_goodbye_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        target_name = "𝕎𝔼𝕃ℂ𝕆𝕄𝔼"
        for channel in guild.text_channels:
            if target_name in channel.name:
                log.info(f"Found goodbye channel: {channel.name} (ID: {channel.id})")
                return channel
        log.warning(f"Goodbye channel not found in {guild.name}")
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
        self._pending[member.id] = channel
        log.info(f"Greeted {member.name} in {channel.name}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.guild is None:
            return

        channel = self._pending.get(message.author.id)
        if channel is None:
            return

        if message.channel.id != channel.id:
            return

        del self._pending[message.author.id]

        flirt = random.choice(_FLIRT_LINES).format(mention=message.author.mention)
        await channel.send(flirt)
        log.info(f"Flirted with {message.author.name} after their reply")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        if member.bot:
            return

        channel = self._get_goodbye_channel(member.guild)
        if channel is None:
            log.warning(f"No goodbye channel found for {member.guild.name}")
            return

        goodbye = random.choice(_GOODBYE_MESSAGES).format(name=member.display_name)
        await channel.send(goodbye)
        log.info(f"Sent goodbye message for {member.name} in {channel.name}")
