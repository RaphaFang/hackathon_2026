import pandas as pd
from config import DATA_DIR

# ── Load data ──────────────────────────────────────────────────────────────────
movement  = pd.read_csv(DATA_DIR / "movement_stats_hourly.csv")
locations = pd.read_csv(DATA_DIR / "akseltorv_locations_cleaned_data.csv")
holidays  = pd.read_csv(DATA_DIR / "Holidays_data_updated")

# ── Prepare movement ───────────────────────────────────────────────────────────
movement["timestamp"]     = pd.to_datetime(movement["timestamp"], utc=True).dt.tz_convert("Europe/Copenhagen")
movement["date"]          = movement["timestamp"].dt.date
movement["hour"]          = movement["timestamp"].dt.hour
movement["weekday_num"]   = movement["timestamp"].dt.weekday
movement["weekday_short"] = movement["timestamp"].dt.day_name().str.lower().str[:3]

# ── Holidays ───────────────────────────────────────────────────────────────────
holidays["date"]           = pd.to_datetime(holidays["date"]).dt.date
holiday_dates              = set(holidays["date"])
movement["is_public_holiday"] = movement["date"].isin(holiday_dates)

# ── Day groups ─────────────────────────────────────────────────────────────────
movement["day_group"]                                           = "Weekday"
movement.loc[movement["weekday_num"] >= 5, "day_group"]         = "Weekend"
movement.loc[movement["is_public_holiday"], "day_group"]        = "Public holiday"

# ── Place type labels ──────────────────────────────────────────────────────────
TYPE_LABELS = {
    "food":           "Restaurants / cafés",
    "retail":         "Retail",
    "service":        "Services",
    "public service": "Public services",
    "school":         "Schools",
    "parking":        "Parking",
    "nightclub":      "Nightlife",
}
locations["place_type"] = locations["type"].map(TYPE_LABELS).fillna(locations["type"])

# ── Opening-hours helpers ──────────────────────────────────────────────────────

def _time_to_hour(value) -> int | None:
    if pd.isna(value):
        return None
    value = str(value).strip().lower()
    if value in ("closed", ""):
        return None
    try:
        return int(value.split(":")[0])
    except ValueError:
        return None


def _is_open_at_hour(row, day: str, hour: int, is_public_holiday: bool = False) -> bool:
    if is_public_holiday:
        public_open = row.get("public_holiday_open")
        if pd.isna(public_open) or str(public_open).strip().lower() in ("closed", ""):
            return False
        public_close = row.get("public_holiday_close")
        if public_close is not None and not pd.isna(public_close):
            open_h  = _time_to_hour(public_open)
            close_h = _time_to_hour(public_close)
        else:
            open_h  = _time_to_hour(row.get("open_sun"))
            close_h = _time_to_hour(row.get("close_sun"))
    else:
        open_h  = _time_to_hour(row.get(f"open_{day}"))
        close_h = _time_to_hour(row.get(f"close_{day}"))

    if open_h is None or close_h is None:
        return False
    if open_h < close_h:
        return open_h <= hour < close_h
    if open_h > close_h:
        return hour >= open_h or hour < close_h
    return False


# ── Compute combined dataset ───────────────────────────────────────────────────

def _build_combined() -> pd.DataFrame:
    pedestrian_hourly = (
        movement[movement["category"] == "pedestrian"]
        .groupby(["day_group", "weekday_short", "hour"], as_index=False)["amount"]
        .mean()
        .rename(columns={"amount": "avg_pedestrian_movement"})
    )

    day_groups  = {"Weekday": ["mon","tue","wed","thu","fri"], "Weekend": ["sat","sun"], "Public holiday": ["sun"]}
    place_types = sorted(locations["place_type"].dropna().unique())

    rows = []
    for day_group, days in day_groups.items():
        for day in days:
            for hour in range(24):
                open_mask   = locations.apply(
                    lambda row: _is_open_at_hour(row, day, hour, day_group == "Public holiday"),
                    axis=1,
                )
                open_places = locations[open_mask]
                for place_type in place_types:
                    rows.append({
                        "day_group":     day_group,
                        "weekday_short": day,
                        "hour":          hour,
                        "place_type":    place_type,
                        "open_count":    len(open_places[open_places["place_type"] == place_type]),
                    })

    open_by_type = pd.DataFrame(rows)
    combined     = open_by_type.merge(pedestrian_hourly, on=["day_group", "weekday_short", "hour"], how="left")
    combined["avg_pedestrian_movement"] = combined["avg_pedestrian_movement"].fillna(0)
    combined["movement_while_open"]     = combined["open_count"] * combined["avg_pedestrian_movement"]
    return (
        combined
        .groupby(["day_group", "place_type", "hour"], as_index=False)
        .agg(
            open_count=("open_count", "mean"),
            avg_pedestrian_movement=("avg_pedestrian_movement", "mean"),
            movement_while_open=("movement_while_open", "mean"),
        )
    )


def build_city_insight_prompts() -> dict[str, str]:
    """Returns a dict of {group: prompt_text} for each day group."""
    combined = _build_combined()
    prompts  = {}

    for group in ("Weekday", "Weekend", "Public holiday"):
        subset = combined[combined["day_group"] == group].copy()
        matrix = (
            subset.pivot(index="place_type", columns="hour", values="movement_while_open")
            .fillna(0)
        )
        peak_place = matrix.sum(axis=1).idxmax()
        peak_hour  = int(matrix.sum(axis=0).idxmax())
        peak_value = int(matrix.values.max())

        prompts[group] = (
            f"Heatmap output | Day group: {group}\n"
            f"Peak place: {peak_place}\n"
            f"Peak hour: {peak_hour}:00\n"
            f"Peak value: {peak_value}"
        )

    return prompts
