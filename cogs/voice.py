import random
from datetime import datetime, timezone

import discord
from discord.ext import commands

from config import FOOTBALL_TEAMS

_TEAM_LINES: dict[str, str] = {
    "Man United": "A Man United fan. They've been 'rebuilding' since 2013.",
    "Arsenal": "An Arsenal fan. Always top 4 in December, always gone by March.",
    "Liverpool": "A Liverpool fan. You'll Never Walk Alone — especially in the title race lately.",
    "Chelsea": "A Chelsea fan. Their squad costs more than most countries' GDP.",
    "Man City": "A Man City fan. Must be nice winning everything.",
    "Juventus": "A Juve fan. Still waiting for that Champions League trophy.",
    "Real Madrid": "A Real Madrid fan. The CL trophy room is basically a second home.",
    "Barcelona": "A Barça fan. Still living off memories of 2009–2015.",
    "Bayern Munich": "A Bayern fan. The Bundesliga must be a fun competition for the other 17 clubs.",
    "PSG": "A PSG fan. Bought every player in the world and still can't win the CL.",
}


def _age_str(days: int) -> str:
    if days < 30:
        return f"{days} day{'s' if days != 1 else ''}"
    elif days < 365:
        m = days // 30
        return f"{m} month{'s' if m != 1 else ''}"
    else:
        y = days // 365
        m = (days % 365) // 30
        y_str = f"{y} year{'s' if y != 1 else ''}"
        if m:
            return f"{y_str} and {m} month{'s' if m != 1 else ''}"
        return y_str


