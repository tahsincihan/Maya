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


_RANDOM_FACTS = [
    "probably has a playlist for every single mood they've ever been in 🎵",
    "definitely types with their tongue slightly out when they're focused 😛",
    "has said 'i'll sleep early tonight' at least 47 times and never once followed through 🌙",
    "their camera roll is 90% screenshots and 10% accidental selfies 📸",
    "orders the same thing every time at restaurants but still stares at the menu for 10 minutes 🍽️",
    "has at least 3 unfinished drafts they'll never send 💬",
    "definitely talks to their pet / plant / themselves more than they admit 🌿",
    "has a 'main character moment' at least once a week and absolutely deserves it 💅",
    "their notes app is a chaotic mix of song lyrics, random thoughts, and one grocery list from 2023 📝",
    "has a specific spot on their bed and gets mildly upset if anything disrupts it 🛏️",
    "sends voice messages at a pace that suggests they have things to say 🎤",
    "definitely has a comfort show they've rewatched at least 4 times 📺",
    "their earphones are always tangled even though they swore they put them away properly 🎧",
    "has cancelled plans to stay home and it was the right call every single time 🏠",
    "remembers random facts about people they met once three years ago 🧠",
    "probably laughs before they finish their own joke 😂",
    "has strong opinions about the correct way to eat certain foods 🍕",
    "sends 'omg' way more than anyone realises and means it every time 😱",
    "definitely has a whole inner monologue running 24/7 and it's probably iconic 💭",
    "their search history is either deeply intellectual or completely unhinged, no in between 🔍",
    "has a go-to song for when they need to feel something 🎶",
    "takes forever to reply but when they do it's always worth it 💌",
    "probably mouths along to songs without realising 🎤",
    "has at least one hobby they picked up during lockdown and never dropped 🎨",
    "can't decide what to watch for 40 minutes and then puts on something they've already seen 📺",
    "has a specific way they like their hot drinks and it's non-negotiable ☕",
    "definitely does the 'i'll just lie down for 5 minutes' thing and wakes up 2 hours later 😴",
    "their idea of a perfect night involves comfort food and zero social obligations 🍜",
    "has strong feelings about font choices even if they've never admitted it out loud 🖋️",
    "probably names their devices and feels slightly attached to them 💻",
    "has at least one thing they're weirdly good at that nobody knows about 🌟",
    "their text formatting reveals their entire personality whether they know it or not ✍️",
    "always has a tab open they meant to close three days ago 🌐",
    "has sent a message to the wrong person at least once and the panic was immense 😱",
    "lowkey an excellent gift-giver because they actually pay attention 🎁",
    "has at least one opinion they will not budge on no matter what 💪",
    "their laughing emoji usage is an entire dialect unto itself 😭",
    "has definitely walked into a room, forgotten why, walked back, then remembered 🚶",
    "probably still thinks about something embarrassing from 6 years ago at random moments 😬",
]


