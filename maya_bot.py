import logging
import os
import sys

from dotenv import load_dotenv
import discord
from discord.ext import commands

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)

from cogs.football import FootballCog
from cogs.help import HelpCog
from cogs.predictions import PredictionsCog
from cogs.roles import RolesCog
from cogs.voice import VoiceCog
from cogs.welcome import WelcomeCog
from keep_alive import keep_alive

# Bot setup with necessary intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True
intents.presences = True

class MayaBot(commands.Bot):
    async def setup_hook(self) -> None:
        await self.add_cog(HelpCog(self))
        await self.add_cog(RolesCog(self))
        await self.add_cog(FootballCog(self))
        await self.add_cog(PredictionsCog(self))
        await self.add_cog(VoiceCog(self))
        await self.add_cog(WelcomeCog(self))


bot = MayaBot(command_prefix="!", intents=intents, help_command=None)


log = logging.getLogger(__name__)

@bot.event
async def on_ready() -> None:
    log.info(f"Logged in as {bot.user} | Guilds: {len(bot.guilds)}")


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument. Use `!helpmaya {ctx.command}` for usage information.")
        return
    await ctx.send(f"❌ An error occurred: {str(error)}")


if __name__ == "__main__":
    load_dotenv()
    token = os.getenv("DISCORD_BOT_TOKEN")

    if not token:
        print("ERROR: DISCORD_BOT_TOKEN environment variable not set!")
        print("Please set your bot token before running.")
    else:
        # Start keep-alive web server for hosting
        keep_alive()
        bot.run(token)
