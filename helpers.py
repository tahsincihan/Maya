import unicodedata
from datetime import datetime

import aiohttp
import discord

from config import COMPETITIONS, COMPETITION_ALIASES, PREMIER_LEAGUE_CODE, TEAM_NAME_MAP


def _normalize_team_name(team_name: str) -> str:
    cleaned = team_name.strip()
    cleaned = unicodedata.normalize("NFKD", cleaned)
    cleaned = "".join(ch for ch in cleaned if not unicodedata.combining(ch))

    prefixes = (
        "FC ",
        "CF ",
        "SC ",
        "AC ",
        "AS ",
        "RC ",
        "RCD ",
        "RB ",
        "SS ",
        "UD ",
        "CD ",
        "CA ",
        "US ",
        "SV ",
        "VfL ",
        "VfB ",
        "AFC ",
    )
    for prefix in prefixes:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break

    suffixes = (" FC", " CF", " AFC", " AC", " AS", " SC")
    for suffix in suffixes:
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
            break

    return cleaned.strip()


def _role_for_team(guild: discord.Guild, team_name: str) -> discord.Role | None:
    candidates = []
    mapped = TEAM_NAME_MAP.get(team_name)
    if mapped:
        candidates.append(mapped)
    candidates.append(team_name)
    normalized = _normalize_team_name(team_name)
    if normalized != team_name:
        candidates.append(normalized)

    for candidate in candidates:
        role = discord.utils.get(guild.roles, name=candidate)
        if role:
            return role
    return None


def _resolve_competition(league: str | None) -> tuple[str, str] | None:
    if not league:
        return PREMIER_LEAGUE_CODE, COMPETITIONS[PREMIER_LEAGUE_CODE]

    raw = league.strip()
    code = raw.upper()
    if code in COMPETITIONS:
        return code, COMPETITIONS[code]

    key = raw.lower().replace(" ", "")
    alias_code = COMPETITION_ALIASES.get(key)
    if alias_code:
        return alias_code, COMPETITIONS[alias_code]

    return None


def _matches_role_name(role_name: str, team: dict) -> bool:
    normalized_role = _normalize_team_name(role_name).lower()
    candidates = [
        team.get("name", ""),
        team.get("shortName", ""),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        if TEAM_NAME_MAP.get(candidate) == role_name:
            return True
        if candidate.lower() == role_name.lower():
            return True
        if _normalize_team_name(candidate).lower() == normalized_role:
            return True
    return False


def _format_fixture_line(match: dict, guild: discord.Guild) -> str:
    home_name = match["homeTeam"]["name"]
    away_name = match["awayTeam"]["name"]
    home_role = _role_for_team(guild, home_name)
    away_role = _role_for_team(guild, away_name)
    home_display = home_role.mention if home_role else home_name
    away_display = away_role.mention if away_role else away_name
    kickoff = _format_kickoff(match.get("utcDate"))
    line = f"{home_display} vs {away_display}"
    if kickoff:
        line = f"{line} — Kickoff {kickoff}"
    return line


async def _fetch_football_data(url: str, token: str) -> dict:
    headers = {"X-Auth-Token": token}
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
        async with session.get(url) as response:
            if response.status != 200:
                details = await response.text()
                raise RuntimeError(f"API error {response.status}: {details}")
            return await response.json()


def _format_kickoff(utc_date: str | None) -> str | None:
    if not utc_date:
        return None
    try:
        kickoff = datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
    except ValueError:
        return None
    return discord.utils.format_dt(kickoff, "R")


def _parse_utc_date(utc_date: str | None) -> datetime | None:
    if not utc_date:
        return None
    try:
        return datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
    except ValueError:
        return None


def _format_result_line(match: dict, guild: discord.Guild) -> tuple[str, str]:
    home_name = match["homeTeam"]["name"]
    away_name = match["awayTeam"]["name"]
    home_role = _role_for_team(guild, home_name)
    away_role = _role_for_team(guild, away_name)
    home_display = home_role.mention if home_role else home_name
    away_display = away_role.mention if away_role else away_name

    status = match.get("status", "SCHEDULED")
    score = match.get("score", {})
    full_time = score.get("fullTime") or {}
    home_score = full_time.get("home")
    away_score = full_time.get("away")

    if home_score is not None and away_score is not None:
        scoreline = f"{home_score}-{away_score}"
    else:
        scoreline = "vs"

    if status == "FINISHED":
        winner = score.get("winner")
        if winner == "HOME_TEAM":
            result_text = "Home win"
        elif winner == "AWAY_TEAM":
            result_text = "Away win"
        else:
            result_text = "Draw"
    elif status in {"IN_PLAY", "PAUSED"}:
        result_text = "Live"
    else:
        kickoff = _format_kickoff(match.get("utcDate"))
        result_text = f"Kickoff {kickoff}" if kickoff else status.replace("_", " ").title()

    line = f"{home_display} {scoreline} {away_display} — {result_text}"
    match_name = f"{home_name} vs {away_name}"
    return match_name, line
