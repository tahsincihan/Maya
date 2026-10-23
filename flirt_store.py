"""Saved state for the flirty features: couples, channels, logs and opt-outs (flirt.json)."""

import json

from config import FLIRT_FILE

_state: dict | None = None


def state() -> dict:
    global _state
    if _state is None:
        try:
            with open(FLIRT_FILE, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            data = {}
        if not isinstance(data, dict):
            data = {}
        data.setdefault("guilds", {})
        data.setdefault("admirer_optout", [])
        _state = data
    return _state


def guild_state(guild_id: int) -> dict:
    return state()["guilds"].setdefault(str(guild_id), {})


def append_log(guild_id: int, key: str, entry: dict, keep: int = 500) -> None:
    log = guild_state(guild_id).setdefault(key, [])
    log.append(entry)
    del log[:-keep]


def save() -> None:
    with open(FLIRT_FILE, "w", encoding="utf-8") as handle:
        json.dump(state(), handle, indent=2, sort_keys=True)
