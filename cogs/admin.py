"""Admin tools: run a fun command from an admin channel and have Maya post it somewhere else."""

import copy

import discord
from discord.ext import commands

from config import SENDTO_COMMANDS


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(
        name="sendto",
        aliases=["post"],
        help="Run a fun command here, Maya posts the result in another channel (admins)",
        usage="#channel <command> [details]",
    )
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def send_to(self, ctx: commands.Context, channel: discord.TextChannel, *, command_text: str) -> None:
        prefix = ctx.prefix or "!"
        command_text = command_text.strip()
        if command_text.startswith(prefix):
            command_text = command_text[len(prefix):].lstrip()

        name = command_text.split(maxsplit=1)[0].lower() if command_text else ""
        command = self.bot.get_command(name)
        allowed = sorted(SENDTO_COMMANDS)
        if command is None or command.qualified_name not in SENDTO_COMMANDS:
            await ctx.reply(
                f"❌ I can only send fun commands: {', '.join(f'`{c}`' for c in allowed)}",
                mention_author=False,
            )
            return

        perms = channel.permissions_for(ctx.guild.me)
        if not (perms.view_channel and perms.send_messages and perms.embed_links):
            await ctx.reply(f"❌ I need to see, send messages and embed links in {channel.mention}.", mention_author=False)
            return

        # Re-run the command as if it was typed in the target channel, so Maya replies there.
        message = copy.copy(ctx.message)
        message.channel = channel
        message.content = f"{prefix}{command_text}"
        target_ctx = await self.bot.get_context(message, cls=type(ctx))
        if target_ctx.command is None:
            await ctx.reply("❌ I couldn't understand that command.", mention_author=False)
            return

        try:
            await target_ctx.command.invoke(target_ctx)
        except commands.MissingRequiredArgument as exc:
            await ctx.reply(
                f"❌ Missing `{exc.param.name}`. Try `!helpmaya {command.qualified_name}`.", mention_author=False
            )
            return
        except commands.CommandError as exc:
            original = getattr(exc, "original", exc)
            await ctx.reply(f"❌ That didn't work: {original}", mention_author=False)
            return

        await ctx.reply(f"💌 Sent `{prefix}{command_text}` in {channel.mention}", mention_author=False)
