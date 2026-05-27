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

    # ── Parking data ──────────────────────────────────────────────────────────
    try:
        import pandas as pd
        from config import DATA_DIR

        df_cum   = pd.read_csv(DATA_DIR / "cache_parking_hourly_sim.csv")
        baseline = pd.read_csv(DATA_DIR / "cache_parking_baseline.csv")
        parking  = pd.read_csv(DATA_DIR / "parking_snapshot.csv")

        core_cap  = int(parking[parking["distance_km"] <= 0.5]["spaceCount"].sum())
        total_cap = int(parking[parking["distance_km"] <= 0.7]["spaceCount"].sum())

        avg_occ  = df_cum["occupancy_rate"].mean()
        peak_occ = df_cum["occupancy_rate"].max()
        peak_row = df_cum.loc[df_cum["occupancy_rate"].idxmax()]

        sections.append(
            f"=== PARKING OVERVIEW ===\n"
            f"  Core capacity (<0.5 km)   : {core_cap} spaces\n"
            f"  Total capacity (<0.7 km)  : {total_cap} spaces\n"
            f"  Average occupancy rate    : {avg_occ:.1%}\n"
            f"  Peak occupancy rate       : {peak_occ:.1%}\n"
            f"  Peak occurred on          : {peak_row['date']} at {int(peak_row['hour']):02d}:00\n"
            f"  Day type at peak          : {peak_row['group']}"
        )

        hourly_occ = (
            df_cum.groupby("hour")["occupancy_rate"]
            .mean()
            .reset_index()
        )
        pk_lines = "\n".join(
            f"  {int(r['hour']):02d}:00 — {r['occupancy_rate']:.1%}"
            for _, r in hourly_occ.iterrows()
        )
        sections.append(f"=== PARKING HOURLY AVERAGE OCCUPANCY ===\n{pk_lines}")

        cong = pd.read_csv(DATA_DIR / "precomputed_hourly_congestion.csv")
        cong_hourly = cong.groupby("hour")["congestion_score"].mean().reset_index()
        cong_lines = "\n".join(
            f"  {int(r['hour']):02d}:00 — {r['congestion_score']:.0f} vehicles"
            for _, r in cong_hourly.iterrows()
        )
        sections.append(f"=== STREET CONGESTION BY HOUR (average vehicles) ===\n{cong_lines}")

    except Exception as e:
        sections.append(f"=== PARKING DATA ===\n  Unavailable: {e}")

    # ── Forecast data ──────────────────────────────────────────────────────────
    try:
        import pandas as pd
        from config import DATA_DIR

        DAY_NAMES = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        mv = pd.read_csv(DATA_DIR / "movement_stats_hourly.csv")
        mv["ts"]      = pd.to_datetime(mv["timestamp"], utc=True).dt.tz_convert("Europe/Copenhagen")
        mv["datestr"] = mv["ts"].dt.strftime("%Y-%m-%d")
        mv["hour"]    = mv["ts"].dt.hour
        mv["dow"]     = mv["ts"].dt.dayofweek

        ped       = mv[(mv["category"] == "pedestrian") & (mv["direction"] == "IN")]
        daily     = ped.groupby("datestr")["amount"].sum()
        good      = daily[daily >= 200].index
        pedg      = ped[ped["datestr"].isin(good)]

        dt        = pedg.groupby("datestr").agg(total=("amount","sum"), dow=("dow","first"))
        level     = dt.groupby("dow")["total"].agg(["mean","std"]).reindex(range(7))

        fc_lines = "\n".join(
            f"  {DAY_NAMES[i]}: avg {round(float(level.loc[i,'mean'])):,} arrivals "
            f"(±{round(float(level.loc[i,'std'])):,})"
            for i in range(7)
            if not pd.isna(level.loc[i,"mean"])
        )
        hi_idx = int(level["mean"].idxmax())
        lo_idx = int(level["mean"].idxmin())
        sections.append(
            f"=== PEDESTRIAN FORECAST BY WEEKDAY ===\n"
            f"  Busiest day : {DAY_NAMES[hi_idx]} ({round(float(level.loc[hi_idx,'mean'])):,} avg arrivals)\n"
            f"  Quietest day: {DAY_NAMES[lo_idx]} ({round(float(level.loc[lo_idx,'mean'])):,} avg arrivals)\n"
            f"{fc_lines}"
        )
    except Exception as e:
        sections.append(f"=== FORECAST DATA ===\n  Unavailable: {e}")

    # ── City / locations data ─────────────────────────────────────────────────
    try:
        import pandas as pd
        from config import DATA_DIR

        loc = pd.read_csv(DATA_DIR / "akseltorv_locations_cleaned_data.csv")
        type_counts = loc["type"].value_counts()
        type_lines  = "\n".join(f"  {t}: {n}" for t, n in type_counts.items())
        sections.append(
            f"=== CITY LOCATIONS (Akseltorv area) ===\n"
            f"  Total places: {len(loc)}\n"
            f"{type_lines}"
        )
    except Exception as e:
        sections.append(f"=== CITY LOCATIONS DATA ===\n  Unavailable: {e}")

    return "\n\n".join(sections)