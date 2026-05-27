import pandas as pd
from config import DATA_DIR

# ── Load raw data ──────────────────────────────────────────────────────────────
movement = pd.read_excel(DATA_DIR / "Movement.xlsx")
stay     = pd.read_excel(DATA_DIR / "StayDuration.xlsx")
events   = pd.read_csv(DATA_DIR / "clean_kolding_events.csv")

movement["timestamp"] = pd.to_datetime(movement["timestamp"], utc=True, errors="coerce")
stay["timestamp"]     = pd.to_datetime(stay["timestamp"],     utc=True, errors="coerce")

movement = movement.dropna(subset=["timestamp"])
stay     = stay.dropna(subset=["timestamp"])

stay["avg_stay_min"] = (stay["sum_ms"] / stay["objects"]) / 1000 / 60


# ── API functions ──────────────────────────────────────────────────────────────

def get_overview() -> dict:
    return {
        "movement": float(movement["amount"].sum()),
        "events":   int(len(events)),
        "avg_stay": float(stay["avg_stay_min"].mean()),
    }


def get_movement() -> list:
    df = movement.groupby("timestamp")["amount"].sum().reset_index()
    df["timestamp"] = df["timestamp"].astype(str)
    return df.to_dict(orient="records")


def get_stay() -> list:
    df = (
        stay.groupby("sensor")["avg_stay_min"]
        .mean()
        .reset_index()
        .sort_values("avg_stay_min", ascending=False)
        .head(10)
    )
    return df.to_dict(orient="records")


def get_events() -> list:
    events["Year"] = events["Date"].astype(str).str.extract(r"(20\d{2})")
    df = events["Year"].value_counts().sort_index().reset_index()
    df.columns = ["year", "events"]
    return df.to_dict(orient="records")


def get_vitality() -> list:
    move_daily = movement.groupby(movement["timestamp"].dt.date)["amount"].sum().reset_index()
    stay_daily = stay.groupby(stay["timestamp"].dt.date)["avg_stay_min"].mean().reset_index()
    merged     = move_daily.merge(stay_daily, on="timestamp", how="inner")
    return merged.to_dict(orient="records")


# ── Full context for AI agent ──────────────────────────────────────────────────

def get_full_ai_context() -> str:
    sections = []

    ov = get_overview()
    sections.append(
        f"=== OVERVIEW ===\n"
        f"Total movements : {int(ov['movement']):,}\n"
        f"Total events    : {ov['events']}\n"
        f"Avg stay        : {ov['avg_stay']:.1f} min"
    )

    move_daily = (
        movement.copy()
        .assign(date=lambda df: df["timestamp"].dt.date)
        .groupby("date")["amount"].sum()
        .reset_index()
        .sort_values("date")
    )
    peak       = move_daily.loc[move_daily["amount"].idxmax()]
    move_lines = "\n".join(
        f"  {r['date']}: {int(r['amount']):,}" for _, r in move_daily.iterrows()
    )
    sections.append(
        f"=== DAILY MOVEMENT (all days) ===\n"
        f"Peak day: {peak['date']} — {int(peak['amount']):,} movements\n"
        f"{move_lines}"
    )

    movement["hour"] = movement["timestamp"].dt.hour
    hourly     = movement.groupby("hour")["amount"].sum().reset_index()
    hour_lines = "\n".join(
        f"  {int(r['hour']):02d}:00 — {int(r['amount']):,}" for _, r in hourly.iterrows()
    )
    sections.append(f"=== MOVEMENT BY HOUR ===\n{hour_lines}")

    movement["weekday"] = movement["timestamp"].dt.day_name()
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekly        = (
        movement.groupby("weekday")["amount"].sum()
        .reindex(weekday_order)
        .reset_index()
    )
    week_lines = "\n".join(
        f"  {r['weekday']}: {int(r['amount']):,}" for _, r in weekly.iterrows()
    )
    sections.append(f"=== MOVEMENT BY DAY OF WEEK ===\n{week_lines}")

    all_stay   = (
        stay.groupby("sensor")["avg_stay_min"]
        .mean()
        .reset_index()
        .sort_values("avg_stay_min", ascending=False)
    )
    stay_lines = "\n".join(
        f"  {r['sensor']}: {r['avg_stay_min']:.1f} min" for _, r in all_stay.iterrows()
    )
    sections.append(f"=== STAY DURATION PER SENSOR (all sensors) ===\n{stay_lines}")

    sections.append(f"=== EVENTS DATASET COLUMNS ===\n  {list(events.columns)}")
    sections.append(f"=== EVENTS (first 50 rows) ===\n{events.head(50).to_string(index=False)}")

    ev_year    = get_events()
    year_lines = "\n".join(f"  {r['year']}: {r['events']} events" for r in ev_year)
    sections.append(f"=== EVENTS BY YEAR ===\n{year_lines}")

    vitality   = get_vitality()
    vit_lines  = "\n".join(
        f"  {r['timestamp']}: {int(r['amount']):,} moves, {r['avg_stay_min']:.1f} min stay"
        for r in vitality
    )
    sections.append(f"=== DAILY VITALITY (movement + stay combined) ===\n{vit_lines}")

    return "\n\n".join(sections)