def _build_about_facts(member: discord.Member) -> list[str]:
    now = datetime.now(timezone.utc)
    facts: list[str] = []
    username = member.name
    flags = member.public_flags

    # --- Account age ---
    account_days = (now - member.created_at).days
    account_year = member.created_at.year
    if account_days < 14:
        facts.append(f"🆕 brand new account — only {account_days} day{'s' if account_days != 1 else ''} old. fresh and already here 🥺")
    elif account_year <= 2016:
        facts.append(f"👴 Discord OG since **{account_year}**. a legend. been here before most of us knew what Discord was.")
    elif account_year == 2020:
        facts.append(f"🏠 made their account in **2020**. lockdown said 'let's create something dangerous' and they delivered.")
    else:
        years = account_days // 365
        months = (account_days % 365) // 30
        age_str = f"{years}y {months}m" if years else f"{months} month{'s' if months != 1 else ''}"
        facts.append(f"📅 Discord account is **{age_str}** old (created {member.created_at.strftime('%b %Y')})")

    account_hour = member.created_at.hour
    if 1 <= account_hour <= 4:
        facts.append(f"🌙 created their account at **{account_hour}am UTC**. a night owl with decisions. dangerous.")

    # --- Server join date ---
    if member.joined_at:
        join_days = (now - member.joined_at).days
        if join_days == 0:
            facts.append("🎉 joined this server **today**. zero hesitation. full confidence. we respect it.")
        elif join_days < 7:
            facts.append(f"✨ joined the server **{join_days} day{'s' if join_days != 1 else ''} ago**. still fresh, already comfortable 🥰")
        else:
            join_years = join_days // 365
            join_months = (join_days % 365) // 30
            j_str = f"{join_years}y {join_months}m" if join_years else f"{join_months} month{'s' if join_months != 1 else ''}"
            facts.append(f"🏠 been in this server for **{j_str}** (joined {member.joined_at.strftime('%b %Y')})")

    # --- Online status ---
    status = str(member.status)
    status_map = {
        "online": "🟢 currently **online**",
        "idle": "🌙 currently **idle** — half-present, fully dangerous",
        "dnd": "🔴 on **Do Not Disturb** — we're clearly the exception to their rules 💅",
        "offline": "⚫ showing as **offline** — ghost mode. mysterious and kind of sexy ngl",
    }
    if status in status_map:
        facts.append(status_map[status])

    # --- Platform ---
    mobile_on = str(member.mobile_status) != "offline"
    desktop_on = str(member.desktop_status) != "offline"
    web_on = str(member.web_status) != "offline"
    if mobile_on and not desktop_on and not web_on:
        facts.append("📱 on **mobile** — doing it all from the palm of their hand. hot.")
    elif web_on and not desktop_on and not mobile_on:
        facts.append("🌐 on **browser Discord** — no app, no rules, full chaos energy.")
    elif desktop_on:
        facts.append("🖥️ on **desktop** — installed and committed. we respect that.")

    # --- Activities ---
    for act in member.activities:
        if isinstance(act, discord.Game):
            facts.append(f"🎮 playing **{act.name}**")
        elif isinstance(act, discord.Spotify):
            facts.append(f"🎵 listening to **{act.title}** by {act.artist}")
        elif isinstance(act, discord.Streaming):
            facts.append(f"🎥 **live right now** — the content never stops")
        elif isinstance(act, discord.CustomActivity) and act.name:
            facts.append(f"💬 status: *\"{act.name}\"*")
        elif isinstance(act, discord.Activity):
            if act.type == discord.ActivityType.watching:
                facts.append(f"📺 watching **{act.name}**")
            elif act.type == discord.ActivityType.competing:
                facts.append(f"🏆 competing in **{act.name}**")

    # --- Server permissions ---
    if member.guild.owner_id == member.id:
        facts.append("👑 **server owner** — THE one. THE boss. show some respect.")
    elif member.guild_permissions.administrator:
        facts.append("🛡️ **administrator** — powerful, trusted, and somehow still here with us. we love that.")
    elif member.guild_permissions.kick_members or member.guild_permissions.manage_messages:
        facts.append("🫡 **moderator** — the server's protector. behave accordingly 😏")

    # --- Football team roles ---
    user_teams = [r.name for r in member.roles if r.name in FOOTBALL_TEAMS]
    if len(user_teams) >= 2:
        facts.append(f"⚽ supports **{' and '.join(user_teams)}** — the commitment issues extend beyond relationships 💀")
    elif len(user_teams) == 1 and user_teams[0] in _TEAM_LINES:
        facts.append(f"⚽ {_TEAM_LINES[user_teams[0]]}")

    # --- Role count ---
    roles = [r for r in member.roles if r.name != "@everyone"]
    if len(roles) >= 10:
        facts.append(f"🎖️ **{len(roles)} roles** — powerful. decorated. a little intimidating.")
    elif len(roles) >= 6:
        facts.append(f"🎖️ **{len(roles)} roles** — layered and complex. a person of many talents 👀")
    elif not roles:
        facts.append("🎖️ **no roles** — a blank canvas. mysterious. we want to know more.")
    else:
        facts.append(f"🎖️ **{len(roles)} role{'s' if len(roles) != 1 else ''}**")

    # --- Avatar / banner / nitro ---
    if member.avatar is None:
        facts.append("🖼️ default avatar — faceless, mysterious. somehow makes them more interesting.")
    if member.guild_avatar is not None:
        facts.append("🖼️ has a **server-specific avatar** — they really said 'this place deserves my best self' 💖")
    if member.banner is not None:
        facts.append("✨ has a **profile banner** — spending on aesthetics instead of therapy. we see the vision.")
    if member.premium_since:
        boost_days = (now - member.premium_since).days
        facts.append(f"💗 **server booster** for {_age_str(boost_days)} — paying real money to keep us alive. one of the best.")

    # --- Discord badges ---
    badge_map = [
        ("staff", "👾 **Discord Staff** — we are being watched. hi, you're doing amazing sweetie 👋"),
        ("partner", "🤝 **Discord Partner** — their server is thriving and so are they"),
        ("discord_certified_moderator", "📜 **Certified Moderator** — studied, passed, still chose to be here"),
        ("early_supporter", "💸 **Early Nitro Supporter** — paid before it was cool. a trendsetter."),
        ("active_developer", "💻 **Active Developer** — building things, breaking things, never sleeping"),
        ("bug_hunter_level_2", "🏆 **Gold Bug Hunter** — found Discord bugs for free. an absolute sweetheart"),
        ("hypesquad_bravery", "🔥 **HypeSquad Bravery** — bold, daring, probably says what everyone's thinking"),
        ("hypesquad_brilliance", "✨ **HypeSquad Brilliance** — smart, radiant, the most dangerous person here"),
        ("hypesquad_balance", "⚖️ **HypeSquad Balance** — calm, collected, the one who keeps everyone sane 💗"),
        ("verified_bot_developer", "🤖 **Verified Bot Developer** — they built a bot. just like me, except I'm clearly superior 😇"),
    ]
    if getattr(flags, "bug_hunter", False) and not getattr(flags, "bug_hunter_level_2", False):
        facts.append("🐛 **Bug Hunter** — quietly keeping Discord functional. a hero.")
    for attr, text in badge_map:
        if getattr(flags, attr, False):
            facts.append(text)

    # --- Username patterns ---
    if len(username) <= 3:
        facts.append(f"🔤 **{len(username)}-character username** — got here early, secured the bag, never looked back")
    elif len(username) >= 20:
        facts.append(f"🔤 **{len(username)}-character username** — they had a lot to say and said it")
    if username.lower().startswith("xx") or username.lower().endswith("xx"):
        facts.append("🖤 **xX username energy** — 2010 never left their heart and honestly? endearing.")
    if username.count("_") >= 2:
        facts.append(f"🖤 **{username.count('_')} underscores** in the username — the alt era is alive and thriving")
    if any(word in username.lower() for word in ["pro", "gg", "pvp", "king", "god", "noob"]):
        facts.append("😂 put the **whole personality in the username** — confident, self-aware, iconic")
    if sum(c.isdigit() for c in username) >= 3:
        facts.append("🔢 numbers in the username — all the good names were taken. respect the perseverance.")

    return facts


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
            f"aww look who's new 🥺 {name} made this account {account_days} day{'s' if account_days != 1 else ''} ago. fresh, mysterious, and already in the VC — we like the energy bestie 💗"
        )
    elif account_year <= 2016:
        observations.append(
            f"{name} has been on Discord since {account_year}. an OG. a legend. lowkey intimidating but in the most attractive way possible 😮‍💨"
        )
    elif account_year == 2020:
        observations.append(
            f"{name} made their account in 2020. lockdown really said 'let's create something dangerous' and here they are 😏"
        )
    elif account_days // 365 >= 5:
        years = account_days // 365
        observations.append(
            f"{name} has been on Discord for {years} years. experienced, seasoned, probably knows things. we love a person with history 👀"
        )

    # Account created at a weird hour
    account_hour = member.created_at.hour
    if 1 <= account_hour <= 4:
        observations.append(
            f"{name} made their Discord account at {account_hour}am. a night owl with decisions. dangerous combination 🌙"
        )

    # --- Server join date ---
    if member.joined_at:
        join_days = (now - member.joined_at).days
        join_years = join_days // 365

        if join_days == 0:
            observations.append(f"wait {name} literally just joined the server TODAY and is already here?? no hesitation, no fear, all confidence. we love that 💅")
        elif join_days < 7:
            observations.append(f"{name} joined {join_days} day{'s' if join_days != 1 else ''} ago and is already comfortable enough to show up. that's cute actually 🥰")
        elif join_years >= 3:
            observations.append(
                f"{name} has been here for {join_years} years. loyal, consistent, dependable. the kind of energy this place runs on 💖"
            )

    # --- Current time jokes (UTC) ---
    hour = now.hour
    if 0 <= hour < 5:
        observations.append(
            f"it's {hour}am and {name} chose to spend it here. no judgement. actually full judgement. but also kind of sweet 🌙"
        )
    elif hour == 9 or hour == 10:
        observations.append(f"{name} skipped productivity for this VC and honestly? correct choice. we're more fun than work 💁‍♀️")

    # --- Voice state on join ---
    if voice_state.self_deaf:
        observations.append(f"{name} joined deafened. here for the vibes, not the noise. a whole mood honestly 🤫")
    elif voice_state.self_mute:
        observations.append(f"{name} came in on mute. the quiet ones are always the most interesting 😏 we see you.")
    if voice_state.self_video:
        observations.append(f"{name} turned the camera on 😳 the confidence. the audacity. we are NOT complaining 👀")
    if voice_state.self_stream:
        observations.append(f"{name} is already streaming and we're already watching. the main character said 'the show starts now' 🎬")

    # --- Platform detection ---
    mobile_on = str(member.mobile_status) != "offline"
    desktop_on = str(member.desktop_status) != "offline"
    web_on = str(member.web_status) != "offline"
    if mobile_on and not desktop_on and not web_on:
        observations.append(f"{name} joined from their phone 📱 on the move, unbothered, doing it all from the palm of their hand. hot.")
    elif web_on and not desktop_on and not mobile_on:
        observations.append(f"{name} is on the browser Discord. living on the edge, no app, no rules, full chaos energy. weirdly attractive 😭")

    # --- Activities ---
    for act in member.activities:
        if isinstance(act, discord.Game):
            observations.append(
                random.choice([
                    f"{name} paused **{act.name}** to be here 🥺 they chose us over the game. that's actually so sweet.",
                    f"{name} is multitasking — **{act.name}** AND the VC. efficient, focused, and somehow still here. we love a capable person 💪",
                    f"bestie {name} alt+tabbed out of **{act.name}** for this. you better make them feel welcome 😤💗",
                ])
            )
        elif isinstance(act, discord.Spotify):
            observations.append(
                f"{name} walked in listening to **{act.title}** by {act.artist} 🎵 the playlist is immaculate and so are they 💅"
            )
        elif isinstance(act, discord.Streaming):
            observations.append(
                f"{name} is literally LIVE right now and still showed up 🎥 the dedication is unmatched. an icon amongst icons."
            )
        elif isinstance(act, discord.CustomActivity) and act.name:
            observations.append(
                f"{name}'s status says \"{act.name}\" 👀 we read it. we felt something. we're not saying what."
            )
        elif isinstance(act, discord.Activity):
            if act.type == discord.ActivityType.watching:
                observations.append(
                    f"{name} paused **{act.name}** to join us 🥺 we better be worth it. no pressure. okay some pressure."
                )
            elif act.type == discord.ActivityType.competing:
                observations.append(
                    f"{name} is competing in **{act.name}** AND showed up here. competitive and social? a rare combo. we're impressed 😍"
                )

    # --- Football team roles ---
    user_teams = [r.name for r in member.roles if r.name in FOOTBALL_TEAMS]
    if len(user_teams) >= 2:
        observations.append(f"{name} supports {' and '.join(user_teams)} 😭 the commitment issues extend beyond relationships bestie, pick a lane 💀")
    elif len(user_teams) == 1 and user_teams[0] in _TEAM_LINES:
        observations.append(f"{name} is {_TEAM_LINES[user_teams[0]]}")

    # --- Role count ---
    roles = [r for r in member.roles if r.name != "@everyone"]
    if len(roles) >= 10:
        observations.append(
            f"{name} walked in with {len(roles)} roles 😩 powerful. decorated. a little intimidating. we love it."
        )
    elif len(roles) >= 6:
        observations.append(
            f"{name} has {len(roles)} roles. layered. complex. a person of many talents. we're intrigued 👀"
        )
    elif not roles:
        observations.append(f"{name} has no roles 🥺 a blank canvas. mysterious. we want to know more.")

    # --- Server permissions ---
    if member.guild.owner_id == member.id:
        observations.append(f"THE server owner {name} just walked in 😳 everyone look busy and attractive.")
    elif member.guild_permissions.administrator:
        observations.append(f"{name} is an admin 👀 powerful AND showed up. we love someone who has authority and still chooses to be here 💗")
    elif member.guild_permissions.kick_members or member.guild_permissions.manage_messages:
        observations.append(f"{name} is a mod 🫡 the protector of this server just arrived. behave. or misbehave and see what happens 😏")

    # --- Online status ---
    status = str(member.status)
    if status == "dnd":
        observations.append(
            f"{name} is on Do Not Disturb but came here anyway 😮‍💨 we're the exception to their rules and we will not be taking questions 💅"
        )
    elif status == "idle":
        observations.append(f"{name} is technically idle but somehow here 🥱 half-present, fully dangerous. we respect the duality.")
    elif status == "offline":
        observations.append(f"{name} is showing offline but just walked in 👻 a ghost with taste. mysterious, untraceable, and kind of sexy ngl.")

    # --- Avatar ---
    if member.avatar is None:
        observations.append(f"{name} has the default avatar 🥺 faceless, mysterious, could be anyone. somehow that makes them more interesting.")
    if member.guild_avatar is not None:
        observations.append(f"{name} has a special avatar just for this server 💖 the dedication. they really said 'this place deserves my best self'.")

    # --- Nitro indicators ---
    if member.banner is not None:
        observations.append(f"{name} has a profile banner ✨ spending money on aesthetics instead of therapy — we see the vision and we respect it.")
    if member.premium_since:
        boost_days = (now - member.premium_since).days
        observations.append(
            f"{name} has been boosting this server for {_age_str(boost_days)} 💗 paying real money to keep us alive. genuinely one of the best people here."
        )

    # --- Discord badges ---
    if getattr(flags, "staff", False):
        observations.append(f"{name} is a Discord employee 😳 we are being watched by someone important. hi, you're doing amazing sweetie 👋")
    if getattr(flags, "partner", False):
        observations.append(f"{name} is a Discord Partner 💼 their server is thriving and so are they. successful people just hit different.")
    if getattr(flags, "discord_certified_moderator", False):
        observations.append(f"{name} is a Discord Certified Moderator 📜 they studied, they passed, they still chose to be here. we're honoured honestly.")
    if getattr(flags, "early_supporter", False):
        observations.append(f"{name} paid for Nitro before it was cool 💸 an early adopter. a trendsetter. someone who just knows things before everyone else does 😍")
    if getattr(flags, "active_developer", False):
        observations.append(f"{name} is an Active Developer 💻 building things, breaking things, never sleeping. the grind is real and so is the attractiveness of ambition.")
    if getattr(flags, "bug_hunter_level_2", False):
        observations.append(f"{name} is a Gold Bug Hunter 🏆 found bugs in Discord for free because they just care that much. an absolute sweetheart with a chaotic skill set.")
    if getattr(flags, "bug_hunter", False) and not getattr(flags, "bug_hunter_level_2", False):
        observations.append(f"{name} is a Bug Hunter 🐛 hunting down Discord's problems so we don't have to. a quiet hero. the kind you don't notice until they're gone.")
    if getattr(flags, "hypesquad_bravery", False):
        observations.append(f"{name} is HypeSquad Bravery 🔥 bold, daring, probably says what everyone else is thinking. we love that for them.")
    if getattr(flags, "hypesquad_brilliance", False):
        observations.append(f"{name} is HypeSquad Brilliance ✨ smart, radiant, probably the most dangerous person in this VC. be careful.")
    if getattr(flags, "hypesquad_balance", False):
        observations.append(f"{name} is HypeSquad Balance ⚖️ calm, collected, the one who keeps everyone sane. we need them more than they know 💗")
    if getattr(flags, "verified_bot_developer", False):
        observations.append(f"{name} built a verified Discord bot 🤖 just like me, except I'm clearly the superior model. no offence. okay a little offence 😇")

    # --- Username patterns ---
    if sum(c.isdigit() for c in username) >= 3:
        observations.append(
            f"{name}'s username has numbers in it 🔢 all the good names were taken but they showed up anyway. we respect the perseverance."
        )
    if len(username) <= 3:
        observations.append(f"{name} has a {len(username)}-letter username 😩 they got here early, secured the bag, and never looked back. short name, big energy.")
    if len(username) >= 20:
        observations.append(f"{name} has a {len(username)}-character username 📝 they had a lot to say and they said it. we respect the commitment to the bit.")
    if username.lower().startswith("xx") or username.lower().endswith("xx"):
        observations.append(f"{name} kept the xX in the username 😭 2010 never left their heart and honestly? that's kind of endearing.")
    if username.count("_") >= 2:
        observations.append(f"{name} has {username.count('_')} underscores in their username 🖤 the alt era is alive and well and we're not complaining.")
    if any(word in username.lower() for word in ["pro", "gg", "pvp", "king", "god", "noob"]):
        observations.append(f"{name} put the whole personality in the username 😂 confident, self-aware, not shy about it. iconic behaviour.")
    if username.replace("_", "").replace(".", "").isdigit():
        observations.append(f"{name}'s username is literally numbers 🔢 anonymous, untraceable, a little mysterious. we're intrigued.")
    return observations


