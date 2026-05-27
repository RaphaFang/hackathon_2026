import pandas as pd
from config import DATA_DIR

OUTLIER_THRESHOLD = 200
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def build_forecast_model() -> dict:
    mv = pd.read_csv(DATA_DIR / "movement_stats_hourly.csv")

    mv["ts"]      = pd.to_datetime(mv["timestamp"], utc=True).dt.tz_convert("Europe/Copenhagen")
    mv["date"]    = mv["ts"].dt.normalize()
    mv["datestr"] = mv["ts"].dt.strftime("%Y-%m-%d")
    mv["hour"]    = mv["ts"].dt.hour
    mv["dow"]     = mv["ts"].dt.dayofweek

    ped = mv[(mv["category"] == "pedestrian") & (mv["direction"] == "IN")].copy()

    # Daily totals
    daily         = ped.groupby("datestr")["amount"].sum().sort_index()
    daily_actuals = {d: int(v) for d, v in daily.items()}

    # Remove camera-down days
    good_dates = daily[daily >= OUTLIER_THRESHOLD].index
    pedg       = ped[ped["datestr"].isin(good_dates)]

    # Weekday level stats
    dt    = pedg.groupby("datestr").agg(total=("amount", "sum"), dow=("dow", "first"))
    level = dt.groupby("dow")["total"].agg(["mean", "std"]).reindex(range(7))

    level_mean = [round(float(level.loc[i, "mean"]), 1) for i in range(7)]
    level_std  = [round(float(level.loc[i, "std"]),  1) for i in range(7)]

    # Hourly fraction profile
    hourly = ped.groupby(["dow", "hour"])["amount"].sum().reset_index()
    totals = hourly.groupby("dow")["amount"].transform("sum")
    hourly["frac"] = hourly["amount"] / totals

    frac_pivot = (
        hourly.pivot(index="dow", columns="hour", values="frac")
        .reindex(index=range(7), columns=range(24))
        .fillna(0)
    )
    frac = [[round(float(frac_pivot.loc[d, h]), 5) for h in range(24)] for d in range(7)]

    # Hourly actuals per date
    hourly_actuals = {}
    for d, sub in pedg.groupby("datestr"):
        by_h = sub.groupby("hour")["amount"].sum().reindex(range(24)).fillna(0).astype(int)
        hourly_actuals[d] = {"h": by_h.tolist(), "t": int(by_h.sum())}

    return {
        "model":         {"level_mean": level_mean, "level_std": level_std, "frac": frac},
        "actuals":       hourly_actuals,
        "daily_actuals": daily_actuals,
    }


def get_forecast_data() -> dict:
    return build_forecast_model()


def build_forecast_insight_prompt() -> str:
    data    = build_forecast_model()
    means   = data["model"]["level_mean"]
    hi_idx  = means.index(max(means))
    lo_idx  = means.index(min(means))
    return (
        f"Highest forecast: {DAY_NAMES[hi_idx]} with {round(max(means))} arrivals.\n"
        f"Lowest forecast: {DAY_NAMES[lo_idx]} with {round(min(means))} arrivals.\n"
        f"Explain what this suggests about movement patterns in Kolding."
    )
