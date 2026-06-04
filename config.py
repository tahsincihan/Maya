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
]

FOOTBALL_DATA_BASE_URL = "https://api.football-data.org/v4"
PREMIER_LEAGUE_CODE = "PL"
PREDICTIONS_FILE = "predictions.json"
LEGACY_PREDICTIONS_FILE = "pl_predictions.json"

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
}
