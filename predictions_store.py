import json
import os
from datetime import datetime

from config import LEGACY_PREDICTIONS_FILE, PREDICTIONS_FILE


def load_predictions() -> dict:
    file_path = None
    if os.path.exists(PREDICTIONS_FILE):
        file_path = PREDICTIONS_FILE
    elif os.path.exists(LEGACY_PREDICTIONS_FILE):
        file_path = LEGACY_PREDICTIONS_FILE
    else:
        return {"version": 1, "predictions": {}}

    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "predictions": {}}

    if not isinstance(data, dict):
        return {"version": 1, "predictions": {}}
    if "predictions" not in data or not isinstance(data["predictions"], dict):
        data["predictions"] = {}
    data.setdefault("version", 1)
    return data


def save_predictions(data: dict) -> None:
    with open(PREDICTIONS_FILE, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)


def record_prediction(data: dict, match_id: int, user_id: int, outcome: str) -> None:
    match_key = str(match_id)
    match_bucket = data["predictions"].setdefault(match_key, {"predictions": {}})
    match_bucket["predictions"][str(user_id)] = {
        "outcome": outcome,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def outcome_from_score(home: int, away: int) -> str:
    if home > away:
        return "HOME"
    if away > home:
        return "AWAY"
    return "DRAW"


def score_prediction(predicted_outcome: str, actual_home: int, actual_away: int) -> int:
    actual = outcome_from_score(actual_home, actual_away)
    return 2 if predicted_outcome == actual else 0
