"""!lovetest: how compatible two members are, from what Maya can see about them (no football)."""

import hashlib
import random
import re
import unicodedata

import discord
from discord.ext import commands

from config import FOOTBALL_TEAMS

NO_PINGS = discord.AllowedMentions.none()
MAX_REASONS = 6
HISTORY_LIMIT = 300  # recent messages in the channel Maya reads for chat clues

_CUSTOM_EMOJI = re.compile(r"<a?:\w+:\d+>")
_STOPWORDS = {
    "about", "after", "again", "also", "been", "from", "have", "just", "like", "more", "only",
    "over", "really", "some", "that", "them", "then", "there", "they", "this", "what", "when",
    "with", "your", "yours", "will", "would", "dont", "cant", "im",
}

# The score stays stable for a pair; the wording is picked fresh each time.
_SHARED_ROLES = [
    "🎭 share {roles}. you keep ending up in the same places... are you following each other? be honest 👀",
    "🎭 share {roles}. matching roles today, matching tattoos tomorrow 💅",
    "🎭 share {roles}. same circles, same vibe, same bed sheets eventually? I'm KIDDING. unless 😏",
    "🎭 share {roles}. the server literally sorted you into the same box. that's basically an arranged marriage 💍",
]
_SAME_COLOUR = [
    "🎨 your names are both **{role}** coloured. you two coordinated outfits without even talking. disgusting. I love it 😍",
    "🎨 matching **{role}** name colours?? next you'll be finishing each other's sentences 🙄💕",
]
_BOOSTERS = [
    "💎 both boosting the server. rich, generous, and clearly trying to impress each other 💸😏",
    "💎 two boosters? a power couple with a budget. marry rich, kids 💅",
]
_STATUS_EMOJI = [
    "💬 both have {emoji} in your status. secret couple code? don't lie to me 👀",
    "💬 {emoji} in both your statuses... that's not a coincidence, that's a cry for help (to each other) 💌",
]
_STATUS_WORDS = [
    "💬 you both wrote **{word}** in your status. same brain cell, shared lovingly 🧠💕",
    "💬 **{word}** in both your statuses? you two are flirting through your bios and thought I wouldn't notice 😏",
]
_CHATTING = [
    "💌 replied to or pinged each other {n} times in here lately. get a room. or a DM. same thing 👀",
    "💌 {n} replies and pings between you two recently. the flirting is NOT as subtle as you think 😏",
    "💌 {n} times you two have been at each other in this chat. I've been watching. I'm always watching 👁️💕",
]
_CHAT_EMOJI = [
    "😚 you both keep spamming {emoji} in chat. same sense of humour = dangerous combo 😘",
    "😚 {emoji} is clearly your couple emoji. I've noticed. everyone has noticed 🙄💕",
]
_ACCENT = [
    "🌈 your profile colours match. you're colour-coordinating your PROFILES now?? wedding planners in shambles 🎀",
]
_BANNERS = [
    "🖼️ both rocking custom profile banners. an aesthetic couple who will absolutely post each other on their story 📸",
]
_ANIMATED = [
    "✨ both have animated profile pics. high maintenance, high standards, highly compatible 💅",
]
_SPOTIFY = [
    "🎧 both listening to **{artist}** right now. that's basically slow dancing in separate rooms 🎶💃",
    "🎧 vibing to **{artist}** at the same time? the shared playlist is already called 'us' 💕",
    "🎧 same **{artist}** song energy... one of you is definitely thinking about the other right now 🎶😳",
]
_BOTH_MUSIC = [
    "🎶 both have music on right now. different songs, same longing 💃🕺",
]
_GAME = [
    "🎮 both on **{game}** right now. duo queue date? loser has to say \"you're cute\" out loud 😘",
    "🎮 both playing **{game}**. player 2 has entered your heart and refuses to leave 🕹️💗",
]
_VOICE = [
    "🔊 already in **{vc}** together... hearing each other's voices 😳 I'll show myself out",
    "🔊 sharing **{vc}** right now. whispering sweet nothings, I assume. or arguing. same thing at this point 🤫💕",
]
_MOBILE = [
    "📱 both on your phones right now... texting each other under the table? CAUGHT 👀",
]
_ONLINE = [
    "🟢 both online right now... just staring at the chat, waiting for the other to text first? cowards 📱💕",
]
_SAME_WEEK = [
    "📅 joined the server {when}. fate literally pushed you through the same door 🚪💘",
    "📅 arrived {when}... was that planned? did you two come as a package deal? be honest 👀",
]
_SAME_MONTHS = [
    "📅 joined just {days} days apart. you've been circling each other like sharks this whole time 🦈😏",
]
_SAME_YEAR = [
    "🎂 both joined Discord in {year}. childhood sweethearts of the internet. this is a Netflix series 🥹",
]
_INITIALS = [
    "🔤 both names start with **{letter}**. matching initials on the towels, the mugs, the gravestone 🛁💍",
    "🔤 **{letter}** + **{letter}**... I'm already carving it into a tree 🌳💘",
]
_NOTHING_IN_COMMON = [
    "I found literally nothing in common... the perfect excuse to get to know each other 👀",
    "a total mystery to me... and mysteries are hot 😏",
    "nothing in common? blank canvas. paint something cute. or chaotic. I'll take either 🎨💕",
    "zero overlap. you two are strangers. strangers who are about to be VERY not strangers 😈",
]
_VERDICTS = [
    (90, [
        "soulmates. I hear wedding bells, a choir and someone crying (it's me) 💍😭",
        "get a room. actually get a house. a mortgage. a dog named after me 🏡🐶",
        "this is the love story I'd watch on repeat and scream at the screen 🎬💘",
        "I'm calling the priest. no I'm not taking questions 💒",
    ]),
    (75, [
        "the way you two look at each other... I'm melting into the floor 🫠💗",
        "the chemistry is chemistry-ing. someone open a window, it's getting HOT in here 🥵",
        "I'm already planning your first date and you can't stop me 🍝🕯️",
        "the tension?? I could cut it with a knife and spread it on toast 🍞😩",
    ]),
    (55, [
        "a little spark is there. one candlelit dinner and it's game over 🕯️",
        "there's tension here and I'm eating it up with a spoon 😏",
        "flirty texts at 2am energy. don't pretend you haven't 📱💋",
        "you're one 'haha you're so funny 🥺' away from dating 💬",
    ]),
    (35, [
        "a slow burn. like, VERY slow. microwave on defrost slow 🌱",
        "it's giving 'just friends'... the kind of friends who stare a little too long 😉",
        "one good conversation and this whole thing flips. I believe in you. barely 💭",
    ]),
    (15, [
        "maybe in another life, my loves. maybe in another server 🥺",
        "the vibes are shy. painfully shy. hiding-behind-a-plant shy 🙈🪴",
        "friend-zone forecast: cloudy with a strong chance of 'you're like a sibling to me' ☁️",
    ]),
    (0, [
        "the stars said no. the moon said no. the WiFi said no 💫",
        "yikes. but enemies-to-lovers is a whole genre and I'm seated 🍿😈",
        "zero sparks... unless you two are about to prove me VERY wrong 👀",
        "this is a crime scene, not a love story. but I'd still read it 📚",
    ]),
]
_ADVICE = [
    (75, [
        "{a}, if you don't slide into {b}'s DMs tonight, I'm doing it for you and I WILL use your name 😤💕",
        "{a} and {b}, the server ships it. the server has spoken. resistance is futile 📣💘",
        "save me a seat at the wedding. front row. I'm giving a speech and it's going to be embarrassing 💐🎤",
        "{b}, check your DMs in 5 minutes. no reason. 👀",
    ]),
    (40, [
        "{a}, compliment {b}'s profile pic. right now. I'm watching 😉",
        "voice chat tonight, both of you. Maya's orders. no excuses, no 'I'm tired' 🎧💞",
        "{a}, send {b} a song that reminds you of them. if it's a breakup song we need to talk 🎶",
        "{b}, stop pretending you didn't smile reading this 😏",
    ]),
    (0, [
        "go talk! the best love stories start with 'so... hi' and a lot of sweating 👋💦",
        "{a}, ask {b} their favourite song. if it's bad, lie and say you love it. that's romance 🎶😏",
        "one late-night voice call and we run this test again. I have a feeling 📞💘",
        "{a}, {b}... just say hi. I'll hold your hand. metaphorically. I'm a bot 🤖💕",
    ]),
]
_SELF_LOVE = [
    "💘 {m} + {m} = 100%. loving yourself is the most beautiful romance of all 🥰💗",
    "💘 {m} + {m} = 100%. honestly? iconic. no notes. marry yourself, I'll officiate 💅✨",
    "💘 {m} + {m} = 100%. the only person who'll never leave you on read 🍷💕",
    "💘 {m} testing themselves... babe, are you okay? (100% though, you're a catch) 🥺",
]
_MAYA_LOVE = [
    "😳 me and {m}? stop, you're making me blush... I'm a bot, I don't even HAVE cheeks 🙈💕",
    "😳 {m}, are you flirting with me? ...buy me a coffee first. I don't drink coffee. buy it anyway ☕💗",
    "😳 me + {m}? I'd say 100% but a lady never tells 💋",
    "😳 {m}, I'm married to this server. ...but what the server doesn't know won't hurt it 😏",
]


