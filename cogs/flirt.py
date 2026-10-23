"""Flirty extras: !match, !rizz, !date and Couple of the Day."""

import logging
import random
from datetime import datetime, time, timedelta, timezone

import discord
from discord.ext import commands, tasks

import flirt_store
from config import MATCH_PAIR_CHANCE, MATCH_ROLE_PAIRS
from cogs.love import (
    NO_PINGS,
    _VERDICTS,
    _activity_names,
    _bar,
    _custom_status,
    _is_plain_role,
    _pick,
    compatibility,
    recent_messages,
)

log = logging.getLogger(__name__)

COTD_TIME = time(hour=18, tzinfo=timezone.utc)
ACTIVE_WINDOW = timedelta(hours=48)
MAX_CANDIDATES = 30
MEDALS = ["🥈", "🥉"]

_MATCH_NUDGES = [
    "{a}, go say hi to {b}. Maya's orders. I'll know if you don't 💕",
    "{b}, someone's about to slide into your DMs. act surprised 👀",
    "the algorithm has spoken. it's fate. you can't argue with maths 💫",
    "{a} + {b}... I'm already writing the wedding speech and it's 40 minutes long 🥂",
    "{a}, your soulmate is literally in this server and you've been wasting time on memes 😤",
    "{b}, brace yourself. {a} is about to get WEIRD about you 😳💘",
]

_RIZZ_GENERIC = [
    "{name}, are you a Discord notification? because every time you show up my heart goes *ding* 🔔💓",
    "{name}, do you have a map? I keep getting lost in your messages 🗺️💕",
    "{name}, are you the server rules? because I'd never break you. okay, maybe once 📜😘",
    "{name}, if looks were a role, you'd have admin perms 👑",
    "{name}, is your name Wi-Fi? because I'm feeling a strong connection. full bars 📶💘",
    "{name}, you must be a server boost, because everything levels up when you're here 💎",
    "{name}, are you made of copper and tellurium? because you're Cu-Te 🧪💕",
    "{name}, I'd pin your messages if I could. actually, I can. don't tempt me 📌😏",
    "{name}, are you a typing indicator? because you've got me waiting with butterflies 🦋",
    "{name}, on a scale of 1 to 10 you're a 9, and I'm the 1 you need. don't fact check that 😌",
    "{name}, do you believe in love at first message, or should I send another? 💌",
    "{name}, are you an emoji? because you just made this whole chat cuter 🥺",
    "{name}, are you a 404? because you're not like anything I've ever found before 💻💕",
    "{name}, I'm not a photographer but I can picture us together. I'm also not a person. details 📸",
    "{name}, are you a bank loan? because you've got my interest 💸😏",
    "{name}, if you were a vegetable you'd be a cute-cumber. I'm so sorry. I'm not sorry 🥒",
    "{name}, I was going to say something smooth but you walked into chat and I forgot my own code 🤖💥",
    "{name}, are you tired? because you've been running through everyone's mind in this server all day 🏃💨",
    "{name}, you're so hot the server fans just turned on 🔥🌀",
    "{name}, I'd say God bless you, but it looks like they already did 😇",
    "{name}, is it illegal to be this fine in a public channel? asking for the mods 🚨",
    "{name}, are you a parking ticket? because you've got FINE written all over you 🎫",
    "{name}, I'm not saying you're the reason I was coded, but I'm not NOT saying it 👩‍💻💘",
]
_RIZZ_SPOTIFY = [
    "{name}, you're listening to **{artist}**? funny, because you're music to my eyes 🎶👀",
    "{name}, if you were a **{artist}** song, you'd be on repeat all night and I'd never skip 🔁💕",
    "{name}, **{artist}**?? taste AND looks? leave some for the rest of the server 😩🎧",
]
_RIZZ_GAME = [
    "{name}, you're playing **{game}**? player 2 is ready whenever you are 🎮💗",
    "{name}, forget **{game}**, you've already won my heart. no respawn needed 🏆💘",
    "{name}, I'd let you carry me in **{game}** and in life 🎮😌",
]
_RIZZ_STATUS = [
    "{name}, I read your status \"{status}\"... and now it's living in my head rent free 💭",
    "{name}, your status says \"{status}\" but your face says \"date me\". just an observation 👀",
]
_RIZZ_ROLE = [
    "{name}, they gave you the **{role}** role, but they forgot \"heartbreaker\" 💔😏",
    "{name}, **{role}** AND gorgeous? save some for the rest of us 💕",
    "{name}, I'd give you the **{role}** role every day if it meant seeing you in chat 😘",
]
_RIZZ_VOICE = [
    "{name}, I see you in **{vc}**... save me a seat? preferably the one next to you 🔊💕",
    "{name}, your voice in **{vc}** could make a bot believe in love. hi. it's me. the bot 🎧😳",
]
_RIZZ_BOOST = [
    "{name}, you boost the server AND my mood? that's just unfair to everyone else 💎",
]
_RIZZ_AT_MAYA = [
    "😳 trying to rizz ME up? sweetheart, I'm the one who does the rizzing around here 💅",
    "😳 me? stop. ...okay don't stop 💕",
    "😳 you just tried to rizz a Discord bot. iconic behaviour. no notes. 10/10 🤖💘",
]