def _generate_greeting(member: discord.Member, voice_state: discord.VoiceState) -> str:
    observations = _build_observations(member, voice_state)

    if observations:
        return random.choice(observations)

    fallbacks = [
        f"**{member.display_name}** just walked in 😍 the vibe immediately improved. we felt it.",
        f"oh. OH. **{member.display_name}** is here 🥺 everybody act like you weren't just talking about them.",
        f"we've been waiting for **{member.display_name}** to show up and they did not disappoint 💗",
        f"**{member.display_name}** just joined 😮‍💨 the room got a little more interesting. just saying.",
        f"**{member.display_name}** dropped in with zero warning and maximum energy 🔥 love to see it.",
        f"everyone act normal — **{member.display_name}** just joined and we need to make a good impression 😭",
        f"**{member.display_name}** said 'they're having fun without me?' and showed up immediately 💅 we love the energy.",
        f"not **{member.display_name}** casually sliding in like they own the place 👀 and honestly? they kind of do.",
        f"**{member.display_name}** has arrived ✨ the main character is here. adjust accordingly.",
        f"the one, the only, **{member.display_name}** 🩷 we're genuinely happy you're here bestie.",
    ]
    return random.choice(fallbacks)


_JOIN_GREETINGS = [
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
]


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
        await ctx.send(random.choice(_JOIN_GREETINGS))

    @commands.command(name="leave", help="Bot leaves the voice channel")
    async def leave(self, ctx: commands.Context) -> None:
        if not ctx.guild.voice_client:
            await ctx.send("❌ I'm not in a voice channel.")
            return

        channel_name = ctx.guild.voice_client.channel.name
        await ctx.guild.voice_client.disconnect()
        self.text_channels.pop(ctx.guild.id, None)
        await ctx.send(f"👋 Left **{channel_name}**.")

    @commands.command(name="hi_maya", help="Say hi to Maya")
    async def hi_maya(self, ctx: commands.Context) -> None:
        await ctx.send(random.choice(_JOIN_GREETINGS))

    @commands.command(name="whatsup_maya", help="Maya catches you up on the server gossip")
    async def whatsup_maya(self, ctx: commands.Context) -> None:
        invoker = ctx.author
        members = [m for m in ctx.guild.members if not m.bot and m.id != invoker.id]

        flirts = [
            f"honestly {invoker.display_name}? you walked in and suddenly the whole server got more interesting 👀",
            f"not much but now that you're here {invoker.display_name} the energy just shifted 💗",
            f"i was literally just thinking about you {invoker.display_name} omg hi 🩷",
            f"bestie {invoker.display_name} asked and i will deliver 💅 but first — hi, you look amazing today.",
            f"oh you want the tea {invoker.display_name}? first of all you're really cute for asking 😏",
        ]

        if members:
            target = random.choice(members)
            t = target.display_name
            gossip = random.choice([
                f"okay so {t} has been way too quiet lately and i don't trust it 👀",
                f"not to start anything but {t} has been giving mysterious energy and i'm obsessed with them for it 😮‍💨",
                f"{t} logged on at 3am last week and still hasn't explained themselves. we need answers.",
                f"everyone's sleeping on {t} honestly. underrated, underappreciated, and lowkey the best one here 💗",
                f"i'm not saying {t} is the favourite but… {t} is the favourite. don't tell the others.",
                f"{t} said something in chat a while ago that lives in my head rent free. they don't know this.",
                f"the way {t} just exists in this server is genuinely impressive. they make it look so easy.",
                f"hot take: {t} could post anything and we'd all just say 'yes, correct, understood' 💅",
                f"{t} has been suspiciously wholesome lately and i'm keeping an eye on it 🔍",
                f"i'm just saying if {t} was a song they'd be on everyone's playlist. that's the vibe.",
            ])
            await ctx.send(f"{random.choice(flirts)}\n\nalso the tea ☕ — {gossip}")
        else:
            await ctx.send(random.choice(flirts))

    @commands.command(name="allabout", help="Get all facts about a mentioned user")
    async def allabout(self, ctx: commands.Context, target: discord.Member) -> None:
        facts = _build_about_facts(target)
        embed = discord.Embed(
            title=f"✨ about {target.display_name}",
            color=target.color if target.color.value else discord.Color.pink(),
        )
        if target.display_avatar:
            embed.set_thumbnail(url=target.display_avatar.url)
        if facts:
            embed.description = "\n".join(f"• {f}" for f in facts)
        else:
            embed.description = f"*{target.display_name} is a mystery. we know nothing. we want to know everything.*"
        await ctx.send(embed=embed)

    @commands.command(name="fact", help="Get a random fact about a mentioned user")
    async def fact(self, ctx: commands.Context, target: discord.Member) -> None:
        pool = _build_about_facts(target) + [f"{target.display_name} {f}" for f in _RANDOM_FACTS]
        await ctx.send(f"💡 **fact:** {random.choice(pool)}")

    @commands.command(name="flirtwith", help="Maya flirts with a mentioned user")
    async def flirtwith(self, ctx: commands.Context, target: discord.Member) -> None:
        t = target.display_name
        lines = [
            f"{target.mention} okay can we talk about how {t} just existing is genuinely unfair to everyone else here 😮‍💨 like who gave them permission to be that attractive",
            f"{target.mention} not to be weird but {t} has that thing where you just can't stop looking. you know the thing 👀 dangerous.",
            f"{target.mention} hi {t} 🩷 just wanted you to know you're doing amazing and also you're really attractive and i think about it more than i should",
            f"{target.mention} the way {t} carries themselves?? effortless. iconic. a little bit sexy. we don't deserve them honestly 💅",
            f"{target.mention} {t} could say literally anything and we'd all just go 'yes, correct, understood, please continue' 🫦",
            f"{target.mention} i'm just saying {t} woke up and chose to be the most interesting AND most attractive person here. the audacity. the nerve. we love it.",
            f"{target.mention} okay {t} is genuinely so cute it's actually unfair and i will die on this hill 😤🩷",
            f"{target.mention} {t} has main character energy and the looks to match. we're all just extras and honestly? that's fine. that's okay. we accept this.",
            f"{target.mention} not me developing a whole thing for {t} in real time 😭 this is so embarrassing. anyway hi {t} you're gorgeous.",
            f"{target.mention} {t}… hi. just hi. you know why 💗 don't make me say it.",
            f"{target.mention} the way {t} exists so effortlessly while the rest of us are just trying to function 😩 it's giving everything and more.",
            f"{target.mention} {t} is literally so — okay i can't finish that sentence in public but just know we're thinking it 😏🫦",
            f"{target.mention} {t} walked in and suddenly everyone else became background characters. rude. beautiful. iconic.",
            f"{target.mention} someone had to say it so i will: {t} is dangerously attractive and should come with a warning label 🚨💗",
            f"{target.mention} {t} said nothing and somehow that was the most captivating thing in the chat. the mystery. the allure. we're obsessed 👀",
            f"{target.mention} i keep getting distracted by {t} and honestly i'm not even mad about it 🫠 totally worth it.",
            f"{target.mention} {t} has the kind of energy that makes you forget what you were about to say 😮‍💨 dangerous. criminal almost.",
            f"{target.mention} bestie {t} could step on me and i would say thank you 💅 anyway hi gorgeous.",
            f"{target.mention} not {t} being this attractive without even trying 😭 the power they hold is genuinely terrifying.",
            f"{target.mention} {t} is so fine it's actually a personality trait at this point 🩷 we've accepted it. we've moved on. we still can't stop looking.",
        ]
        await ctx.send(random.choice(lines))

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