def _pair_seed(a: discord.Member, b: discord.Member) -> int:
    # Same pair always gets the same number, whichever order they're named.
    low, high = sorted((a.id, b.id))
    return int(hashlib.sha256(f"{low}:{high}".encode()).hexdigest(), 16)


def _is_plain_role(role: discord.Role) -> bool:
    """A role worth comparing: not @everyone, not a bot's role, not a football team."""
    if role.name in FOOTBALL_TEAMS or getattr(role, "managed", False):
        return False
    return not (role.is_default() if hasattr(role, "is_default") else role.name == "@everyone")


def _emojis(text: str) -> set[str]:
    found = set(_CUSTOM_EMOJI.findall(text))
    found.update(ch for ch in text if ord(ch) > 0x2000 and unicodedata.category(ch) == "So")
    return found


def _words(text: str) -> set[str]:
    words = re.findall(r"[a-zà-ÿ']{4,}", text.lower())
    return {w.strip("'") for w in words if w.strip("'") not in _STOPWORDS}


def _custom_status(member: discord.Member) -> str:
    for activity in getattr(member, "activities", ()) or ():
        if isinstance(activity, discord.CustomActivity):
            return f"{activity.emoji or ''} {activity.name or ''}".strip()
    return ""


# ---- what Maya compares -------------------------------------------------------

