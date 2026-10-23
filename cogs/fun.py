"""!banter: Maya teases fans before the next game."""

import os
import random
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands

from config import COMPETITIONS, FOOTBALL_DATA_BASE_URL, FOOTBALL_TEAMS
from helpers import _fetch_football_data, _format_kickoff, _matches_role_name, _parse_utc_date

_UNDERDOG_TEASES = [
    "{team} fans, prepare your excuses 😌",
    "{team} fans already drafting the 'the ref was against us' tweet 📝",
    "{team} fans, it's not too late to switch off the TV 🙈",
    "{team} fans are about to learn the meaning of suffering 🥲",
]
_FAVOURITE_TEASES = [
    "{team} fans acting confident like last week didn't happen 🤭",
    "{team} fans, don't celebrate before the final whistle this time 🙃",
    "{team} fans, I've seen your defence. I'd be nervous 😬",
    "{team} fans already planning the parade, adorable 🎉",
]
_OPPONENT_TEASES = [
    "{opponent} have no idea what's about to hit them. or maybe {team} don't 😏",
    "honestly {opponent} could ruin {team}'s whole weekend and I'd find it funny 😈",
]


class FunCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="banter", help="Maya teases fans before the next big game", usage="[team]")
    async def banter(self, ctx: commands.Context, *, team: str | None = None) -> None:
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return
        token = os.getenv("FOOTBALL_DATA_TOKEN")
        if not token:
            await ctx.send("❌ FOOTBALL_DATA_TOKEN is not set. Add it to your .env file.")
            return

        # Only tease teams this server actually has fans of.
        supported = []
        for name in FOOTBALL_TEAMS:
            role = discord.utils.get(ctx.guild.roles, name=name)
            if role and any(not m.bot for m in role.members):
                supported.append(role)
        if team:
            supported = [r for r in supported if team.lower() in r.name.lower()]
            if not supported:
                await ctx.send(f"❌ Nobody here supports a team matching `{team}`.")
                return
        if not supported:
            await ctx.send("❌ Nobody has a team role yet, so there's no one to tease 😔")
            return

        today = datetime.now(timezone.utc).date()
        url = (
            f"{FOOTBALL_DATA_BASE_URL}/matches"
            f"?competitions={','.join(COMPETITIONS)}"
            f"&status=SCHEDULED,TIMED"
            f"&dateFrom={today.isoformat()}&dateTo={(today + timedelta(days=7)).isoformat()}"
        )
        async with ctx.typing():
            try:
                payload = await _fetch_football_data(url, token)
            except Exception as exc:
                await ctx.send(f"❌ Couldn't get fixtures: {exc}")
                return

        best = None
        for match in payload.get("matches", []):
            sides = []
            for side in ("homeTeam", "awayTeam"):
                role = next((r for r in supported if _matches_role_name(r.name, match.get(side, {}))), None)
                sides.append(role)
            if any(sides):
                kickoff = _parse_utc_date(match.get("utcDate")) or datetime.max.replace(tzinfo=timezone.utc)
                if best is None or kickoff < best[0]:
                    best = (kickoff, match, sides)

        if best is None:
            await ctx.send("😴 None of our teams play in the next 7 days. Nothing to tease... yet.")
            return

        _, match, (home_role, away_role) = best
        home_name = match["homeTeam"].get("shortName") or match["homeTeam"].get("name", "Home")
        away_name = match["awayTeam"].get("shortName") or match["awayTeam"].get("name", "Away")

        lines = []
        if home_role and away_role:
            underdog, favourite = random.sample([home_role, away_role], 2)
            lines.append(random.choice(_UNDERDOG_TEASES).format(team=underdog.mention))
            lines.append(random.choice(_FAVOURITE_TEASES).format(team=favourite.mention))
        else:
            role = home_role or away_role
            opponent = away_name if home_role else home_name
            lines.append(random.choice(_UNDERDOG_TEASES + _FAVOURITE_TEASES).format(team=role.mention))
            lines.append(random.choice(_OPPONENT_TEASES).format(team=role.name, opponent=opponent))

        kickoff_text = _format_kickoff(match.get("utcDate"))
        embed = discord.Embed(
            title=f"🔥 {home_name} vs {away_name}",
            description="\n".join(lines),
            color=discord.Color.orange(),
        )
        if kickoff_text:
            embed.add_field(name="Kick-off", value=kickoff_text, inline=True)
        if match.get("id"):
            embed.add_field(name="Predict it", value=f"`!predict {match['id']} home|away|draw`", inline=True)
        await ctx.send(embed=embed)
