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
- `cogs/voice.py` — `VoiceCog`: voice channel join/leave and the flirty "fun facts about a member" commands
- `cogs/welcome.py` — `WelcomeCog`: greets new members on join
- `cogs/help.py` — `HelpCog`: `!helpmaya`, backed by `help_content.py`

Shared config (football team list, competition codes/aliases, file paths) lives in `config.py`. Shared formatting/lookup helpers live in `helpers.py`.

**Key Technical Details**:
- Intents required: `members`, `message_content`, `voice_states`, `presences`
- Role lookups are case-sensitive using `discord.utils.get()`
- Responses use Discord embeds for formatting
- Command errors are handled centrally in `maya_bot.py`'s `on_command_error`
- Logs go to stdout and `bot.log` (gitignored)

## Configuration

The `FOOTBALL_TEAMS` list, competition codes/aliases, and predictions file paths are in `config.py`. To add/remove supported teams, edit that list.

## Discord Setup Requirements

When testing or deploying, ensure the Discord bot application has:
1. **Server Members Intent** enabled in Discord Developer Portal
2. **Message Content Intent** enabled in Discord Developer Portal
3. Bot permissions: Read Messages/View Channels, Send Messages, Embed Links, Connect/Speak (for voice commands)