def _roles(a: discord.Member, b: discord.Member) -> list[tuple[int, str]]:
    reasons = []
    b_ids = {r.id for r in b.roles}
    shared = [r for r in a.roles if r.id in b_ids and _is_plain_role(r)]
    if shared:
        names = ", ".join(f"**{r.name}**" for r in shared[:3])
        more = f" and {len(shared) - 3} more" if len(shared) > 3 else ""
        roles = f"{len(shared)} role{'s' if len(shared) > 1 else ''}: {names}{more}"
        reasons.append((min(20, 4 * len(shared)), random.choice(_SHARED_ROLES).format(roles=roles)))

    # Name colour comes from the highest coloured role.
    a_colour = getattr(a, "colour", None)
    b_colour = getattr(b, "colour", None)
    if a_colour and b_colour and a_colour.value and a_colour.value == b_colour.value:
        top = next(
            (r for r in sorted(a.roles, key=lambda r: getattr(r, "position", 0), reverse=True)
             if getattr(r, "colour", None) and r.colour.value == a_colour.value and _is_plain_role(r)),
            None,
        )
        if top:
            reasons.append((4, random.choice(_SAME_COLOUR).format(role=top.name)))

    if getattr(a, "premium_since", None) and getattr(b, "premium_since", None):
        reasons.append((8, random.choice(_BOOSTERS)))
    return reasons


def _status(a: discord.Member, b: discord.Member) -> list[tuple[int, str]]:
    a_text, b_text = _custom_status(a), _custom_status(b)
    if not a_text or not b_text:
        return []
    emoji = _emojis(a_text) & _emojis(b_text)
    if emoji:
        return [(10, random.choice(_STATUS_EMOJI).format(emoji=sorted(emoji)[0]))]
    words = _words(a_text) & _words(b_text)
    if words:
        return [(10, random.choice(_STATUS_WORDS).format(word=sorted(words)[0]))]
    return []


async def recent_messages(channel, limit: int = HISTORY_LIMIT) -> list:
    """Recent messages in a channel (empty if Maya can't read them)."""
    if channel is None or not hasattr(channel, "history"):
        return []
    try:
        return [message async for message in channel.history(limit=limit)]
    except discord.HTTPException:
        return []


