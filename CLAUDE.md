# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Discord bot that counts members with specific roles and provides role statistics. It uses discord.py with the commands extension and requires specific Discord Gateway Intents (Server Members Intent and Message Content Intent) to function.

## Running the Bot

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot (requires DISCORD_BOT_TOKEN environment variable)
python role_counter_bot.py
```

The bot reads the Discord token from the `DISCORD_BOT_TOKEN` environment variable, which should be set in a `.env` file (not committed to git).

## Architecture

**Single-file architecture**: All bot logic is in `role_counter_bot.py` (230 lines)

**Bot Commands** (prefix: `!`):
- `!teamstats` - Shows member counts for hardcoded football team roles
- `!rolecount <role_name>` - Counts members with a specific role
- `!allroles` - Lists all server roles with member counts (sorted, max 25 shown)
- `!multirolecount "Role 1" "Role 2"` - Counts multiple roles at once
- `!rolesearch <keyword>` - Searches for roles containing a keyword

**Key Technical Details**:
- Uses Discord Intents: `intents.members = True` and `intents.message_content = True` (both required)
- Hardcoded football team list in `FOOTBALL_TEAMS` constant (lines 13-24)
- Role lookups are case-sensitive using `discord.utils.get()`
- Responses use Discord embeds for formatting
- Error handling for missing arguments and command errors (lines 221-228)

## Configuration

The `FOOTBALL_TEAMS` list is hardcoded in the bot. To add/remove teams, modify lines 13-24 in `role_counter_bot.py`.

## Discord Setup Requirements

When testing or deploying, ensure the Discord bot application has:
1. **Server Members Intent** enabled in Discord Developer Portal
2. **Message Content Intent** enabled in Discord Developer Portal
3. Bot permissions: Read Messages/View Channels, Send Messages, Embed Links
