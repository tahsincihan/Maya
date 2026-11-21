"""How the Me & The Boys League looks in Discord: tables, pages, buttons and the team menu."""

import itertools
import math
import unicodedata

import discord

from config import LEAGUE_NAME, TEAM_CODES

PAGE_SIZE = 15
NAME_WIDTH = 12
MEDALS = ["🥇", "🥈", "🥉"]
RULES = "Win 3 · Draw 1 · Loss 0"


def points(record: dict) -> int:
    return record["won"] * 3 + record["draw"]


def _code(team: str) -> str:
    """Short club code for the table, e.g. MUN."""
    return TEAM_CODES.get(team) or _fit(team, 3).upper()


def _fit(text: str, width: int) -> str:
    """Trim text to a fixed width, dropping emoji and wide characters so the table stays aligned."""
    clean = "".join(
        ch for ch in unicodedata.normalize("NFKC", text)
        if ch.isprintable()
        and not unicodedata.combining(ch)
        and unicodedata.category(ch) != "So"
        and unicodedata.east_asian_width(ch) not in ("W", "F")
        and ord(ch) <= 0xFFFF
    )
    clean = " ".join(clean.replace("`", "'").split())
    return clean if len(clean) <= width else clean[: width - 1] + "…"


def _fan_name(member: discord.Member) -> str:
    """Nickname if it can be shown in the table, else their username."""
    for name in (member.display_name, getattr(member, "global_name", None), getattr(member, "name", None)):
        if name and len(_fit(name, NAME_WIDTH)) >= 2:
            return _fit(name, NAME_WIDTH)
    return "?"


def _plural(count: int, word: str) -> str:
    return f"{count} {word}{'s' if count != 1 else ''}"


def _table(lines: list[str]) -> str:
    return "```\n" + "\n".join(lines) + "\n```"


class LeagueData:
    """The ranked table plus per-team groupings, ready to display."""

    def __init__(self, ranked: list[tuple[int, discord.Member, str, dict]], records: dict[str, dict]) -> None:
        self.ranked = ranked
        self.records = records
        self.fans: dict[str, list[discord.Member]] = {}
        for _, member, team, _ in ranked:
            self.fans.setdefault(team, []).append(member)
        self.teams = sorted(
            self.fans,
            key=lambda t: (-points(records[t]), -records[t]["gd"], -records[t]["gf"], t),
        )
        self.pages = max(1, math.ceil(len(ranked) / PAGE_SIZE))

    def rows_for(self, member_id: int) -> list[tuple[int, tuple]]:
        """(index in table, row) for each of this member's entries."""
        return [(i, row) for i, row in enumerate(self.ranked) if row[1].id == member_id]

    def team_position(self, team: str) -> int:
        return next(pos for pos, _, t, _ in self.ranked if t == team)


def teams_embed(
    data: LeagueData,
    viewer_id: int | None = None,
    title: str = f"🏆 {LEAGUE_NAME}",
    recap: list[str] | None = None,
) -> discord.Embed:
    my_teams = {team for _, (_, _, team, _) in data.rows_for(viewer_id)} if viewer_id else set()

    podium = [
        f"{medal} **{team}** · {points(data.records[team])} pts"
        for medal, team in zip(MEDALS, data.teams)
    ]
    # 28 characters wide, so it fits a phone screen without wrapping.
    header = f" {'#':>2} {'Team':<4}{'P':>2} {'W':>2} {'D':>2} {'L':>2} {'Pts':>3} {'Fans':>4}"
    rows = [header, "─" * len(header)]
    for i, team in enumerate(data.teams, 1):
        r = data.records[team]
        mark = ">" if team in my_teams else " "
        rows.append(
            f"{mark}{i:>2} {_code(team):<4}{r['played']:>2} {r['won']:>2} {r['draw']:>2} {r['lost']:>2} "
            f"{points(r):>3} {len(data.fans[team]):>4}"
        )
    key = " · ".join(f"{_code(team)} {team}" for team in data.teams if _code(team) != team)
    most = max(data.teams, key=lambda t: len(data.fans[t]))

    parts = ["\n".join(podium), _table(rows)]
    if key:
        parts.append(f"-# {key}")
    extras = f"👑 Biggest fanbase: **{most}** ({_plural(len(data.fans[most]), 'fan')})"
    if my_teams:
        extras += " · `>` your team 💛"
    parts.append(extras)

    embed = discord.Embed(title=title, description="\n".join(parts)[:4096], color=discord.Color.gold())
    if recap:
        embed.add_field(name="This matchday", value="\n".join(recap)[:1024], inline=False)
    embed.set_footer(text=f"{_plural(len(data.teams), 'team')} · {_plural(len(data.ranked), 'fan')} · {RULES}")
    return embed


def fans_embed(data: LeagueData, page: int = 0, viewer_id: int | None = None) -> discord.Embed:
    rows = data.ranked[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]
    header = f" {'#':>2} {'Fan':<{NAME_WIDTH}} {'Team':<4}{'Pts':>4}"
    lines = [header, "─" * len(header)]
    viewer_here = False
    for index, (team, group) in enumerate(itertools.groupby(rows, key=lambda row: row[2])):
        if index:
            lines.append("")  # small gap between teams
        for position, member, _, record in group:
            mark = " "
            if member.id == viewer_id:
                mark, viewer_here = ">", True
            lines.append(f"{mark}{position:>2} {_fan_name(member):<{NAME_WIDTH}} {_code(team):<4}{points(record):>4}")

    parts = ["Every fan shares their team's position.", _table(lines)]
    if viewer_here:
        parts.append("`>` that's you 💛")
    embed = discord.Embed(
        title=f"👥 {LEAGUE_NAME} · Fans", description="\n".join(parts)[:4096], color=discord.Color.gold()
    )
    embed.set_footer(text=f"Page {page + 1}/{data.pages} · {_plural(len(data.ranked), 'fan')} · {RULES}")
    return embed