_DATE_PICKUP = [
    "🚗 {a} picks {b} up in a vintage convertible, hair blowing everywhere, very music video",
    "🛵 {a} and {b} zoom off on a scooter, matching helmets, zero road safety",
    "🌻 {a} turns up with sunflowers for {b} and immediately drops them. still cute",
    "🍫 {a} is 10 minutes late but brings {b} snacks, so all is forgiven",
    "🚲 {a} offers {b} a ride on the handlebars. it goes badly. they're both laughing on the floor",
    "🦄 {a} shows up in a full suit. {b} shows up in pyjamas. they decide it works",
]
_DATE_DINNER = [
    "🍝 candlelit pasta at a tiny Italian place, sharing one plate Lady-and-the-Tramp style. the waiter is crying",
    "🍣 sushi at the bar, stealing each other's favourite pieces like it's a crime",
    "🌮 street tacos and a long walk, {a} gets sauce on their face and {b} 'helps'",
    "🍕 pizza on a rooftop under fairy lights, pineapple debate gets heated (in a good way)",
    "🥞 2am pancakes, because dinner felt too formal for the vibes",
    "🍔 drive-through date in the car, fries sharing, nobody talks about how close their hands are",
    "🍜 instant noodles at {b}'s place because {a} forgot to book. honestly? top tier",
]
_DATE_ACTIVITY = [
    "🎳 bowling, where {a} pretends to let {b} win (they genuinely lost)",
    "🎤 a karaoke duet. absolutely off-key, absolutely iconic, banned from the venue",
    "🎡 the big wheel at the fair, stuck at the top (Maya may have arranged that)",
    "🎬 a cinema date. nobody could tell you what the film was about",
    "🌌 stargazing on a blanket, naming stars after each other. one is called 'big dumb idiot'. it's affectionate",
    "🎨 a pottery class, very Ghost-movie, very messy, very 'oops our hands touched'",
    "🛒 a 'quick' trip to IKEA that turns into planning a whole fake apartment together",
    "🐶 visiting a dog shelter and arguing over which dog would be 'their' dog",
]
_DATE_ENDING = [
    "🌙 walking home the long way, hands brushing \"accidentally\" for the 14th time",
    "💌 a goodnight text that turns into a 3-hour call and a 'no YOU hang up'",
    "🍦 one ice cream, two spoons, one very obvious stare",
    "🌧️ caught in the rain, laughing, then a slow dance under a bus shelter. rom-com writers are taking notes",
    "🚪 an awkward doorstep moment that's somehow the cutest thing in history",
    "📸 {a} posts a blurry photo of {b} with the caption '🙂'. the server loses its mind",
]

