import json
import os
from datetime import datetime
from config import DATA_PATH

# Plant database and seasonal data are loaded once at module load.
with open(os.path.join(DATA_PATH, "plants.json"), encoding="utf-8") as f:
    _plant_db = json.load(f)

with open(os.path.join(DATA_PATH, "seasons.json"), encoding="utf-8") as f:
    _season_data = json.load(f)

_MONTH_TO_SEASON = {
    12: "winter", 1: "winter", 2: "winter",
    3: "spring", 4: "spring", 5: "spring",
    6: "summer", 7: "summer", 8: "summer",
    9: "fall",  10: "fall",  11: "fall",
}


def lookup_plant(plant_name: str) -> dict:
    normalized = plant_name.strip().lower()

    # 1. Direct key match
    if normalized in _plant_db:
        return {"found": True, "plant": _plant_db[normalized]}

    # 2. Display name match
    for key, plant in _plant_db.items():
        if plant["display_name"].lower() == normalized:
            return {"found": True, "plant": plant}

    # 3. Alias match
    for key, plant in _plant_db.items():
        if normalized in [alias.lower() for alias in plant["aliases"]]:
            return {"found": True, "plant": plant}

    return {
        "found": False,
        "name": normalized,
        "message": f"No plant matching '{normalized}' was found in the database. Let the user know and offer general advice if possible.",
    }


def get_seasonal_conditions(season: str | None = None) -> dict:
    """
    Return current seasonal care context for houseplants.

    If season is provided and valid, returns that season's data.
    If season is None (or invalid), auto-detects from the current calendar month.

    Pre-implemented — read through this and the spec before working on lookup_plant().
    """
    VALID_SEASONS = {"spring", "summer", "fall", "winter"}

    if season and season.lower() in VALID_SEASONS:
        season_key = season.lower()
        detected = False
    else:
        current_month = datetime.now().month
        season_key = _MONTH_TO_SEASON[current_month]
        detected = True

    result = dict(_season_data[season_key])
    result["detected_season"] = detected
    return result