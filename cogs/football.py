import os
from datetime import datetime

import discord
from discord.ext import commands

from config import COMPETITIONS, FOOTBALL_DATA_BASE_URL, FOOTBALL_TEAMS
from helpers import (
    _fetch_football_data,
    _format_fixture_line,
    _format_result_line,
    _matches_role_name,
    _parse_utc_date,
    _resolve_competition,
)


class FootballCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(
        name="myteam",
        aliases=["myfixtures", "mygames"],
        help="Show upcoming fixtures for your team roles",
    )
    async def my_team(self, ctx: commands.Context) -> None:
        """
        Show upcoming fixtures for the teams you have as roles.
        Usage: !myteam
        """
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        token = os.getenv("FOOTBALL_DATA_TOKEN")
        if not token:
            await ctx.send("❌ FOOTBALL_DATA_TOKEN is not set. Add it to your .env file.")
            return

        member = ctx.author
        user_team_roles = []
        for team_name in FOOTBALL_TEAMS:
            role = discord.utils.get(ctx.guild.roles, name=team_name)
            if role and role in member.roles:
                user_team_roles.append(role)

        if not user_team_roles:
            await ctx.send(
                "❌ You don't have any team roles from the tracked list. "
                f"Tracked teams: {', '.join(FOOTBALL_TEAMS)}"
            )
            return

        competition_teams = []
        for competition_code, competition_name in COMPETITIONS.items():
            try:
                teams_payload = await _fetch_football_data(
                    f"{FOOTBALL_DATA_BASE_URL}/competitions/{competition_code}/teams",
                    token,
                )
            except Exception as exc:
                await ctx.send(f"❌ {competition_name} API error: {exc}")
                return

            teams = teams_payload.get("teams", [])
            if teams:
                competition_teams.append(
                    {
                        "code": competition_code,
                        "name": competition_name,
                        "teams": teams,
                    }
                )

        if not competition_teams:
            await ctx.send("❌ No teams returned from the API.")
            return

        fixtures_by_team = []
        unmatched = []
        for role in user_team_roles:
            team = None
            competition_code = None
            competition_name = None
            for competition in competition_teams:
                match = next(
                    (t for t in competition["teams"] if _matches_role_name(role.name, t)),
                    None,
                )
                if match:
                    team = match
                    competition_code = competition["code"]
                    competition_name = competition["name"]
                    break

            if not team or not competition_code or not competition_name:
                unmatched.append(role.name)
                continue

            team_id = team.get("id")
            if not team_id:
                unmatched.append(role.name)
                continue

            try:
                matches_payload = await _fetch_football_data(
                    f"{FOOTBALL_DATA_BASE_URL}/teams/{team_id}/matches"
                    f"?competitions={competition_code}"
                    f"&status=SCHEDULED,TIMED"
                    f"&limit=30",
                    token,
                )
            except Exception as exc:
                await ctx.send(f"❌ {competition_name} API error: {exc}")
                return

            matches = matches_payload.get("matches", [])
            matches.sort(key=lambda match: _parse_utc_date(match.get("utcDate")) or datetime.max)
            fixtures_by_team.append((role, competition_name, matches[:5]))

        if not fixtures_by_team:
            await ctx.send("❌ No fixtures found for your teams.")
            return

        embed = discord.Embed(
            title="📅 Your Team Fixtures",
            description="Next 5 fixtures with match IDs",
            color=discord.Color.dark_teal(),
        )

        for role, competition_name, matches in fixtures_by_team:
            if matches:
                lines = []
                for match in matches:
                    match_id = match.get("id")
                    line = _format_fixture_line(match, ctx.guild)
                    if match_id:
                        line = f"`{match_id}` • {line}"
                    lines.append(line)
            else:
                lines = ["No upcoming fixtures found."]

            embed.add_field(
                name=f"{role.mention} fixtures ({competition_name})",
                value="\n".join(lines),
                inline=False,
            )

        if unmatched:
            embed.set_footer(text=f"No API match for: {', '.join(unmatched)}")

        await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))

    @commands.command(
        name="fixtures",
        aliases=["plfixtures"],
        help="Show upcoming fixtures for a matchweek (league optional)",
    )
    async def fixtures(self, ctx: commands.Context, league: str | None = None, matchday: int | None = None) -> None:
        """
        Show fixtures for a matchweek.
        Usage: !fixtures [league] [matchday]
        """
        token = os.getenv("FOOTBALL_DATA_TOKEN")
        if not token:
            await ctx.send("❌ FOOTBALL_DATA_TOKEN is not set. Add it to your .env file.")
            return

        if league and league.isdigit() and matchday is None:
            matchday = int(league)
            league = None

        competition = _resolve_competition(league)
        if not competition:
            leagues = ", ".join(f"{code} ({name})" for code, name in COMPETITIONS.items())
            await ctx.send(f"❌ Unknown league. Supported leagues: {leagues}")
            return

        league_code, league_name = competition

        try:
            if matchday is None:
                competition = await _fetch_football_data(
                    f"{FOOTBALL_DATA_BASE_URL}/competitions/{league_code}",
                    token,
                )
                current_matchday = competition.get("currentSeason", {}).get("currentMatchday")
                if not current_matchday:
                    await ctx.send(f"❌ Unable to determine the current {league_name} matchweek.")
                    return

                matchday = current_matchday
                matches_payload = await _fetch_football_data(
                    f"{FOOTBALL_DATA_BASE_URL}/competitions/{league_code}/matches?matchday={matchday}",
                    token,
                )
                matches = matches_payload.get("matches", [])
                if matches and all(m.get("status") == "FINISHED" for m in matches):
                    matchday += 1
                    matches_payload = await _fetch_football_data(
                        f"{FOOTBALL_DATA_BASE_URL}/competitions/{league_code}/matches?matchday={matchday}",
                        token,
                    )
                    matches = matches_payload.get("matches", [])
            else:
                matches_payload = await _fetch_football_data(
                    f"{FOOTBALL_DATA_BASE_URL}/competitions/{league_code}/matches?matchday={matchday}",
                    token,
                )
                matches = matches_payload.get("matches", [])
        except Exception as exc:
            await ctx.send(f"❌ {league_name} API error: {exc}")
            return

        if not matches:
            await ctx.send(f"❌ No matches found for {league_name} matchweek {matchday}.")
            return

        fixtures = [match for match in matches if match.get("status") in {"SCHEDULED", "TIMED"}]
        if not fixtures:
            fixtures = matches

        embed = discord.Embed(
            title=f"🗓️ {league_name} Matchweek {matchday} Fixtures",
            description="Use the match ID to predict: home/away/draw",
            color=discord.Color.dark_green(),
        )

        for match in fixtures:
            match_id = match.get("id")
            line = _format_fixture_line(match, ctx.guild)
            embed.add_field(name=f"Match ID {match_id}", value=line, inline=False)

        await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))

    @commands.command(
        name="results",
        aliases=["plweek", "matchweek"],
        help="Show matchweek results (league optional)",
    )
    async def results(self, ctx: commands.Context, league: str | None = None, matchday: int | None = None) -> None:
        """
        Show matchweek results and fixtures.
        Usage: !results [league] [matchday]
        """
        token = os.getenv("FOOTBALL_DATA_TOKEN")
        if not token:
            await ctx.send("❌ FOOTBALL_DATA_TOKEN is not set. Add it to your .env file.")
            return

        if league and league.isdigit() and matchday is None:
            matchday = int(league)
            league = None

        competition = _resolve_competition(league)
        if not competition:
            leagues = ", ".join(f"{code} ({name})" for code, name in COMPETITIONS.items())
            await ctx.send(f"❌ Unknown league. Supported leagues: {leagues}")
            return

        league_code, league_name = competition

        try:
            if matchday is None:
                competition = await _fetch_football_data(
                    f"{FOOTBALL_DATA_BASE_URL}/competitions/{league_code}",
                    token,
                )
                current_matchday = competition.get("currentSeason", {}).get("currentMatchday")
                if not current_matchday:
                    await ctx.send(f"❌ Unable to determine the current {league_name} matchweek.")
                    return

                matchday = current_matchday
                matches_payload = await _fetch_football_data(
                    f"{FOOTBALL_DATA_BASE_URL}/competitions/{league_code}/matches?matchday={matchday}",
                    token,
                )
                matches = matches_payload.get("matches", [])
                if matches and all(m.get("status") in {"SCHEDULED", "TIMED"} for m in matches):
                    if matchday > 1:
                        matchday -= 1
                        matches_payload = await _fetch_football_data(
                            f"{FOOTBALL_DATA_BASE_URL}/competitions/{league_code}/matches?matchday={matchday}",
                            token,
                        )
                        matches = matches_payload.get("matches", [])
            else:
                matches_payload = await _fetch_football_data(
                    f"{FOOTBALL_DATA_BASE_URL}/competitions/{league_code}/matches?matchday={matchday}",
                    token,
                )
                matches = matches_payload.get("matches", [])
        except Exception as exc:
            await ctx.send(f"❌ {league_name} API error: {exc}")
            return

        if not matches:
            await ctx.send(f"❌ No matches found for {league_name} matchweek {matchday}.")
            return

        embed = discord.Embed(
            title=f"🏆 {league_name} Matchweek {matchday}",
            description="Latest results and fixtures",
            color=discord.Color.gold(),
        )

        for match in matches:
            match_name, line = _format_result_line(match, ctx.guild)
            embed.add_field(name=match_name, value=line, inline=False)

        await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))
