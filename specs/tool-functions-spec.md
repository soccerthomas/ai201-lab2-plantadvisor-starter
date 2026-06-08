# Spec: Tool Functions

**File:** `tools.py`
**Status:** `get_seasonal_conditions` — Pre-implemented, read through. `lookup_plant` — complete spec fields before implementing.

---

## Purpose

These two functions are the tools the agent can call. They retrieve structured data from the local plant database and seasonal data files and return it to the agent loop, which passes it to the LLM as context for generating a response.

---

## Function 1: `lookup_plant()`

### Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `plant_name` | `str` | The plant name as entered by the user or chosen by the LLM — may be any casing, common name, scientific name, or alias |

**Output:** `dict`

When the plant is **found**, return:
```python
{"found": True, "plant": }
```

When the plant is **not found**, return:
```python
{"found": False, "name": , "message": }
```

---

### Design Decisions

---

#### Input normalization

Strip leading/trailing whitespace and convert to lowercase before any comparison.

```python
normalized = plant_name.strip().lower()
```

---

#### Search order

Search in this order: direct key → display name → aliases. Keys are the fastest
lookup (O(1) dict access), so check those first. Display names are the next most
likely match for clean user input. Aliases are the broadest net, so they go last.

Direct key match: normalized in _plant_db
Display name match: plant["display_name"].lower() == normalized
Alias match: normalized in [alias.lower() for alias in plant["aliases"]]


---

#### Alias matching approach
Loop through every plant in the database. For each plant, lowercase every
alias in its aliases list and check if the normalized input matches any of
them. Return the plant as soon as a match is found.

---

#### Not-found message
"No plant matching '{normalized}' was found in the database. Let the user
know and offer general advice if possible."

---

#### Implementation Notes

**Test: does `"devil's ivy"` return the pothos entry?**
Yes

**Test: does `"SNAKE PLANT"` return the snake plant entry?**
Yes — input normalization to lowercase handles the casing.

**One edge case you discovered while implementing:**
Aliases with inconsistent spacing or punctuation (e.g. "devil's ivy" vs
"devils ivy") won't match unless the alias in plants.json is an exact
lowercase match. The normalization only handles casing, not punctuation.

---

## Function 2: `get_seasonal_conditions()`

### Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `season` | `str \| None` | One of `"spring"`, `"summer"`, `"fall"`, `"winter"`, or `None` to auto-detect |

**Output:** `dict`

The full season dict from `_season_data`, plus one additional field:

| Added field | Type | Value |
|-------------|------|-------|
| `"detected_season"` | `bool` | `True` if auto-detected from the month; `False` if season was passed as an argument |

---

### Design Decisions

---

#### Auto-detection logic

When `season` is `None`, get the current calendar month with `datetime.now().month`
and look it up in the `_MONTH_TO_SEASON` dict, which maps month numbers to season strings.

```python
current_month = datetime.now().month
season_key = _MONTH_TO_SEASON[current_month]
```

---

#### Season validation

If the caller passes an invalid season string (e.g., `"monsoon"`), the function
falls back to auto-detection — same as if `None` were passed. The `VALID_SEASONS`
set acts as the gate:

```python
VALID_SEASONS = {"spring", "summer", "fall", "winter"}
if season and season.lower() in VALID_SEASONS:
    ...  # use provided season
else:
    ...  # auto-detect
```

---

#### Return structure

The full season dict from `_season_data`, plus a `detected_season` boolean. Example for spring:

```python
{
    "season": "spring",
    "watering": "Increase watering frequency as plants break dormancy ...",
    "fertilizing": "Resume feeding with a balanced fertilizer ...",
    "light": "Days are lengthening — move plants closer to windows ...",
    "pests": "Watch for spider mites and aphids as temperatures rise ...",
    "detected_season": True   # True = auto-detected; False = caller specified
}
```

---

#### Implementation Notes

**Test: does calling with `season=None` return the correct season for the current month?**
Current month: June
Expected season: summer
Returned season: summer

**Test: does calling with `season="winter"` return winter data regardless of the current month?**
Yes