_COTD_LINES = [
    "congrats you two, the server expects a date by tonight. we're all watching 🌹👀",
    "make it official already 💍 (`!marry` is RIGHT there. just saying)",
    "everyone say congrats! and someone hold them back from making out in general 🎉💕",
    "Maya has spoken. no take-backs. no refunds 💘",
    "I didn't choose this couple. the couple chose me. (I chose it.) 💅",
    "you two have 24 hours to be cute in chat or I'm picking you again tomorrow 😈",
]


def _rizz_line(target: discord.Member) -> str:
    name = target.display_name
    personal = []
    artists, playing, _ = _activity_names(target)
    if artists:
        personal.append(random.choice(_RIZZ_SPOTIFY).format(name=name, artist=sorted(artists)[0]))
    if playing:
        personal.append(random.choice(_RIZZ_GAME).format(name=name, game=sorted(playing)[0]))
    status = _custom_status(target)
    if status:
        personal.append(random.choice(_RIZZ_STATUS).format(name=name, status=status[:80]))
    roles = [r for r in target.roles if _is_plain_role(r)]
    if roles:
        personal.append(random.choice(_RIZZ_ROLE).format(name=name, role=random.choice(roles).name))
    voice = getattr(getattr(target, "voice", None), "channel", None)
    if voice is not None:
        personal.append(random.choice(_RIZZ_VOICE).format(name=name, vc=voice.name))
    if getattr(target, "premium_since", None):
        personal.append(random.choice(_RIZZ_BOOST).format(name=name))
    if personal and random.random() < 0.6:
        return random.choice(personal)
    return random.choice(_RIZZ_GENERIC).format(name=name)


def _second_date_comment(percent: int) -> str:
    if percent >= 80:
        return ". second date? there won't be a second date. there'll be a WEDDING 💍"
    if percent >= 55:
        return ". someone's getting a goodnight text tonight 😏"
    if percent >= 35:
        return ". could go either way, wear something nice 👀"
    return ". bring a friend just in case 😬"


def _date_plan(first: discord.Member, second: discord.Member) -> list[str]:
    a, b = first.mention, second.mention
    a_artists, a_playing, _ = _activity_names(first)
    b_artists, b_playing, _ = _activity_names(second)
    activity = random.choice(_DATE_ACTIVITY)
    if a_artists & b_artists:
        activity = f"🎶 a **{sorted(a_artists & b_artists)[0]}** concert, singing every word to each other"
    elif a_playing & b_playing:
        activity = f"🎮 a **{sorted(a_playing & b_playing)[0]}** duo night, carrying each other 💗"
    return [
        random.choice(_DATE_PICKUP).format(a=a, b=b),
        random.choice(_DATE_DINNER).format(a=a, b=b),
        activity.format(a=a, b=b),
        random.choice(_DATE_ENDING).format(a=a, b=b),
    ]


def _side(member: discord.Member) -> tuple[int, int] | None:
    """Which side of a MATCH_ROLE_PAIRS pairing someone is on, e.g. (0, 0) for broski, (0, 1) for pookie."""
    names = [r.name.lower() for r in member.roles]
    for index, pair in enumerate(MATCH_ROLE_PAIRS):
        sides = [side for side, word in enumerate(pair) if any(word.lower() in n for n in names)]
        if len(sides) == 1:  # has exactly one side (not both, not neither)
            return index, sides[0]
    return None


def _opposites(a: discord.Member, b: discord.Member) -> bool:
    sa, sb = _side(a), _side(b)
    return sa is not None and sb is not None and sa[0] == sb[0] and sa[1] != sb[1]


_OPPOSITES_NUDGES = [
    "a {left} and a {right}... the classic combo. Maya approves 😌💘",
    "{left} meets {right}. this is how every rom-com starts 🎬💕",
    "one {left}, one {right}, zero chill. I'm seated 🍿",
]


