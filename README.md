# Discord Role Counter Bot

A Discord bot that counts members with specific roles and provides role statistics.

## Features

- **!helpmaya** - List all commands and usage
- **!teamstats** - Show member counts for configured football team roles
- **!rolecount <role_name>** - Count members with a specific role
- **!allroles** - List all server roles with member counts (sorted by popularity)
- **!multirolecount "Role 1" "Role 2"** - Count members for multiple roles at once
- **!rolesearch <keyword>** - Search for roles containing a keyword
- **!results [league] [matchday]** (alias: `!plweek`) - Matchweek results (requires API token)
- **!myteam** (aliases: `!myfixtures`, `!mygames`) - Upcoming fixtures for your team roles (Premier League, La Liga, Serie A, Bundesliga, Ligue 1)
- **!fixtures [league] [matchday]** (alias: `!plfixtures`) - Upcoming fixtures with match IDs
- **!predict <match_id> <home|away|draw>** (alias: `!plpredict`) - Predict a match outcome
- **!mypicks** (aliases: `!plmypicks`, `!plpicks`) - Show your prediction picks
- **!leaderboard** (alias: `!plleaderboard`) - Prediction leaderboard (2 pts per correct outcome)

## Setup Instructions

### 1. Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" tab and click "Add Bot"
4. Under "Privileged Gateway Intents", enable:
   - **Server Members Intent** (Required!)
   - **Message Content Intent** (Required!)
5. Click "Reset Token" and copy your bot token
6. Keep this token secret!

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the Bot

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your bot token:
   ```
   DISCORD_BOT_TOKEN=your_actual_bot_token_here
   ```

3. (Optional) If you want fixtures/results and predictions, add a football-data.org API token:
   ```
   FOOTBALL_DATA_TOKEN=your_football_data_api_token_here
   ```

### 4. Invite Bot to Your Server

1. In Discord Developer Portal, go to "OAuth2" > "URL Generator"
2. Select scopes:
   - `bot`
3. Select bot permissions:
   - Read Messages/View Channels
   - Send Messages
   - Embed Links
4. Copy the generated URL and open it in your browser
5. Select your server and authorize the bot

### 5. Run the Bot

```bash
python role_counter_bot.py
```

Or if you want to run it in the background:

```bash
nohup python role_counter_bot.py &
```

## Usage Examples

### Show help
```
!helpmaya
!helpmaya predict
```

### Count a specific role
```
!rolecount Moderator
```

### List all roles
```
!allroles
```

### Count multiple roles
```
!multirolecount "Admin" "Moderator" "VIP"
```

### Search for roles
```
!rolesearch member
```
This will find roles like "Member", "Team Member", "Premium Member", etc.

### Matchweek results
```
!results
```
Or specify a league and matchweek:
```
!results laliga 5
```

### Fixtures and predictions
```
!myteam
!fixtures
!predict 123456 home
!mypicks
!leaderboard
```

## Troubleshooting

### Bot doesn't respond
- Make sure the bot has "Send Messages" permission in the channel
- Check that Message Content Intent is enabled in Developer Portal
- Verify the bot is online (check your terminal for "has connected to Discord!")

### "Role not found" errors
- Role names are case-sensitive
- Use quotes for roles with spaces: `!rolecount "My Role"`
- Use `!allroles` to see exact role names

### Member counts show 0
- Make sure Server Members Intent is enabled in Developer Portal
- Wait a few minutes after bot starts for member cache to populate
- Restart the bot after enabling intents

## Security Notes

- Never share your bot token
- Add `.env` to `.gitignore` if using version control
- Use environment variables for production deployments

## For Production

Consider using:
- **systemd** for Linux servers to auto-restart
- **PM2** for Node.js-style process management
- **Docker** for containerized deployment
- **Railway/Heroku** for cloud hosting
