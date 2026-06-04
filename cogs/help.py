import discord
from discord.ext import commands

from help_content import HELP_DETAILS, HELP_EXAMPLES


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="helpmaya", aliases=["help", "commands", "bothelp"])
    async def help_command(self, ctx: commands.Context, *, command_name: str | None = None) -> None:
        """
        Show command help.
        Usage: !helpmaya [command]
        """
        if command_name:
            command = self.bot.get_command(command_name)
            if not command or command.hidden:
                await ctx.send(f'❌ Command "{command_name}" not found.')
                return

            description = command.help or command.short_doc or "No description provided."
            detail = HELP_DETAILS.get(command.name)
            usage = f"!{command.qualified_name} {command.signature}".strip()
            embed = discord.Embed(
                title=f"Help: !{command.qualified_name}",
                description=description,
                color=discord.Color.blurple(),
            )
            embed.add_field(name="Usage", value=f"`{usage}`", inline=False)
            if detail:
                embed.add_field(name="Details", value=detail, inline=False)
            if command.aliases:
                aliases = ", ".join(f"!{alias}" for alias in command.aliases)
                embed.add_field(name="Aliases", value=aliases, inline=False)
            example = HELP_EXAMPLES.get(command.name)
            if example:
                embed.add_field(name="Example", value=f"```\n{example}\n```", inline=False)
            await ctx.send(embed=embed)
            return

        commands_list = sorted(
            [command for command in self.bot.commands if not command.hidden],
            key=lambda command: command.name,
        )
        embed = discord.Embed(
            title="📖 Bot Commands",
            description="Use `!helpmaya <command>` for details.",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="🎯 Prediction Game",
            value=(
                "1) Get match IDs: `!fixtures` or `!myteam`\n"
                "2) Predict: `!predict <match_id> home|away|draw`\n"
                "3) Check picks: `!mypicks`\n"
                "4) See scores: `!leaderboard`\n"
                "Scoring: 1 pt per correct outcome."
            ),
            inline=False,
        )
        for command in commands_list:
            description = command.help or command.short_doc or "No description provided."
            detail = HELP_DETAILS.get(command.name)
            usage = f"!{command.qualified_name} {command.signature}".strip()
            value = f"{description}\nUsage: `{usage}`"
            if detail:
                value = f"{value}\nDetails: {detail}"
            if command.aliases:
                aliases = ", ".join(f"!{alias}" for alias in command.aliases)
                value = f"{value}\nAliases: {aliases}"
            embed.add_field(name=f"!{command.qualified_name}", value=value, inline=False)

        await ctx.send(embed=embed)
