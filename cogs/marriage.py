"""Server marriages: !marry (with Yes/No buttons), !divorce and !couples."""

import random
from datetime import datetime, timezone

import discord
from discord.ext import commands

import flirt_store

NO_PINGS = discord.AllowedMentions.none()
PROPOSAL_TIMEOUT = 600  # seconds the other person has to answer

_PROPOSALS = [
    "💍 {a} gets down on one knee... {b}, will you marry them? the whole server is holding its breath 😮‍💨",
    "💍 {a} has been practising this speech in the mirror for WEEKS. {b}, will you be theirs forever?",
    "💍 the lights dim, the violins start, someone releases doves indoors... {a} asks {b} the big question 🕊️",
    "💍 {a} just pulled out a ring made of Discord Nitro and pure delusion. {b}, what's it gonna be? 😳",
    "💍 BREAKING NEWS: {a} is proposing to {b}. in a public channel. with no shame. respect 📰",
]
_WEDDINGS = [
    "🎉💒 {a} and {b} are now married! Maya is ugly crying in the back row 😭💕",
    "🎉💒 it's official! {a} + {b}, forever and always. no take-backs, I checked the contract 📜💍",
    "🎉💒 you may now kiss the... okay, send a heart emoji. {a} and {b} are MARRIED! 💞",
    "🎉💒 {b} said YES!! {a} is shaking. the server is shaking. my code is shaking 🫨💕",
    "🎉💒 {a} and {b} just got married. the honeymoon is a voice call that lasts 9 hours 📞🌙",
]
_REJECTIONS = [
    "💔 {b} said no... {a}, Maya's here for you. ice cream? therapy? both? 🍦",
    "💔 OUCH. {b} turned {a} down in front of EVERYONE. the server will need a moment of silence 🕯️",
    "💔 {b} said \"let's just be friends\"... {a}, put the ring down slowly. it's okay. it's okay 🫂",
    "💔 rejected. {a}, look at me. you're still a catch. {b} is just scared of how hot you are 😤",
    "💔 {b} pressed no SO fast. {a}, we'll get through this. there are other fish. in this exact server 🐟",
]
_UNANSWERED = [
    "⏳ the proposal went unanswered... {b} left {a} on read. ON READ. at their own proposal 😬",
    "⏳ {b} never answered. {a} is still on one knee. someone help them up 🦵",
    "⏳ 10 minutes of silence. {b} said nothing. {a}, that's a no but in a cowardly font 💀",
]
_DIVORCES = [
    "💔 {a} and {b} have split after {days}. the server is SHOOK 😱",
    "💔 it's over. {a} and {b} are going their separate ways after {days}. Maya gets custody of the group chat 📱",
    "💔 {a} has filed for divorce from {b} after {days}. pass the tissues and the popcorn 🤧🍿",
    "💔 {a} just divorced {b} after {days}. lawyers are circling. the memes are being prepared 🦈",
    "💔 {a} and {b} are DONE after {days}. who gets the Spotify playlist?? this is getting ugly 🎧⚔️",
]


def _couples(guild_id: int) -> list[dict]:
    return flirt_store.guild_state(guild_id).setdefault("couples", [])


def _couple_of(guild_id: int, member_id: int) -> dict | None:
    return next((c for c in _couples(guild_id) if member_id in c["pair"]), None)


def _days_since(iso: str) -> str:
    days = (datetime.now(timezone.utc) - datetime.fromisoformat(iso)).days
    if days == 0:
        return "less than a day"
    return f"{days} day{'s' if days != 1 else ''}"


