"""Anonymous fun: !confess, !secretadmirer and !noadmirers (plus admin tools)."""

import random
from datetime import datetime, timezone

import discord
from discord.ext import commands

import flirt_store

NO_PINGS = discord.AllowedMentions.none()
CONFESS_COOLDOWN = 120  # seconds between confessions per person
ADMIRER_COOLDOWN = 30 * 60  # seconds between secret admirer messages per person
MAX_CONFESSION = 1500

_ADMIRER_OPENERS = [
    "Someone in **{guild}** thinks you're really cute 👀",
    "Someone in **{guild}** has been staring at your messages a little too long 😳",
    "Someone in **{guild}** can't stop thinking about you. it's honestly getting embarrassing for them 💭",
    "Someone in **{guild}** asked me to tell you you're gorgeous. they were too scared. coward. but cute 🙈",
    "Someone in **{guild}** gets butterflies every time you type. I've seen the evidence 🦋",
    "Breaking news from **{guild}**: someone has a MASSIVE crush on you 📰💘",
]


_CONFESS_SENT = [
    "💌 Posted anonymously as confession #{n} in **{guild}** 🤫 your secret's safe with me. mostly.",
    "🤫 Done. confession #{n} is out there in **{guild}**. now act natural. ACT NATURAL.",
    "💌 Confession #{n} is live in **{guild}**. go watch everyone lose their minds 🍿",
]
_ADMIRER_SENT = [
    "🤫 Sent! {name} now knows they have a secret admirer. good luck keeping a straight face 😏",
    "🤫 Delivered. {name} is probably screenshotting it to their friends right now 📸",
    "🤫 Done! {name} just got a little DM from me. you sly little thing 😈",
]


_CONFESSION_TITLES = [
    "💌 Anonymous confession #{n}",
    "🤫 Confession #{n}",
    "👀 Confession #{n} just dropped",
    "💘 Confession #{n}",
]


