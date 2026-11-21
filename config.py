FOOTBALL_TEAMS = [
    "Man United",
    "Bayern Munich",
    "Real Madrid",
    "Juventus",
    "Barcelona",
    "Liverpool",
    "Arsenal",
    "Man City",
    "Chelsea",
    "PSG",
    "Atlético Madrid",
]

FOOTBALL_DATA_BASE_URL = "https://api.football-data.org/v4"
PREMIER_LEAGUE_CODE = "PL"
PREDICTIONS_FILE = "predictions.json"
LEGACY_PREDICTIONS_FILE = "pl_predictions.json"
LEAGUE_FILE = "league.json"
LEAGUE_NAME = "Me & The Boys League"
FLIRT_FILE = "flirt.json"

COMPETITIONS = {
    "PL": "Premier League",
    "PD": "La Liga",
    "SA": "Serie A",
    "BL1": "Bundesliga",
    "FL1": "Ligue 1",
}

COMPETITION_ALIASES = {
    "premierleague": "PL",
    "premier": "PL",
    "epl": "PL",
    "england": "PL",
    "laliga": "PD",
    "seriea": "SA",
    "bundesliga": "BL1",
    "ligue1": "FL1",
}

# Map API team names to local role names when they differ.
TEAM_NAME_MAP = {
    "Manchester United FC": "Man United",
    "Manchester City FC": "Man City",
    "Liverpool FC": "Liverpool",
    "Arsenal FC": "Arsenal",
    "Chelsea FC": "Chelsea",
    "FC Bayern München": "Bayern Munich",
    "Club Atlético de Madrid": "Atlético Madrid",
    "Atleti": "Atlético Madrid",
}

# Commands admins can run in another channel with !sendto (by their main name).
SENDTO_COMMANDS = {
    "lovetest",
    "flirtwith",
    "fact",
    "allabout",
    "hi_maya",
    "whatsup_maya",
    "banter",
    "match",
    "rizz",
    "date",
    "couples",
    "coupleoftheday",
}

# !match and Couple of the Day usually pair someone from one side with the other side.
# Matched by role name, ignoring case, so "🧢 Broski" counts as broski.
MATCH_ROLE_PAIRS = [("broski", "pookie")]
MATCH_PAIR_CHANCE = 0.75  # how often Maya sticks to these pairings (0 = never, 1 = always)