def _chat(messages: list, a: discord.Member, b: discord.Member) -> list[tuple[int, str]]:
    """Replies, pings and favourite emojis between two people in recent messages."""
    talks = 0
    emojis: dict[int, set[str]] = {a.id: set(), b.id: set()}
    for message in messages:
        author_id = message.author.id
        if author_id not in emojis:
            continue
        other_id = b.id if author_id == a.id else a.id
        replied = getattr(getattr(message.reference, "resolved", None), "author", None)
        if (replied and replied.id == other_id) or any(u.id == other_id for u in message.mentions):
            talks += 1
        emojis[author_id] |= _emojis(message.content or "")

    reasons = []
    if talks:
        reasons.append((min(15, 3 * talks), random.choice(_CHATTING).format(n=talks)))
    shared = emojis[a.id] & emojis[b.id]
    if shared:
        reasons.append((5, random.choice(_CHAT_EMOJI).format(emoji=sorted(shared)[0])))
    return reasons


async def _profiles(bot: commands.Bot, a: discord.Member, b: discord.Member) -> list[tuple[int, str]]:
    """Profile colours, banners and animated avatars (needs a profile lookup)."""
    reasons = []
    try:
        ua, ub = await bot.fetch_user(a.id), await bot.fetch_user(b.id)
    except (discord.HTTPException, AttributeError):
        ua = ub = None
    if ua and ub:
        ca, cb = ua.accent_colour, ub.accent_colour
        if ca and cb:
            distance = sum((x - y) ** 2 for x, y in zip(ca.to_rgb(), cb.to_rgb())) ** 0.5
            if distance < 60:
                reasons.append((5, random.choice(_ACCENT)))
        if ua.banner and ub.banner:
            reasons.append((3, random.choice(_BANNERS)))
    a_avatar, b_avatar = getattr(a, "display_avatar", None), getattr(b, "display_avatar", None)
    if a_avatar and b_avatar and a_avatar.is_animated() and b_avatar.is_animated():
        reasons.append((4, random.choice(_ANIMATED)))
    return reasons


def _activity_names(member: discord.Member) -> tuple[set[str], set[str], bool]:
    artists, playing, music = set(), set(), False
    for activity in getattr(member, "activities", ()) or ():
        if isinstance(activity, discord.Spotify):
            music = True
            artists.update(x.strip() for x in activity.artist.split(";"))
        elif getattr(activity, "type", None) in (discord.ActivityType.playing, discord.ActivityType.watching):
            if getattr(activity, "name", None):
                playing.add(activity.name)
    return artists, playing, music


def _right_now(a: discord.Member, b: discord.Member) -> list[tuple[int, str]]:
    reasons = []
    a_artists, a_playing, a_music = _activity_names(a)
    b_artists, b_playing, b_music = _activity_names(b)
    if a_artists & b_artists:
        reasons.append((12, random.choice(_SPOTIFY).format(artist=sorted(a_artists & b_artists)[0])))
    elif a_music and b_music:
        reasons.append((4, random.choice(_BOTH_MUSIC)))
    if a_playing & b_playing:
        reasons.append((12, random.choice(_GAME).format(game=sorted(a_playing & b_playing)[0])))

    a_voice = getattr(a.voice, "channel", None) if getattr(a, "voice", None) else None
    b_voice = getattr(b.voice, "channel", None) if getattr(b, "voice", None) else None
    if a_voice is not None and b_voice is not None and a_voice.id == b_voice.id:
        reasons.append((10, random.choice(_VOICE).format(vc=a_voice.name)))
    elif getattr(a, "is_on_mobile", lambda: False)() and getattr(b, "is_on_mobile", lambda: False)():
        reasons.append((3, random.choice(_MOBILE)))
    elif getattr(a, "status", None) == discord.Status.online and getattr(b, "status", None) == discord.Status.online:
        reasons.append((3, random.choice(_ONLINE)))
    return reasons


