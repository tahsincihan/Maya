import discord
from discord.ext import commands

from help_content import HELP_CATEGORIES, HELP_EXAMPLES, HELP_TIPS


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="helpmaya", aliases=["help", "commands", "bothelp"])
    async def help_command(self, ctx: commands.Context, *, command_name: str | None = None) -> None:
        """Show the command menu, or details for one command."""
        if command_name:
            await self._send_command_help(ctx, command_name.lstrip("!").strip())
        else:
            await self._send_menu(ctx)

    async def _send_menu(self, ctx: commands.Context) -> None:
        embed = discord.Embed(
            title="Hey, I'm Maya 👋",
            description="Here's what I can do. Type `!helpmaya <command>` for more on any of them.",
            color=discord.Color.blurple(),
        )
        listed: set[str] = set()
        for category, entries in HELP_CATEGORIES:
            lines = []
            for name, summary in entries:
                if self.bot.get_command(name):
                    lines.append(f"`!{name}` · {summary}")
                    listed.add(name)
            if lines:
                embed.add_field(name=category, value="\n".join(lines), inline=False)

        # Any command not yet placed in a category still shows up.
        extra = [
            f"`!{c.name}` · {c.short_doc or ''}".rstrip(" ·")
            for c in sorted(self.bot.commands, key=lambda c: c.name)
            if not c.hidden and c.name not in listed and c.name != "helpmaya"
        ]
        if extra:
            embed.add_field(name="✨ More", value="\n".join(extra), inline=False)

        embed.set_footer(text="Prediction game: !fixtures → !predict <id> home|away|draw → !leaderboard")
        await ctx.send(embed=embed)

    async def _send_command_help(self, ctx: commands.Context, command_name: str) -> None:
        command = self.bot.get_command(command_name)
        if not command or command.hidden:
            await ctx.send(f"❌ I don't know `!{command_name}`. Try `!helpmaya` to see everything.")
            return

        name = command.name
        embed = discord.Embed(
            title=f"!{name}",
            description=command.short_doc or "No description yet.",
            color=discord.Color.blurple(),
        )
        usage = f"!{name} {command.signature}".strip()
        embed.add_field(name="How to use", value=f"`{usage}`", inline=False)
        if name in HELP_TIPS:
            embed.add_field(name="Tip", value=HELP_TIPS[name], inline=False)
        if name in HELP_EXAMPLES:
            embed.add_field(name="Example", value=f"```\n{HELP_EXAMPLES[name]}\n```", inline=False)
        if command.aliases:
            embed.set_footer(text="Also works: " + ", ".join(f"!{a}" for a in command.aliases))
        await ctx.send(embed=embed)
