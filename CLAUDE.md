# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Maya is a Discord bot built with discord.py. It counts members with specific roles, reports role statistics, tracks football (soccer) fixtures/results/predictions via the football-data.org API, provides voice-channel utilities, and posts welcome messages for new members. It requires the **Server Members**, **Message Content**, and **Voice State** Discord Gateway Intents to function.

## Running the Bot

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot (requires DISCORD_BOT_TOKEN environment variable, set via .env)
python maya_bot.py
```

The bot reads secrets from environment variables loaded via `python-dotenv` from a `.env` file (not committed to git; see `.env.example` for the expected keys). `FOOTBALL_DATA_TOKEN` is optional and only needed for the fixtures/results/predictions commands.

## Architecture

The entry point `maya_bot.py` builds the `commands.Bot` instance, configures intents/logging, starts the Flask keep-alive server (`keep_alive.py`, for free-tier hosts that need an HTTP port to stay awake), and registers cogs from `cogs/`:

- `cogs/roles.py` — `RolesCog`: `!teamstats`, `!rolecount`, `!allroles`, `!multirolecount`, `!rolesearch`
- `cogs/football.py` — `FootballCog`: `!results`/`!plweek`, `!myteam`/`!myfixtures`/`!mygames`, `!fixtures`/`!plfixtures` (calls the football-data.org API)
- `cogs/predictions.py` — `PredictionsCog`: `!predict`/`!plpredict`, `!mypicks`, `!leaderboard`; persists picks via `predictions_store.py` to `predictions.json` (gitignored — runtime state, not tracked)
- `cogs/league.py` — `LeagueCog`: `!league` Me & The Boys League (name set by `LEAGUE_NAME` in `config.py`; members score their team's real league W/D/L this season, from the standings endpoint) and `!leaguetable`/`!leaguechannel` (a pinned live table). A nightly task (23:30 UTC) edits that message in place and posts a recap when a supported team has played. Its buttons are a persistent `LiveTableView` (fixed `custom_id`s, registered with `bot.add_view` in `cog_load`) that open an ephemeral `LeagueView` per user. Standings are cached for 30 min. Channel, message id and last-seen records persist to `league.json` (gitignored). Table rendering, page buttons and the team menu live in `cogs/league_view.py`
- `cogs/love.py` — `LoveCog`: `!lovetest`/`!ship`/`!love`; async `compatibility()` scores a pair from a stable per-pair base plus points for non-football shared roles/name colour/boosting, custom-status overlap, recent replies/pings and shared emojis in the channel (reads the last 300 messages), profile accent colour/banners/animated avatars (via `fetch_user`), current activity/voice/mobile, join dates and initials. Deliberately no football. Wording is randomised; the score is not
- `cogs/fun.py` — `FunCog`: `!banter` (teases fans before the next fixture)
- `cogs/voice.py` — `VoiceCog`: voice channel join/leave and the flirty "fun facts about a member" commands
- `cogs/welcome.py` — `WelcomeCog`: greets new members on join
- `cogs/admin.py` — `AdminCog`: `!sendto #channel <command>` (Manage Server) copies the message, points it at the target channel and invokes the command there; only names in `SENDTO_COMMANDS` (`config.py`) are allowed, and errors are reported back in the admin channel
- `cogs/flirt.py` — `FlirtCog`: `!match`/`!mymatch` (love-tests a person against recently active members; reuses one history read, profile checks only for the top 5), `!rizz`, `!date`, and Couple of the Day (`!coupleoftheday`, daily task at 18:00 UTC). Tracks who's been active via `on_message` (in memory). `MATCH_ROLE_PAIRS`/`MATCH_PAIR_CHANCE` in `config.py` make both usually pair opposite sides (e.g. broski × pookie, matched by role-name substring)
- `cogs/marriage.py` — `MarriageCog`: `!marry` (ProposalView with Yes/No, 10 min), `!divorce`, `!couples`
- `cogs/anonymous.py` — `AnonymousCog`: `!confess` (deletes the command in servers and refuses to post if it can't), `!confessions`/`!whoconfessed` (admins), `!secretadmirer` (DM with a hint) and `!noadmirers`
- Flirty state (couples, channels, confession/admirer logs, opt-outs) persists via `flirt_store.py` to `flirt.json` (gitignored)
- `cogs/help.py` — `HelpCog`: `!helpmaya`, backed by `help_content.py`

Shared config (football team list, competition codes/aliases, file paths) lives in `config.py`. Shared formatting/lookup helpers live in `helpers.py`.

**Key Technical Details**:
- Intents required: `members`, `message_content`, `voice_states`, `presences`
- Role lookups are case-sensitive using `discord.utils.get()`
- Responses use Discord embeds for formatting
- Command errors are handled centrally in `maya_bot.py`'s `on_command_error`
- Logs go to stdout and `bot.log` (gitignored)

## Configuration

The `FOOTBALL_TEAMS` list, competition codes/aliases, and predictions file paths are in `config.py`. To add/remove supported teams, edit that list (and give new teams a 3-letter code in `TEAM_CODES` for the league table).

## Discord Setup Requirements

When testing or deploying, ensure the Discord bot application has:
1. **Server Members Intent** enabled in Discord Developer Portal
2. **Message Content Intent** enabled in Discord Developer Portal
3. Bot permissions: Read Messages/View Channels, Send Messages, Embed Links, Connect/Speak (for voice commands)