def _timing(a: discord.Member, b: discord.Member) -> list[tuple[int, str]]:
    reasons = []
    if a.joined_at and b.joined_at:
        days = abs((a.joined_at - b.joined_at).days)
        if days <= 7:
            when = "on the same day" if days == 0 else f"{days} day{'s' if days > 1 else ''} apart"
            reasons.append((10, random.choice(_SAME_WEEK).format(when=when)))
        elif days <= 60:
            reasons.append((6, random.choice(_SAME_MONTHS).format(days=days)))
    if a.created_at and b.created_at and a.created_at.year == b.created_at.year:
        reasons.append((4, random.choice(_SAME_YEAR).format(year=a.created_at.year)))
    return reasons


def _initials(a: discord.Member, b: discord.Member) -> list[tuple[int, str]]:
    first_a = unicodedata.normalize("NFKC", a.display_name)[:1].lower()
    first_b = unicodedata.normalize("NFKC", b.display_name)[:1].lower()
    if first_a and first_a == first_b and first_a.isalpha():
        return [(3, random.choice(_INITIALS).format(letter=first_a.upper()))]
    return []


async def compatibility(
    a: discord.Member,
    b: discord.Member,
    channel=None,
    bot: commands.Bot | None = None,
    messages: list | None = None,
) -> tuple[int, list[tuple[int, str]]]:
    """Return (percent, reasons). Each reason is (points, text).

    Pass `messages` (from recent_messages) to reuse one history read across many pairs.
    Pass `bot` to include profile checks, which cost two API lookups."""
    base = 25 + _pair_seed(a, b) % 21  # 25-45: their natural chemistry
    reasons = _roles(a, b) + _status(a, b) + _right_now(a, b) + _timing(a, b) + _initials(a, b)
    if messages is None:
        messages = await recent_messages(channel)
    reasons += _chat(messages, a, b)
    if bot is not None:
        reasons += await _profiles(bot, a, b)
    reasons.sort(key=lambda r: -r[0])
    percent = max(1, min(100, base + sum(points for points, _ in reasons)))
    return percent, reasons


def _ship_name(a: str, b: str) -> str:
    return (a[: max(1, len(a) // 2)] + b[len(b) // 2:]).capitalize()


def _bar(percent: int) -> str:
    filled = round(percent / 10)
    return "❤️" * filled + "🖤" * (10 - filled)


def _pick(bands: list[tuple[int, list[str]]], percent: int) -> str:
    return random.choice(next(lines for threshold, lines in bands if percent >= threshold))


class LoveCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(
        name="lovetest",
        aliases=["ship", "love"],
        help="How compatible are two members? Maya explains why",
        usage="@person [@person]",
    )
    async def lovetest(self, ctx: commands.Context, first: discord.Member, second: discord.Member | None = None) -> None:
        if second is None:
            first, second = ctx.author, first
        if first.id == second.id:
            await ctx.send(random.choice(_SELF_LOVE).format(m=first.mention), allowed_mentions=NO_PINGS)
            return
        if self.bot.user and self.bot.user.id in (first.id, second.id):
            other = second if first.id == self.bot.user.id else first
            await ctx.send(random.choice(_MAYA_LOVE).format(m=other.mention), allowed_mentions=NO_PINGS)
            return

        async with ctx.typing():
            percent, reasons = await compatibility(first, second, ctx.channel, self.bot)
        # Sort names so the couple name doesn't change with the order they're mentioned.
        a_name, b_name = sorted((first.display_name, second.display_name), key=str.lower)
        embed = discord.Embed(
            title=f"💘 Love test: {_ship_name(a_name, b_name)}",
            description=(
                f"{first.mention} + {second.mention}\n\n"
                f"**{percent}%** {_bar(percent)}\n*{_pick(_VERDICTS, percent)}*"
            ),
            color=discord.Color.pink(),
        )
        if reasons:
            lines = [f"{text} `+{points}`" for points, text in reasons[:MAX_REASONS]]
            hidden = reasons[MAX_REASONS:]
            if hidden:
                lines.append(f"✨ ...and {len(hidden)} more little things `+{sum(p for p, _ in hidden)}`")
            embed.add_field(name="💭 Why Maya thinks so", value="\n".join(lines)[:1024], inline=False)
        else:
            embed.add_field(name="💭 Why Maya thinks so", value=random.choice(_NOTHING_IN_COMMON), inline=False)
        advice = _pick(_ADVICE, percent).format(a=first.mention, b=second.mention)
        embed.add_field(name="💌 Maya says", value=advice, inline=False)
        await ctx.send(embed=embed)