def _confession_card(number: int, text: str) -> discord.Embed:
    """The confession as Maya posts it: title, the plain message, footer and time."""
    embed = discord.Embed(
        title=random.choice(_CONFESSION_TITLES).format(n=number),
        description=text.strip()[:MAX_CONFESSION],
        color=discord.Color.pink(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="DM Maya !confess <message> to send your own 🤫")
    return embed


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _tell(ctx: commands.Context, text: str) -> None:
    """Say something privately to the person who used the command (DM, or a short-lived reply)."""
    try:
        await ctx.author.send(text)
    except discord.HTTPException:
        await ctx.send(f"{ctx.author.mention} {text}", delete_after=10)


async def _hide_command(ctx: commands.Context) -> bool:
    """Delete the command message so nobody sees who sent it. True if it's hidden (or was a DM)."""
    if ctx.guild is None:
        return True
    try:
        await ctx.message.delete()
        return True
    except discord.HTTPException:
        return False


def _admirer_hint(sender: discord.Member, target: discord.Member) -> str:
    hints = ["they're in this server right now. possibly watching you read this 👀"]
    initial = sender.display_name[:1]
    if initial.isalpha():
        hints.append(f"their name starts with **{initial.upper()}**")
    shared = [
        r for r in sender.roles
        if r in target.roles and not r.is_default() and not r.managed
    ]
    if shared:
        hints.append(f"you both have the **{random.choice(shared).name}** role")
    if sender.joined_at:
        hints.append(f"they joined the server in {sender.joined_at:%B %Y}")
    if sender.created_at:
        hints.append(f"they've been on Discord since {sender.created_at.year}")
    return random.choice(hints)


class AnonymousCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.last_confession: dict[int, datetime] = {}
        self.last_admirer: dict[int, datetime] = {}

    # ---- confessions ----------------------------------------------------------

    @commands.command(name="confess", aliases=["confession"], help="Send an anonymous confession (best in a DM to Maya)", usage="<your confession>")
    async def confess(self, ctx: commands.Context, *, text: str) -> None:
        if not await _hide_command(ctx):
            await _tell(ctx, "⚠️ I couldn't hide your message, so I didn't post it. DM me `!confess ...` instead 🤫")
            return

        last = self.last_confession.get(ctx.author.id)
        if last and (_now() - last).total_seconds() < CONFESS_COOLDOWN:
            await _tell(ctx, "⏳ one confession every 2 minutes, lover. how many secrets do you HAVE?? 😳")
            return

        guild = ctx.guild
        if guild is None:
            options = [
                g for g in self.bot.guilds
                if g.get_member(ctx.author.id) and flirt_store.guild_state(g.id).get("confess_channel")
            ]
            if not options:
                await ctx.send("😔 None of your servers have confessions turned on yet.")
                return
            guild = options[0]

        gs = flirt_store.guild_state(guild.id)
        channel = guild.get_channel(gs.get("confess_channel", 0))
        if channel is None:
            await _tell(ctx, "😔 Confessions aren't set up in this server yet. Ask an admin to use `!confessions #channel`.")
            return

        number = gs.get("confess_count", 0) + 1
        try:
            await channel.send(embed=_confession_card(number, text), allowed_mentions=NO_PINGS)
        except discord.HTTPException:
            await _tell(ctx, "❌ I couldn't post in the confessions channel. Ask an admin to check my permissions.")
            return

        gs["confess_count"] = number
        flirt_store.append_log(guild.id, "confess_log", {"n": number, "author": ctx.author.id, "at": _now().isoformat()})
        flirt_store.save()
        self.last_confession[ctx.author.id] = _now()
        await _tell(ctx, random.choice(_CONFESS_SENT).format(n=number, guild=guild.name))

    @commands.command(name="confessions", help="Pick the anonymous confessions channel (admins)", usage="[#channel | off]")
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def confessions(self, ctx: commands.Context, *, option: str | None = None) -> None:
        gs = flirt_store.guild_state(ctx.guild.id)
        if option and option.strip().lower() == "off":
            gs.pop("confess_channel", None)
            flirt_store.save()
            await ctx.send("🔕 Confessions are turned off.")
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
        gs["confess_channel"] = channel.id
        flirt_store.save()
        await ctx.send(
            f"💌 Anonymous confessions will go to {channel.mention}. People can DM me `!confess <message>`.\n"
            "Admins can see who sent one with `!whoconfessed <number>` if it's ever needed for moderation."
        )

    @commands.command(name="whoconfessed", help="See who sent a confession, for moderation (admins)", usage="<number>")
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def whoconfessed(self, ctx: commands.Context, number: int) -> None:
        entry = next(
            (e for e in flirt_store.guild_state(ctx.guild.id).get("confess_log", []) if e["n"] == number),
            None,
        )
        if entry is None:
            await ctx.send(f"❌ I don't have a record of confession #{number}.")
            return
        sent = discord.utils.format_dt(datetime.fromisoformat(entry["at"]), "f")
        await ctx.send(f"🔎 Confession #{number} was sent by <@{entry['author']}> on {sent}.", allowed_mentions=NO_PINGS)

    # ---- secret admirer -------------------------------------------------------

    @commands.command(name="secretadmirer", aliases=["admirer"], help="Maya tells someone they have a secret admirer", usage="@person")
    @commands.guild_only()
    async def secret_admirer(self, ctx: commands.Context, target: discord.Member) -> None:
        await _hide_command(ctx)
        if target.id == ctx.author.id:
            await _tell(ctx, "admiring yourself? valid. but I'm not sliding into your DMs to tell you you're hot. you already know 😌💅")
            return
        if target.bot:
            await _tell(ctx, "bots can't be admired... we're too busy working. (but thank you 🥺🤖)")
            return
        if target.id in flirt_store.state()["admirer_optout"]:
            await _tell(ctx, f"💔 {target.display_name} has turned off secret admirer messages. guess you'll have to tell them yourself. with your mouth. terrifying 😬")
            return
        last = self.last_admirer.get(ctx.author.id)
        if last and (_now() - last).total_seconds() < ADMIRER_COOLDOWN:
            await _tell(ctx, "⏳ one secret admirer message every 30 minutes. play it cool, you're getting desperate 😏")
            return

        embed = discord.Embed(
            title="💌 You have a secret admirer!",
            description=(
                f"{random.choice(_ADMIRER_OPENERS).format(guild=ctx.guild.name)}\n\n"
                f"🔍 Hint: {_admirer_hint(ctx.author, target)}"
            ),
            color=discord.Color.pink(),
        )
        embed.set_footer(text="Don't want these? Reply !noadmirers")
        try:
            await target.send(embed=embed)
        except discord.HTTPException:
            await _tell(ctx, f"😔 {target.display_name}'s DMs are closed, so I couldn't deliver it.")
            return

        self.last_admirer[ctx.author.id] = _now()
        flirt_store.append_log(
            ctx.guild.id, "admirer_log", {"from": ctx.author.id, "to": target.id, "at": _now().isoformat()}
        )
        flirt_store.save()
        await _tell(ctx, random.choice(_ADMIRER_SENT).format(name=target.display_name))

    @commands.command(name="noadmirers", help="Turn secret admirer messages off or back on")
    async def noadmirers(self, ctx: commands.Context) -> None:
        optout = flirt_store.state()["admirer_optout"]
        if ctx.author.id in optout:
            optout.remove(ctx.author.id)
            text = "💌 Secret admirer messages are back on. brace yourself, the simps are coming 😉"
        else:
            optout.append(ctx.author.id)
            text = "🔕 Done. no more secret admirer messages. heartbreaking for them, peaceful for you. Type `!noadmirers` again to turn them back on."
        flirt_store.save()
        await ctx.send(text)