class ProposalView(discord.ui.View):
    def __init__(self, cog: "MarriageCog", proposer: discord.Member, partner: discord.Member) -> None:
        super().__init__(timeout=PROPOSAL_TIMEOUT)
        self.cog = cog
        self.proposer = proposer
        self.partner = partner
        self.message: discord.Message | None = None

    def _finish(self) -> None:
        self.cog.pending.discard((self.proposer.guild.id, self.proposer.id))
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.partner.id:
            return True
        text = (
            "you can't say yes to your own proposal. that's just marrying yourself with extra steps 😭"
            if interaction.user.id == self.proposer.id
            else "this proposal isn't for you, nosy 👀 get your own"
        )
        await interaction.response.send_message(text, ephemeral=True)
        return False

    @discord.ui.button(label="Yes!", emoji="💍", style=discord.ButtonStyle.success)
    async def say_yes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        problem = self.cog.marriage_problem(self.proposer, self.partner)
        if problem:
            await interaction.response.edit_message(content=problem, embed=None, view=None)
            self._finish()
            return
        _couples(self.proposer.guild.id).append({
            "pair": [self.proposer.id, self.partner.id],
            "since": datetime.now(timezone.utc).isoformat(),
        })
        flirt_store.save()
        embed = discord.Embed(
            description=random.choice(_WEDDINGS).format(a=self.proposer.mention, b=self.partner.mention),
            color=discord.Color.pink(),
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self._finish()

    @discord.ui.button(label="No", emoji="💔", style=discord.ButtonStyle.danger)
    async def say_no(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        embed = discord.Embed(
            description=random.choice(_REJECTIONS).format(a=self.proposer.mention, b=self.partner.mention),
            color=discord.Color.dark_grey(),
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self._finish()

    async def on_timeout(self) -> None:
        self.cog.pending.discard((self.proposer.guild.id, self.proposer.id))
        if self.message:
            embed = discord.Embed(
                description=random.choice(_UNANSWERED).format(a=self.proposer.mention, b=self.partner.mention),
                color=discord.Color.dark_grey(),
            )
            try:
                await self.message.edit(embed=embed, view=None)
            except discord.HTTPException:
                pass


class MarriageCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.pending: set[tuple[int, int]] = set()  # (guild id, proposer id) with an open proposal

    def marriage_problem(self, a: discord.Member, b: discord.Member) -> str | None:
        """Why these two can't marry right now, or None if they can."""
        for person in (a, b):
            couple = _couple_of(a.guild.id, person.id)
            if couple:
                other_id = couple["pair"][1] if couple["pair"][0] == person.id else couple["pair"][0]
                return f"❌ {person.mention} is already married to <@{other_id}>. homewrecker behaviour. I'm telling 😳"
        return None

    @commands.command(name="marry", aliases=["propose"], help="Propose to someone 💍", usage="@person")
    @commands.guild_only()
    async def marry(self, ctx: commands.Context, partner: discord.Member) -> None:
        if partner.id == ctx.author.id:
            await ctx.send("marrying yourself? self-love is valid but the paperwork needs two signatures, babe 💅")
            return
        if partner.bot:
            await ctx.send("😳 you can't marry a bot. I checked. I checked VERY carefully, for personal reasons 📜💔")
            return
        problem = self.marriage_problem(ctx.author, partner)
        if problem:
            await ctx.send(problem, allowed_mentions=NO_PINGS)
            return
        if (ctx.guild.id, ctx.author.id) in self.pending:
            await ctx.send("⏳ you already have a proposal waiting. proposing to two people at once? the audacity 💕")
            return

        view = ProposalView(self, ctx.author, partner)
        embed = discord.Embed(
            description=random.choice(_PROPOSALS).format(a=ctx.author.mention, b=partner.mention),
            color=discord.Color.pink(),
        )
        embed.set_footer(text=f"{partner.display_name} has 10 minutes to answer")
        self.pending.add((ctx.guild.id, ctx.author.id))
        # Ping the partner so they see the proposal.
        view.message = await ctx.send(
            content=partner.mention, embed=embed, view=view,
            allowed_mentions=discord.AllowedMentions(users=[partner]),
        )

    @commands.command(name="divorce", help="End your server marriage 💔")
    @commands.guild_only()
    async def divorce(self, ctx: commands.Context) -> None:
        couple = _couple_of(ctx.guild.id, ctx.author.id)
        if not couple:
            await ctx.send("divorce who?? you're not even married 💀 (`!marry @someone` first, then ruin it)")
            return
        _couples(ctx.guild.id).remove(couple)
        flirt_store.save()
        other_id = couple["pair"][1] if couple["pair"][0] == ctx.author.id else couple["pair"][0]
        text = random.choice(_DIVORCES).format(a=ctx.author.mention, b=f"<@{other_id}>", days=_days_since(couple["since"]))
        await ctx.send(embed=discord.Embed(description=text, color=discord.Color.dark_grey()))

    @commands.command(name="couples", aliases=["marriages"], help="All the married couples in the server")
    @commands.guild_only()
    async def couples(self, ctx: commands.Context) -> None:
        couples = sorted(_couples(ctx.guild.id), key=lambda c: c["since"])
        if not couples:
            await ctx.send("no couples yet. this server is a desert of loneliness 🏜️ who's going first? `!marry @someone` 💍")
            return
        lines = []
        for c in couples[:25]:
            a, b = (f"<@{i}>" for i in c["pair"])
            lines.append(f"💍 {a} + {b} · married {_days_since(c['since'])}")
        embed = discord.Embed(title="💑 Server couples", description="\n".join(lines), color=discord.Color.pink())
        mine = _couple_of(ctx.guild.id, ctx.author.id)
        footer = f"{len(couples)} couple{'s' if len(couples) != 1 else ''}"
        if not mine:
            footer += " · you're still single btw 👀 `!marry @someone`"
        embed.set_footer(text=footer)
        await ctx.send(embed=embed)