def _build_observations(member: discord.Member, voice_state: discord.VoiceState) -> list[str]:
    name = f"**{member.display_name}**"
    now = datetime.now(timezone.utc)
    observations: list[str] = []
    username = member.name
    flags = member.public_flags

    # --- Account age ---
    account_days = (now - member.created_at).days
    account_year = member.created_at.year

    if account_days < 14:
        observations.append(
            f"Fresh account alert 🚨 {name} made their account {account_days} day{'s' if account_days != 1 else ''} ago. Who are you running from?"
        )
    elif account_year <= 2016:
        observations.append(
            f"{name} has been on Discord since {account_year}. They were here before the rebrand, before Nitro, before all of it."
        )
    elif account_year == 2020:
        observations.append(
            f"{name} made their Discord account in 2020. We all know what everyone was doing during lockdown."
        )
    elif account_days // 365 >= 5:
        years = account_days // 365
        observations.append(
            f"{name} has been on Discord for {years} years. At this point Discord is basically their home."
        )

    # Account created at a weird hour (UTC)
    account_hour = member.created_at.hour
    if 1 <= account_hour <= 4:
        observations.append(
            f"{name} created their Discord account at {account_hour}am UTC. Whatever they were doing that night, it led here."
        )

    # --- Server join date ---
    if member.joined_at:
        join_days = (now - member.joined_at).days
        join_years = join_days // 365

        if join_days == 0:
            observations.append(f"{name} joined the server today. Give them 10 minutes before they ask for mod.")
        elif join_days < 7:
            observations.append(f"{name} joined the server {join_days} day{'s' if join_days != 1 else ''} ago. Still fresh.")
        elif join_years >= 3:
            observations.append(
                f"{name} has been in this server for {join_years} years. They've seen things the rest of us can't even imagine."
            )

    # --- Current time jokes (UTC) ---
    hour = now.hour
    if 0 <= hour < 5:
        observations.append(
            f"It's {hour}am UTC and {name} just joined a Discord VC. The schedule is cooked."
        )
    elif hour == 9 or hour == 10:
        observations.append(f"{name} is in a Discord VC during work hours. Totally fine. Very normal.")

    # --- Voice state on join ---
    if voice_state.self_deaf:
        observations.append(f"{name} joined but immediately deafened themselves. Why are you even here?")
    elif voice_state.self_mute:
        observations.append(f"{name} joined muted. The silent observer has entered.")
    if voice_state.self_video:
        observations.append(f"{name} turned their camera on. Brave. Very brave.")
    if voice_state.self_stream:
        observations.append(f"{name} is already streaming. The content never stops.")

    # --- Platform detection ---
    mobile_on = str(member.mobile_status) != "offline"
    desktop_on = str(member.desktop_status) != "offline"
    web_on = str(member.web_status) != "offline"
    if mobile_on and not desktop_on and not web_on:
        observations.append(f"{name} joined from their phone. Absolute unit of a mobile user.")
    elif web_on and not desktop_on and not mobile_on:
        observations.append(f"{name} is on the browser version of Discord. They never downloaded the app.")

    # --- Activities ---
    for act in member.activities:
        if isinstance(act, discord.Game):
            observations.append(
                random.choice([
                    f"{name} paused **{act.name}** to join this VC. Respect.",
                    f"Still playing **{act.name}** while in VC? Bold strategy, {name}.",
                    f"{name} Alt+Tabbed out of **{act.name}** for this. Hope it was worth it.",
                ])
            )
        elif isinstance(act, discord.Spotify):
            observations.append(
                f"{name} is listening to **{act.title}** by {act.artist} and decided to multitask. We see you."
            )
        elif isinstance(act, discord.Streaming):
            observations.append(
                f"{name} is literally live right now and still joined the VC. The dedication is unreal."
            )
        elif isinstance(act, discord.CustomActivity) and act.name:
            observations.append(
                f"{name}'s status says \"{act.name}\". Noted."
            )
        elif isinstance(act, discord.Activity):
            if act.type == discord.ActivityType.watching:
                observations.append(
                    f"{name} is watching **{act.name}** and still found time to join the VC. Multitasker."
                )
            elif act.type == discord.ActivityType.competing:
                observations.append(
                    f"{name} is competing in **{act.name}**. The competitive spirit never rests."
                )

    # --- Football team roles ---
    user_teams = [r.name for r in member.roles if r.name in FOOTBALL_TEAMS]
    if len(user_teams) >= 2:
        observations.append(f"{name} supports {' and '.join(user_teams)}. Pick a lane.")
    elif len(user_teams) == 1 and user_teams[0] in _TEAM_LINES:
        observations.append(f"{name} is {_TEAM_LINES[user_teams[0]]}")

    # --- Role count ---
    roles = [r for r in member.roles if r.name != "@everyone"]
    if len(roles) >= 10:
        observations.append(
            f"{name} has {len(roles)} roles. At this point they're just collecting them."
        )
    elif len(roles) >= 6:
        observations.append(
            f"{name} is carrying {len(roles)} roles. Some people collect stamps, some collect Discord roles."
        )
    elif not roles:
        observations.append(f"{name} has zero roles. A ghost among us.")

    # --- Server permissions ---
    if member.guild.owner_id == member.id:
        observations.append(f"{name} is the server owner. Show some respect.")
    elif member.guild_permissions.administrator:
        observations.append(f"{name} is an admin. Everybody behave.")
    elif member.guild_permissions.kick_members or member.guild_permissions.manage_messages:
        observations.append(f"{name} is a mod. Act natural.")

    # --- Online status ---
    status = str(member.status)
    if status == "dnd":
        observations.append(
            f"{name} is on Do Not Disturb but joined the VC anyway. The rules simply do not apply."
        )
    elif status == "idle":
        observations.append(f"{name} is idle but somehow here. Schrödinger's presence.")
    elif status == "offline":
        observations.append(f"{name} appears offline but is very much here. Ghost mode activated.")

    # --- Avatar ---
    if member.avatar is None:
        observations.append(f"{name} never changed their default avatar. A person of pure mystery.")
    if member.guild_avatar is not None:
        observations.append(f"{name} has a server-specific avatar just for this server. Committed.")

    # --- Nitro indicators ---
    if member.banner is not None:
        observations.append(f"{name} has a profile banner. Nitro money well spent.")
    if member.premium_since:
        boost_days = (now - member.premium_since).days
        observations.append(
            f"{name} has been boosting this server for {_age_str(boost_days)}. A true patron of the people."
        )

    # --- Nickname ---
    if member.nick:
        observations.append(
            f"{name} goes by **{member.nick}** in this server. What are they hiding?"
        )

    # --- Discord badges ---
    if getattr(flags, "staff", False):
        observations.append(f"{name} is a Discord employee. We are being monitored.")
    if getattr(flags, "partner", False):
        observations.append(f"{name} is a Discord Partner. Their server is doing numbers.")
    if getattr(flags, "discord_certified_moderator", False):
        observations.append(f"{name} is a Discord Certified Moderator. Professionally trained to deal with chaos.")
    if getattr(flags, "early_supporter", False):
        observations.append(f"{name} is an Early Nitro Supporter. Paid for Discord before it was cool.")
    if getattr(flags, "active_developer", False):
        observations.append(f"{name} is an Active Developer — they probably have 40 unfinished side projects.")
    if getattr(flags, "bug_hunter_level_2", False):
        observations.append(f"{name} is a Gold Bug Hunter. Finds Discord bugs for free. An icon.")
    if getattr(flags, "bug_hunter", False) and not getattr(flags, "bug_hunter_level_2", False):
        observations.append(f"{name} hunts Discord bugs. Someone has to do it.")
    if getattr(flags, "hypesquad_bravery", False):
        observations.append(f"{name} is HypeSquad Bravery. Bold choice, very bold.")
    if getattr(flags, "hypesquad_brilliance", False):
        observations.append(f"{name} is HypeSquad Brilliance. The quiz said smart, we'll see.")
    if getattr(flags, "hypesquad_balance", False):
        observations.append(f"{name} is HypeSquad Balance. True neutral energy.")
    if getattr(flags, "verified_bot_developer", False):
        observations.append(f"{name} is a Verified Bot Developer. They built a bot. Just like this one. Meta.")

    # --- Username patterns ---
    if sum(c.isdigit() for c in username) >= 3:
        observations.append(
            f"{name}'s username has a string of numbers in it — classic 'all the good names were taken' moment."
        )
    if len(username) <= 3:
        observations.append(f"{name} secured a {len(username)}-character username. They were early and they were ready.")
    if len(username) >= 20:
        observations.append(f"{name} has a {len(username)}-character username. They had a lot to say.")
    if username.lower().startswith("xx") or username.lower().endswith("xx"):
        observations.append(f"{name}'s username has the xX treatment. A true gamer.")
    if username.count("_") >= 2:
        observations.append(f"{name} has {username.count('_')} underscores in their username. The alt-account aesthetic is real.")
    if any(word in username.lower() for word in ["pro", "gg", "pvp", "king", "god", "noob"]):
        observations.append(f"{name} put it right in the username. They want you to know.")
    if username.replace("_", "").replace(".", "").isdigit():
        observations.append(f"{name}'s username is basically just a number. Bold.")
    if username != member.display_name and not member.nick:
        observations.append(f"{name} changed their global display name. Reinvention arc.")

    return observations