def team_embed(data: LeagueData, team: str) -> discord.Embed:
    r = data.records[team]
    fans = data.fans[team]
    description = (
        f"**{points(r)} pts** · {r['played']}P {r['won']}W {r['draw']}D {r['lost']}L · GD {r['gd']:+}\n"
        f"Playing in {r.get('competition') or 'their league'}\n\n"
        + (f"The only {team} fan sits" if len(fans) == 1 else f"All {len(fans)} {team} fans sit")
        + f" at **#{data.team_position(team)}** in the {LEAGUE_NAME}."
    )
    embed = discord.Embed(title=f"⚽ {team} fans", description=description, color=discord.Color.gold())
    mentions = ", ".join(m.mention for m in fans)
    if len(mentions) > 1024:
        mentions = mentions[:1000].rsplit(",", 1)[0] + ", …"
    embed.add_field(name=f"Fans ({len(fans)})", value=mentions, inline=False)
    embed.set_footer(text="Press 📊 Teams to go back to the table")
    return embed


class LeagueView(discord.ui.View):
    """Buttons and menu under the !league table."""

    TEAMS = "__teams__"
    FANS = "__fans__"

    def __init__(self, data: LeagueData, owner_id: int, timeout: float = 300) -> None:
        super().__init__(timeout=timeout)
        self.data = data
        self.owner_id = owner_id
        self.mode = self.TEAMS
        self.page = 0
        self.message: discord.Message | None = None

        options = []
        for i, team in enumerate(data.teams[:25], 1):
            count = len(data.fans[team])
            options.append(discord.SelectOption(
                label=f"#{i} {team}", value=team, emoji="⚽",
                description=f"{count} fan{'s' if count != 1 else ''} · {points(data.records[team])} pts",
            ))
        self.menu = discord.ui.Select(placeholder="⚽ See one team's fans…", options=options, row=2)
        self.menu.callback = self._on_menu
        self.add_item(self.menu)
        self._update_controls()

    def current_embed(self) -> discord.Embed:
        if self.mode == self.TEAMS:
            return teams_embed(self.data, viewer_id=self.owner_id)
        if self.mode == self.FANS:
            return fans_embed(self.data, self.page, viewer_id=self.owner_id)
        return team_embed(self.data, self.mode)

    def _update_controls(self) -> None:
        on_fans = self.mode == self.FANS
        self.teams_button.style = discord.ButtonStyle.primary if self.mode == self.TEAMS else discord.ButtonStyle.secondary
        self.fans_button.style = discord.ButtonStyle.primary if on_fans else discord.ButtonStyle.secondary
        self.previous.disabled = not on_fans or self.page == 0
        self.next.disabled = not on_fans or self.page >= self.data.pages - 1
        self.page_label.label = f"{self.page + 1}/{self.data.pages}" if on_fans else "—"
        for option in self.menu.options:
            option.default = option.value == self.mode

    async def _redraw(self, interaction: discord.Interaction) -> None:
        self._update_controls()
        await interaction.response.edit_message(embed=self.current_embed(), view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.owner_id:
            return True
        if (interaction.data or {}).get("custom_id") == self.find_me.custom_id:
            return True
        await interaction.response.send_message(
            "Only the person who opened this table can flip through it. Type `!league` for your own 💛",
            ephemeral=True,
        )
        return False

    @discord.ui.button(label="Teams", emoji="📊", row=0)
    async def teams_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.mode = self.TEAMS
        await self._redraw(interaction)

    @discord.ui.button(label="Fans", emoji="👥", row=0)
    async def fans_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.mode = self.FANS
        await self._redraw(interaction)

    @discord.ui.button(label="Find me", emoji="📍", style=discord.ButtonStyle.success, row=0)
    async def find_me(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        rows = self.data.rows_for(interaction.user.id)
        if not rows:
            await interaction.response.send_message(
                "You're not in the league yet. Grab a team role to join! ⚽", ephemeral=True
            )
            return
        if interaction.user.id == self.owner_id:
            self.mode = self.FANS
            self.page = rows[0][0] // PAGE_SIZE
            await self._redraw(interaction)
            return
        lines = [
            f"You're **#{pos}** with **{team}** · {points(record)} pts"
            for _, (pos, _, team, record) in rows
        ]
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.secondary, row=1)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.page = max(0, self.page - 1)
        await self._redraw(interaction)

    @discord.ui.button(label="—", style=discord.ButtonStyle.secondary, disabled=True, row=1)
    async def page_label(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        pass

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.secondary, row=1)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.page = min(self.data.pages - 1, self.page + 1)
        await self._redraw(interaction)

    async def _on_menu(self, interaction: discord.Interaction) -> None:
        self.mode = self.menu.values[0]
        await self._redraw(interaction)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass
