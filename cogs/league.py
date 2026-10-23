"""Me & The Boys League: members earn their team's real league points (W=3, D=1, L=0)."""

import asyncio
import json
import logging
import os
import unicodedata
from datetime import datetime, time, timezone

import discord
from discord.ext import commands, tasks

from config import COMPETITIONS, FOOTBALL_DATA_BASE_URL, FOOTBALL_TEAMS, LEAGUE_FILE, LEAGUE_NAME
from cogs.league_view import PAGE_SIZE, LeagueData, LeagueView, points as _points, teams_embed
from helpers import _fetch_football_data, _matches_role_name

log = logging.getLogger(__name__)

# Checked nightly, after the last European kick-offs have finished.
POST_TIME = time(hour=23, minute=30, tzinfo=timezone.utc)
# Reuse fetched standings for this long, so button clicks stay fast and API calls stay low.
STANDINGS_MAX_AGE = 30 * 60
LIVE_ID = "maya_league"


def _load_state() -> dict:
    try:
        with open(LEAGUE_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    data.setdefault("guilds", {})
    return data


def _save_state(state: dict) -> None:
    with open(LEAGUE_FILE, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)


def _team_records(guild: discord.Guild, standings: list[dict]) -> dict[str, dict]:
    """Season record for each tracked team that has a role with members in this guild."""
    records = {}
    for team_name in FOOTBALL_TEAMS:
        role = discord.utils.get(guild.roles, name=team_name)
        if role is None or not any(not m.bot for m in role.members):
            continue
        row = next((r for r in standings if _matches_role_name(team_name, r.get("team", {}))), None)
        if row is None:
            continue
        records[team_name] = {
            "played": row.get("playedGames", 0),
            "won": row.get("won", 0),
            "draw": row.get("draw", 0),
            "lost": row.get("lost", 0),
            "gd": row.get("goalDifference", 0),
            "gf": row.get("goalsFor", 0),
            "competition": row.get("competition", ""),
        }
    return records


def _ranked_rows(guild: discord.Guild, records: dict[str, dict]) -> list[tuple[int, discord.Member, str, dict]]:
    """One row per supporter and team. Teams are ranked 1, 2, 3...; every fan shares their team's position."""
    team_order = sorted(
        records,
        key=lambda t: (-_points(records[t]), -records[t]["gd"], -records[t]["gf"], t),
    )
    ranked = []
    position = 0
    for team_name in team_order:
        role = discord.utils.get(guild.roles, name=team_name)
        fans = sorted((m for m in role.members if not m.bot), key=lambda m: unicodedata.normalize("NFKC", m.display_name).lower())
        if not fans:
            continue
        position += 1
        ranked.extend((position, member, team_name, records[team_name]) for member in fans)
    return ranked


def _recap_lines(records: dict[str, dict], last_seen: dict[str, dict]) -> list[str]:
    """What each team did since the last post."""
    lines = []
    for team_name, record in records.items():
        before = last_seen.get(team_name)
        if not before or record["played"] <= before["played"]:
            continue
        won = record["won"] - before["won"]
        draw = record["draw"] - before["draw"]
        lost = record["lost"] - before["lost"]
        gained = won * 3 + draw
        if won + draw + lost == 1:
            text = "✅ won" if won else ("➖ drew" if draw else "❌ lost")
            lines.append(f"{text} · **{team_name}** (+{gained})")
        else:
            lines.append(f"📊 **{team_name}** {won}W {draw}D {lost}L (+{gained})")
    return lines


def _snapshot(records: dict[str, dict]) -> dict[str, dict]:
    return {
        team: {key: rec[key] for key in ("played", "won", "draw", "lost")}
        for team, rec in records.items()
    }


def _live_embed(data: LeagueData | None) -> discord.Embed:
    """The pinned table. Shows the teams; buttons open each person's own view."""
    if data is None:
        embed = discord.Embed(
            title=f"🏆 {LEAGUE_NAME}",
            description="Nobody is in the league yet. Grab a team role to join! ⚽",
            color=discord.Color.gold(),
        )
    else:
        embed = teams_embed(data)
        embed.description = (
            f"{embed.description}\n\n🔄 I update this after every matchday. "
            "Use the buttons to see the fans or find yourself."
        )[:4096]
    embed.timestamp = datetime.now(timezone.utc)
    footer = embed.footer.text + " · " if embed.footer.text else ""
    embed.set_footer(text=f"{footer}Last updated")
    return embed


class LiveTableView(discord.ui.View):
    """Buttons under the pinned live table. They keep working after restarts,
    and each click opens a private copy for whoever pressed it."""

    def __init__(self, cog: "LeagueCog", data: LeagueData | None = None) -> None:
        super().__init__(timeout=None)
        self.cog = cog
        options = []
        if data:
            for i, team in enumerate(data.teams[:25], 1):
                count = len(data.fans[team])
                options.append(discord.SelectOption(
                    label=f"#{i} {team}", value=team, emoji="⚽",
                    description=f"{count} fan{'s' if count != 1 else ''} · {_points(data.records[team])} pts",
                ))
        if not options:
            options = [discord.SelectOption(label="No teams yet", value="__none__")]
        self.team_menu = discord.ui.Select(
            custom_id=f"{LIVE_ID}:team", placeholder="⚽ See one team's fans…", options=options, row=1
        )
        self.team_menu.callback = self._on_team
        self.add_item(self.team_menu)

    @discord.ui.button(label="Fans", emoji="👥", style=discord.ButtonStyle.secondary, custom_id=f"{LIVE_ID}:fans", row=0)
    async def fans(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.cog.open_private(interaction, LeagueView.FANS)

    @discord.ui.button(label="Find me", emoji="📍", style=discord.ButtonStyle.success, custom_id=f"{LIVE_ID}:me", row=0)
    async def find_me(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.cog.open_private(interaction, "me")

    async def _on_team(self, interaction: discord.Interaction) -> None:
        await self.cog.open_private(interaction, self.team_menu.values[0])


class LeagueCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.state = _load_state()
        self._standings: list[dict] | None = None
        self._standings_at: datetime | None = None
        self._standings_lock = asyncio.Lock()
        self.last_pin_failed = False
        self.matchday_post.start()

    async def cog_load(self) -> None:
        # Lets the pinned table's buttons work again after a restart.
        self.bot.add_view(LiveTableView(self))

    def cog_unload(self) -> None:
        self.matchday_post.cancel()

    async def _fetch_standings(self, token: str) -> list[dict]:
        rows = []
        for code, name in COMPETITIONS.items():
            payload = await _fetch_football_data(f"{FOOTBALL_DATA_BASE_URL}/competitions/{code}/standings", token)
            for standing in payload.get("standings", []):
                if standing.get("type") == "TOTAL":
                    rows.extend({**row, "competition": name} for row in standing.get("table", []))
        return rows

    async def _get_standings(self, max_age: float = STANDINGS_MAX_AGE) -> list[dict]:
        token = os.getenv("FOOTBALL_DATA_TOKEN")
        if not token:
            raise RuntimeError("FOOTBALL_DATA_TOKEN is not set. Add it to your .env file.")
        async with self._standings_lock:
            now = datetime.now(timezone.utc)
            fresh = self._standings_at and (now - self._standings_at).total_seconds() < max_age
            if self._standings is None or not fresh:
                self._standings = await self._fetch_standings(token)
                self._standings_at = now
            return self._standings

    async def _league_data(self, guild: discord.Guild, max_age: float = STANDINGS_MAX_AGE) -> LeagueData | None:
        records = _team_records(guild, await self._get_standings(max_age))
        ranked = _ranked_rows(guild, records)
        return LeagueData(ranked, records) if ranked else None

    async def open_private(self, interaction: discord.Interaction, target: str) -> None:
        """Answer a click on the live table with a private, browsable copy."""
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            data = await self._league_data(interaction.guild)
        except Exception:
            log.exception("Could not load league for a live-table click")
            await interaction.followup.send("❌ I couldn't load the table right now. Try again in a minute.", ephemeral=True)
            return
        if data is None:
            await interaction.followup.send("Nobody is in the league yet. Grab a team role to join! ⚽", ephemeral=True)
            return

        view = LeagueView(data, owner_id=interaction.user.id)
        if target == "me":
            rows = data.rows_for(interaction.user.id)
            if not rows:
                await interaction.followup.send("You're not in the league yet. Grab a team role to join! ⚽", ephemeral=True)
                return
            view.mode, view.page = LeagueView.FANS, rows[0][0] // PAGE_SIZE
        elif target == LeagueView.FANS or target in data.fans:
            view.mode = target
        else:
            await interaction.followup.send("That team has no fans right now.", ephemeral=True)
            return
        view._update_controls()
        view.message = await interaction.followup.send(
            embed=view.current_embed(), view=view, ephemeral=True, wait=True
        )

    async def _update_live_table(
        self, guild: discord.Guild, guild_state: dict, data: LeagueData | None, recap: list[str] | None = None
    ) -> discord.abc.Snowflake | None:
        """Edit the pinned table (or post a new one if it was deleted). Returns the table message."""
        channel = guild.get_channel(guild_state.get("channel_id", 0))
        if channel is None:
            return None
        embed, view = _live_embed(data), LiveTableView(self, data)
        message = None
        self.last_pin_failed = False
        if guild_state.get("message_id"):
            try:
                message = channel.get_partial_message(guild_state["message_id"])
                await message.edit(embed=embed, view=view)
            except discord.NotFound:
                message = None
        if message is None:
            message = await channel.send(embed=embed, view=view)
            guild_state["message_id"] = message.id
            try:
                await message.pin(reason=f"{LEAGUE_NAME} live table")
                self.last_pin_failed = False
            except discord.HTTPException as exc:
                self.last_pin_failed = True
                log.warning(f"Could not pin the league table in {guild.name}: {exc}")
        if recap:
            recap_embed = discord.Embed(
                title="📣 Matchday results are in!",
                description="\n".join(recap)[:3900] + f"\n\n[📊 See the updated table]({message.jump_url})",
                color=discord.Color.gold(),
            )
            await channel.send(embed=recap_embed)
        return message

    @commands.command(name="league", aliases=["boys", "supporters", "fanleague"], help="The Me & The Boys League table")
    async def league(self, ctx: commands.Context) -> None:
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return
        async with ctx.typing():
            try:
                data = await self._league_data(ctx.guild, max_age=10 * 60)
            except Exception as exc:
                await ctx.send(f"❌ Couldn't get league standings: {exc}")
                return
        if data is None:
            await ctx.send(
                "❌ Nobody is in the league yet. Grab a team role to join! "
                f"Teams: {', '.join(FOOTBALL_TEAMS)}"
            )
            return
        view = LeagueView(data, owner_id=ctx.author.id)
        view.message = await ctx.send(embed=view.current_embed(), view=view)

    @commands.command(
        name="leaguetable",
        aliases=["leaguechannel"],
        help="Post a pinned league table that Maya updates after every matchday",
        usage="[#channel | refresh | off]",
    )
    @commands.has_permissions(manage_guild=True)
    async def league_table(self, ctx: commands.Context, *, option: str | None = None) -> None:
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return
        guild_state = self.state["guilds"].setdefault(str(ctx.guild.id), {})
        choice = (option or "").strip().lower()
        old_channel = ctx.guild.get_channel(guild_state.get("channel_id", 0))
        old_message = (
            old_channel.get_partial_message(guild_state["message_id"])
            if old_channel and guild_state.get("message_id") else None
        )

        if choice == "off":
            if old_message:
                try:
                    await old_message.edit(view=None)
                except discord.HTTPException:
                    pass
            guild_state.pop("channel_id", None)
            guild_state.pop("message_id", None)
            _save_state(self.state)
            await ctx.send("🔕 Stopped. The last table stays where it is, but I won't update it anymore.")
            return

        if choice == "refresh":
            if not old_channel:
                await ctx.send("❌ There's no live table yet. Use `!leaguetable #channel` to set one up.")
                return
            async with ctx.typing():
                try:
                    data = await self._league_data(ctx.guild, max_age=0)
                    message = await self._update_live_table(ctx.guild, guild_state, data)
                except Exception as exc:
                    await ctx.send(f"❌ Couldn't update the table: {exc}")
                    return
            _save_state(self.state)
            await ctx.send(f"🔄 Table updated: {message.jump_url}")
            return

        channel = ctx.channel
        if option:
            try:
                channel = await commands.TextChannelConverter().convert(ctx, option.strip())
            except commands.BadArgument:
                await ctx.send(f"❌ I can't find the channel `{option}`.")
                return
        perms = channel.permissions_for(ctx.guild.me)
        if not (perms.send_messages and perms.embed_links):
            await ctx.send(f"❌ I need Send Messages and Embed Links in {channel.mention}.")
            return

        async with ctx.typing():
            try:
                standings = await self._get_standings(max_age=0)
            except Exception as exc:
                await ctx.send(f"❌ Couldn't get league standings: {exc}")
                return
            records = _team_records(ctx.guild, standings)
            ranked = _ranked_rows(ctx.guild, records)
            data = LeagueData(ranked, records) if ranked else None

            # Replace the old live table, if there was one.
            if old_message:
                try:
                    await old_message.delete()
                except discord.HTTPException:
                    pass
            guild_state["channel_id"] = channel.id
            guild_state.pop("message_id", None)
            # Remember where every team stands now, so the first recap shows only new results.
            guild_state["last_seen"] = _snapshot(records)
            message = await self._update_live_table(ctx.guild, guild_state, data)
            _save_state(self.state)

        note = (
            "\n⚠️ I couldn't pin it. Give me the **Pin Messages** permission in that channel, or pin it yourself."
            if self.last_pin_failed else ""
        )
        await ctx.send(
            f"📌 Live {LEAGUE_NAME} table posted in {channel.mention}. "
            f"I'll update it after every matchday and post a short recap.{note}\n{message.jump_url}"
        )

    @tasks.loop(time=POST_TIME)
    async def matchday_post(self) -> None:
        targets = []
        for guild_id, guild_state in self.state["guilds"].items():
            guild = self.bot.get_guild(int(guild_id))
            if guild and guild.get_channel(guild_state.get("channel_id", 0)):
                targets.append((guild, guild_state))
        if not targets:
            return
        try:
            standings = await self._get_standings(max_age=0)
        except Exception:
            log.exception("Matchday league check failed")
            return

        for guild, guild_state in targets:
            records = _team_records(guild, standings)
            recap = _recap_lines(records, guild_state.get("last_seen", {}))
            guild_state["last_seen"] = _snapshot(records)
            ranked = _ranked_rows(guild, records)
            data = LeagueData(ranked, records) if ranked else None
            try:
                await self._update_live_table(guild, guild_state, data, recap)
                log.info(f"Updated live league table in {guild.name}")
            except discord.HTTPException:
                log.exception(f"Could not update live league table in {guild.name}")
        _save_state(self.state)

    @matchday_post.before_loop
    async def _wait_until_ready(self) -> None:
        await self.bot.wait_until_ready()
