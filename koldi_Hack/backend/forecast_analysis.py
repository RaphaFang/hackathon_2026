import pandas as pd
import ollama


# =====================================
# CONFIG
# =====================================

MOVEMENT_FILE = (
    "data/movement_stats_hourly.csv"
)

OUTLIER_THRESHOLD = 200

DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]


# =====================================
# LOAD + BUILD FORECAST MODEL
# =====================================

def build_forecast_model():

    mv = pd.read_csv(
        MOVEMENT_FILE
    )

    mv["ts"] = pd.to_datetime(
        mv["timestamp"],
        utc=True
    ).dt.tz_convert(
        "Europe/Copenhagen"
    )

    mv["date"] = (
        mv["ts"]
        .dt
        .normalize()
    )

    mv["datestr"] = (
        mv["ts"]
        .dt
        .strftime(
            "%Y-%m-%d"
        )
    )

    mv["hour"] = (
        mv["ts"]
        .dt
        .hour
    )

    mv["dow"] = (
        mv["ts"]
        .dt
        .dayofweek
    )

    ped = mv[

        (mv["category"] == "pedestrian")

        &

        (mv["direction"] == "IN")

    ].copy()

    # --------------------------
    # DAILY TOTALS
    # --------------------------

    daily = (
        ped
        .groupby(
            "datestr"
        )["amount"]
        .sum()
        .sort_index()
    )

    daily_actuals = {

        d: int(v)

        for d, v

        in daily.items()

    }

    # --------------------------
    # REMOVE CAMERA-DOWN DAYS
    # --------------------------

    good_dates = daily[
        daily >= OUTLIER_THRESHOLD
    ].index

    pedg = ped[
        ped["datestr"]
        .isin(
            good_dates
        )
    ]

    # --------------------------
    # WEEKDAY LEVEL
    # --------------------------

    dt = pedg.groupby(
        "datestr"
    ).agg(

        total=(
            "amount",
            "sum"
        ),

        dow=(
            "dow",
            "first"
        )
    )

    level = (

        dt
        .groupby(
            "dow"
        )["total"]
        .agg(
            ["mean", "std"]
        )
        .reindex(
            range(7)
        )

    )

    level_mean = [

        round(
            float(
                level.loc[i, "mean"]
            ),
            1
        )

        for i

        in range(7)

    ]

    level_std = [

        round(
            float(
                level.loc[i, "std"]
            ),
            1
        )

        for i

        in range(7)

    ]

    # --------------------------
    # HOURLY PROFILE
    # --------------------------

    hourly = (
        pedg
        .groupby(
            ["dow", "hour"]
        )["amount"]
        .sum()
        .reset_index()
    )

    totals = (
        hourly
        .groupby(
            "dow"
        )["amount"]
        .transform(
            "sum"
        )
    )

    hourly["frac"] = (
        hourly["amount"]
        / totals
    )

    frac_pivot = (

        hourly
        .pivot(
            index="dow",
            columns="hour",
            values="frac"
        )

        .reindex(
            index=range(7),
            columns=range(24)
        )

        .fillna(0)

    )

    frac = [

        [

            round(
                float(
                    frac_pivot.loc[d, h]
                ),
                5
            )

            for h

            in range(24)

        ]

        for d

        in range(7)

    ]

    # --------------------------
    # HOURLY ACTUALS
    # --------------------------

    hourly_actuals = {}

    for d, sub in pedg.groupby(
        "datestr"
    ):

        by_h = (

            sub
            .groupby(
                "hour"
            )["amount"]

            .sum()

            .reindex(
                range(24)
            )

            .fillna(0)

            .astype(int)

        )

        hourly_actuals[d] = {

            "h":
            by_h.tolist(),

            "t":
            int(
                by_h.sum()
            )
        }

    return {

        "model": {

            "level_mean":
            level_mean,

            "level_std":
            level_std,

            "frac":
            frac

        },

        "actuals":
        hourly_actuals,

        "daily_actuals":
        daily_actuals
    }


# =====================================
# GRAPH DATA
# =====================================

def get_forecast_data():

    return build_forecast_model()


# =====================================
# AI INSIGHT
# =====================================

SYSTEM_PROMPT = """
You are Kolding Pulse AI.

You analyse forecasted
urban movement in Kolding.

Rules:

- Use only provided data
- Never invent numbers
- Explain meaning
- Be concise
- Maximum 3 sentences
"""


def get_forecast_insight():

    data = build_forecast_model()

    means = data[
        "model"
    ][
        "level_mean"
    ]

    hi_idx = means.index(
        max(means)
    )

    lo_idx = means.index(
        min(means)
    )

    hi_day = DAY_NAMES[
        hi_idx
    ]

    lo_day = DAY_NAMES[
        lo_idx
    ]

    hi_val = round(
        max(means)
    )

    lo_val = round(
        min(means)
    )

    prompt = f"""
Highest forecast:
{hi_day}
with
{hi_val}
arrivals.

Lowest forecast:
{lo_day}
with
{lo_val}
arrivals.

Explain what this
suggests about
movement patterns
in Kolding.
"""

    try:

        response = ollama.chat(

            model="phi3",

            messages=[

                {
                    "role":
                    "system",

                    "content":
                    SYSTEM_PROMPT
                },

                {
                    "role":
                    "user",

                    "content":
                    prompt
                }

            ]
        )

        return response[
            "message"
        ][
            "content"
        ]

    except Exception:

        return (
            "AI forecast insight "
            "temporarily unavailable."
        )