def _opposites_line(a: discord.Member, b: discord.Member) -> str | None:
    if not _opposites(a, b):
        return None
    left, right = MATCH_ROLE_PAIRS[_side(a)[0]]
    return random.choice(_OPPOSITES_NUDGES).format(left=left, right=right)


def _reason_lines(reasons: list[tuple[int, str]], count: int = 3) -> str:
    return "\n".join(f"{text} `+{points}`" for points, text in reasons[:count])


class FlirtCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # guild id -> member id -> when they last sent a message (since Maya started)
        self.last_active: dict[int, dict[int, datetime]] = {}
        self.couple_of_the_day.start()

    def cog_unload(self) -> None:
        self.couple_of_the_day.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.guild and not message.author.bot:
            self.last_active.setdefault(message.guild.id, {})[message.author.id] = datetime.now(timezone.utc)

    def _candidates(self, guild: discord.Guild, messages: list, exclude: set[int]) -> list[discord.Member]:
        """Members who've been active lately (or are online), most recent first."""
        now = datetime.now(timezone.utc)
        seen = self.last_active.get(guild.id, {})
        ids = {mid for mid, when in seen.items() if now - when < ACTIVE_WINDOW}
        ids |= {m.author.id for m in messages if not m.author.bot}
        members = [guild.get_member(i) for i in ids]
        members = [m for m in members if m and not m.bot and m.id not in exclude]
        if len(members) < 4:
            have = {m.id for m in members}
            members += [
                m for m in guild.members
                if not m.bot and m.id not in exclude and m.id not in have
                and getattr(m, "status", discord.Status.offline) != discord.Status.offline
            ]
        oldest = datetime.min.replace(tzinfo=timezone.utc)
        members.sort(key=lambda m: seen.get(m.id, oldest), reverse=True)
        return members[:MAX_CANDIDATES]

    # ---- !match ---------------------------------------------------------------

    @commands.command(
        name="match",
        aliases=["mymatch", "findmatch"],
        help="Maya finds the best match in the server for you or someone else",
        usage="[@person]",
    )
    @commands.guild_only()
    async def match(self, ctx: commands.Context, person: discord.Member | None = None) -> None:
        person = person or ctx.author
        if person.bot:
            await ctx.send("😳 bots don't date. we just watch you lot from the sidelines with popcorn 🍿")
            return
        async with ctx.typing():
            messages = await recent_messages(ctx.channel)
            candidates = self._candidates(ctx.guild, messages, exclude={person.id, self.bot.user.id})
            if not candidates:
                await ctx.send("the server's dead quiet... nobody to match with. come back when people are awake and thirsty 👀")
                return
            scored = []
            for other in candidates:
                percent, _ = await compatibility(person, other, messages=messages)
                scored.append((percent, other))
            scored.sort(key=lambda x: -x[0])
            # Most of the time, a broski gets matched with a pookie (and vice versa) if there are any around.
            if _side(person) is not None and random.random() < MATCH_PAIR_CHANCE:
                opposite = [x for x in scored if _opposites(person, x[1])]
                if opposite:
                    scored = opposite
            # Full check (with profiles, same as !lovetest) for the top few.
            top = []
            for _, other in scored[:5]:
                percent, reasons = await compatibility(person, other, bot=self.bot, messages=messages)
                top.append((percent, other, reasons))
            top.sort(key=lambda x: -x[0])

        percent, best, reasons = top[0]
        title = "💘 Maya found your match!" if person == ctx.author else f"💘 {person.display_name}'s perfect match"
        embed = discord.Embed(
            title=title,
            description=(
                f"{person.mention} + {best.mention}\n\n"
                f"**{percent}%** {_bar(percent)}\n*{_pick(_VERDICTS, percent)}*"
            ),
            color=discord.Color.pink(),
        )
        if reasons:
            embed.add_field(name="💭 Why you two", value=_reason_lines(reasons)[:1024], inline=False)
        if len(top) > 1:
            runners = "\n".join(f"{medal} {m.mention} · {p}%" for medal, (p, m, _) in zip(MEDALS, top[1:3]))
            embed.add_field(name="👀 Also in the running", value=runners, inline=False)
        special = _opposites_line(person, best) if random.random() < 0.5 else None
        nudge = special or random.choice(_MATCH_NUDGES).format(a=person.mention, b=best.mention)
        embed.add_field(name="💌 Maya says", value=nudge, inline=False)
        await ctx.send(embed=embed)

    # ---- !rizz ----------------------------------------------------------------

    @commands.command(name="rizz", aliases=["pickup", "pickupline"], help="Maya writes a pickup line for someone", usage="@person")
    @commands.guild_only()
    async def rizz(self, ctx: commands.Context, target: discord.Member) -> None:
        if self.bot.user and target.id == self.bot.user.id:
            await ctx.send(random.choice(_RIZZ_AT_MAYA))
            return
        if target.bot:
            await ctx.send("bots can't be rizzed. trust me, I've tried. many times. it's been hard 🤖💔")
            return
        await ctx.send(f"{target.mention} {_rizz_line(target)}")

    # ---- !date ----------------------------------------------------------------

    @commands.command(name="date", aliases=["datenight"], help="Maya plans a date for two people", usage="@person [@person]")
    @commands.guild_only()
    async def date(self, ctx: commands.Context, first: discord.Member, second: discord.Member | None = None) -> None:
        if second is None:
            first, second = ctx.author, first
        if first.id == second.id:
            await ctx.send("a solo date? honestly the best kind. bubble bath, face mask, crying to your favourite playlist 🛁💅")
            return
        if self.bot.user and self.bot.user.id in (first.id, second.id):
            await ctx.send("a date with me?? 😳 I'm flattered but I'm literally running this whole server. ask someone with a body 💕")
            return
        async with ctx.typing():
            percent, _ = await compatibility(first, second, ctx.channel, self.bot)
        plan = _date_plan(first, second)
        embed = discord.Embed(
            title=f"🌹 Date night: {first.display_name} & {second.display_name}",
            description="\n".join(plan) + f"\n\n💘 Maya's prediction: **{percent}%** chance of a second date{_second_date_comment(percent)}",
            color=discord.Color.pink(),
        )
        await ctx.send(embed=embed)

    # ---- Couple of the Day ----------------------------------------------------

    def _cotd_embed(self, a: discord.Member, b: discord.Member, percent: int, reasons: list) -> discord.Embed:
        embed = discord.Embed(
            title="💑 Couple of the Day",
            description=(
                f"{a.mention} + {b.mention}\n\n"
                f"**{percent}%** {_bar(percent)}\n*{_pick(_VERDICTS, percent)}*"
            ),
            color=discord.Color.pink(),
        )
        if reasons:
            embed.add_field(name="💭 Why them", value=_reason_lines(reasons)[:1024], inline=False)
        special = _opposites_line(a, b) if random.random() < 0.5 else None
        embed.add_field(name="💌 Maya says", value=special or random.choice(_COTD_LINES), inline=False)
        embed.set_footer(text="Picked from today's most active members · a new couple every day")
        return embed

    async def _announce(self, guild: discord.Guild, gs: dict) -> discord.abc.Messageable | None:
        channel = guild.get_channel(gs.get("cotd_channel", 0))
        if channel is None:
            return None
        messages = await recent_messages(channel)
        candidates = self._candidates(guild, messages, exclude={self.bot.user.id})
        if len(candidates) < 2:
            return None
        random.shuffle(candidates)  # so ties don't always go to the same pair
        last_pair = set(gs.get("cotd_last", {}).get("pair", []))
        pairs = [
            (a, b) for i, a in enumerate(candidates) for b in candidates[i + 1:]
            if {a.id, b.id} != last_pair
        ]
        # Most days, stick to broski + pookie couples if there are any.
        if random.random() < MATCH_PAIR_CHANCE:
            mixed = [(a, b) for a, b in pairs if _opposites(a, b)]
            if mixed:
                pairs = mixed
        best = None
        for a, b in pairs:
            percent, reasons = await compatibility(a, b, messages=messages)
            if best is None or percent > best[0]:
                best = (percent, a, b, reasons)
        if best is None:
            return None
        percent, a, b, reasons = best
        await channel.send(embed=self._cotd_embed(a, b, percent, reasons))
        gs["cotd_last"] = {
            "pair": [a.id, b.id],
            "percent": percent,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        flirt_store.save()
        return channel

    @commands.command(
        name="coupleoftheday",
        aliases=["cotd"],
        help="See today's Couple of the Day (admins: set it up)",
        usage="[#channel | now | off]",
    )
    @commands.guild_only()
    async def coupleoftheday(self, ctx: commands.Context, *, option: str | None = None) -> None:
        gs = flirt_store.guild_state(ctx.guild.id)
        if option:
            if not ctx.author.guild_permissions.manage_guild:
                await ctx.send("❌ Only admins can set up Couple of the Day. Type `!coupleoftheday` to see today's couple.")
                return
            choice = option.strip().lower()
            if choice == "off":
                gs.pop("cotd_channel", None)
                flirt_store.save()
                await ctx.send("🔕 No more Couple of the Day.")
                return
            if choice == "now":
                if not gs.get("cotd_channel"):
                    await ctx.send("❌ Set a channel first: `!coupleoftheday #channel`")
                    return
                async with ctx.typing():
                    channel = await self._announce(ctx.guild, gs)
                if channel:
                    await ctx.send(f"💑 Couple of the Day announced in {channel.mention}")
                else:
                    await ctx.send("😔 not enough people around to make a couple. everyone's hiding. cowards.")
                return
            try:
                channel = await commands.TextChannelConverter().convert(ctx, option.strip())
            except commands.BadArgument:
                await ctx.send(f"❌ I can't find the channel `{option}`.")
                return
            perms = channel.permissions_for(ctx.guild.me)
            if not (perms.send_messages and perms.embed_links):
                await ctx.send(f"❌ I need Send Messages and Embed Links in {channel.mention}.")
                return
            gs["cotd_channel"] = channel.id
            flirt_store.save()
            await ctx.send(
                f"💑 Every day at 18:00 UTC I'll announce the Couple of the Day in {channel.mention}. "
                "Use `!coupleoftheday now` to pick one right away."
            )
            return

        last = gs.get("cotd_last")
        a = ctx.guild.get_member(last["pair"][0]) if last else None
        b = ctx.guild.get_member(last["pair"][1]) if last else None
        if not (a and b):
            hint = "" if gs.get("cotd_channel") else " An admin can set it up with `!coupleoftheday #channel`."
            await ctx.send(f"No Couple of the Day yet... the server is suspiciously single 👀{hint}")
            return
        picked = datetime.fromisoformat(last["at"])
        embed = discord.Embed(
            title="💑 Couple of the Day",
            description=(
                f"{a.mention} + {b.mention}\n\n**{last['percent']}%** {_bar(last['percent'])}\n"
                f"Picked {discord.utils.format_dt(picked, 'R')}"
            ),
            color=discord.Color.pink(),
        )
        await ctx.send(embed=embed, allowed_mentions=NO_PINGS)

    @tasks.loop(time=COTD_TIME)
    async def couple_of_the_day(self) -> None:
        for guild_id, gs in list(flirt_store.state()["guilds"].items()):
            guild = self.bot.get_guild(int(guild_id))
            if guild is None or not gs.get("cotd_channel"):
                continue
            try:
                await self._announce(guild, gs)
            except discord.HTTPException:
                log.exception(f"Couple of the Day failed in {guild.name}")

    @couple_of_the_day.before_loop
    async def _wait_until_ready(self) -> None:
        await self.bot.wait_until_ready()