def _generate_greeting(member: discord.Member, voice_state: discord.VoiceState) -> str:
    observations = _build_observations(member, voice_state)

    if observations:
        return random.choice(observations)

    fallbacks = [
        f"**{member.display_name}** just entered the VC. The energy has shifted.",
        f"**{member.display_name}** is here. Everybody act natural.",
        f"The legend **{member.display_name}** has arrived.",
        f"**{member.display_name}** joins the call. Silence.",
        f"Oh, it's **{member.display_name}**. Everyone pretend you were talking about something interesting.",
        f"**{member.display_name}** has entered. Adjust your behavior accordingly.",
        f"**{member.display_name}** just dropped in. No context, no explanation.",
    ]
    return random.choice(fallbacks)


class VoiceCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.text_channels: dict[int, discord.TextChannel] = {}

    @commands.command(name="join", help="Bot joins your current voice channel")
    async def join(self, ctx: commands.Context) -> None:
        if not ctx.author.voice:
            await ctx.send("❌ You're not in a voice channel. Join one first.")
            return

        channel = ctx.author.voice.channel

        if ctx.guild.voice_client:
            await ctx.guild.voice_client.move_to(channel)
        else:
            await channel.connect()

        self.text_channels[ctx.guild.id] = ctx.channel
        await ctx.send(random.choice([
            "hiii 🩷",
            "heyyy bestiesss",
            "omg hii",
            "what's good 💅",
            "heyy sweeties",
            "hiii i'm here don't mind me",
            "HIII 🫶",
            "omg yay hii",
            "hey babes 💗",
            "heyy heyy heyy",
            "hiiii missed u guys 🩷",
            "omg finally hii",
            "heyyy lovelies",
            "hii everyone 🫶",
            "omg hii! I missed Omee so much!",
        ]))

    @commands.command(name="leave", help="Bot leaves the voice channel")
    async def leave(self, ctx: commands.Context) -> None:
        if not ctx.guild.voice_client:
            await ctx.send("❌ I'm not in a voice channel.")
            return

        channel_name = ctx.guild.voice_client.channel.name
        await ctx.guild.voice_client.disconnect()
        self.text_channels.pop(ctx.guild.id, None)
        await ctx.send(f"👋 Left **{channel_name}**.")

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        if member.id == self.bot.user.id and after.channel is None:
            self.text_channels.pop(member.guild.id, None)
            return

        if member.bot:
            return

        voice_client = member.guild.voice_client
        if not voice_client:
            return

        joined_bots_channel = (
            after.channel is not None
            and after.channel.id == voice_client.channel.id
            and (before.channel is None or before.channel.id != voice_client.channel.id)
        )
        if not joined_bots_channel:
            return

        text_channel = self.text_channels.get(member.guild.id)
        if not text_channel:
            return

        await text_channel.send(_generate_greeting(member, after))
