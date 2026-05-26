import json
from pathlib import Path

from agent import parking_ai_insight
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.utils
from plotly.subplots import make_subplots
from fastapi import Query


# ======================================================
# DYNAMIC DATA PATH
# ======================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# ======================================================
# LOAD DATA
# ======================================================

try:

    df_cum = pd.read_csv(
        DATA_DIR / "cache_parking_hourly_sim.csv"
    )

    baseline = pd.read_csv(
        DATA_DIR / "cache_parking_baseline.csv"
    )

    parking = pd.read_csv(
        DATA_DIR / "parking_snapshot.csv"
    )

    core_capacity = int(
        parking[
            parking["distance_km"] <= 0.5
        ]["spaceCount"].sum()
    )

    total_capacity = int(
        parking[
            parking["distance_km"] <= 0.7
        ]["spaceCount"].sum()
    )

except FileNotFoundError as e:
    print("Missing parking dataset:", e)

# ======================================================
# STRESS THRESHOLDS
# ======================================================

p50 = df_cum[
    "occupancy_rate"
].quantile(.50)

p75 = df_cum[
    "occupancy_rate"
].quantile(.75)

p90 = df_cum[
    "occupancy_rate"
].quantile(.90)


def stress_label(val):

    if pd.isna(val):
        return -1

    if val >= p90:
        return 3

    elif val >= p75:
        return 2

    elif val >= p50:
        return 1

    return 0


# ======================================================
# SPECIAL EVENT DAYS
# ======================================================

SPECIAL_DATES = {

    "2026-02-07","2026-02-08","2026-02-09",
    "2026-02-10","2026-02-11","2026-02-12",
    "2026-02-13","2026-02-14","2026-02-15",
    "2026-02-26","2026-03-08","2026-03-24",
    "2026-03-28","2026-03-29","2026-03-30",
    "2026-03-31","2026-04-01","2026-04-02",
    "2026-04-03","2026-04-04","2026-04-05",
    "2026-04-06","2026-04-12","2026-04-25",
    "2026-05-01","2026-05-06"
}

event_dates_set = set(
    pd.to_datetime(
        list(SPECIAL_DATES)
    ).date
)

# ======================================================
# MAIN ANALYSIS
# ======================================================

def get_parking_analytics(
    date="2026-02-14"
):

    target_date = pd.to_datetime(
        date
    ).date()

    is_future = (
        target_date
        >
        pd.to_datetime(
            df_cum["date"].max()
        ).date()
    )

    weekday = pd.to_datetime(
        target_date
    ).dayofweek

    day_type = (
        "weekend"
        if weekday >= 5
        else "weekday"
    )

    is_special = (
        1
        if target_date in event_dates_set
        else 0
    )

    target_group = (
        f"{day_type}_"
        f"{'special' if is_special else 'regular'}"
    )

    # BASELINE

    bl = (

        baseline[
            baseline["group"]
            ==
            target_group
        ]

        .sort_values("hour")
        .set_index("hour")
        .reindex(range(24))
    )

    n_days = (
        bl["n"].iloc[0]
        if not bl.empty
        else 0
    )

    stay_series = df_cum[
        df_cum["group"]
        ==
        target_group
    ]["stay_hours"]

    stay_hours = (
        stay_series.iloc[0]
        if not stay_series.empty
        else 0
    )

    # ACTUAL

    if is_future:

        actual_occ = pd.Series(
            [np.nan]*24
        )

        actual_cong = pd.Series(
            [np.nan]*24
        )

    else:

        day_match = (

            df_cum[
                df_cum["date"]
                ==
                str(target_date)
            ]

            .sort_values("hour")
            .set_index("hour")
        )

        actual_occ = (
            day_match[
                "occupancy_rate"
            ].reindex(range(24))
        )

        actual_cong = (
            day_match[
                "congestion_score"
            ].reindex(range(24))
        )

    # ==================================================
    # FIGURE
    # ==================================================

    fig = make_subplots(

        rows=2,
        cols=1,

        shared_xaxes=True,

        vertical_spacing=.12,

        row_heights=[
            .6,
            .4
        ],

        subplot_titles=(

            f"Parking Occupancy | "
            f"Assumed Stay: {stay_hours}h",

            "Street Flow vs Parking Stock"
        ),

        specs=[
            [{}],
            [{"secondary_y": True}]
        ]
    )

    hours = [
        f"{h:02d}:00"
        for h in range(24)
    ]

    # BACKGROUND ZONES

    zones = [

        (0,p50,
        'rgba(46,204,113,.08)'),

        (p50,p75,
        'rgba(241,196,15,.08)'),

        (p75,p90,
        'rgba(230,126,34,.08)'),

        (p90,1.05,
        'rgba(231,76,60,.08)')
    ]

    for y0,y1,color in zones:

        fig.add_hrect(
            y0=y0,
            y1=y1,
            fillcolor=color,
            line_width=0,
            layer="below",
            row=1,
            col=1
        )

        fig.add_hrect(
            y0=y0,
            y1=y1,
            fillcolor=color,
            line_width=0,
            layer="below",
            row=2,
            col=1
        )

    # BASELINE BAND

    fig.add_trace(

        go.Scatter(

            x=hours,
            y=bl["upper"],

            mode="lines",
            line=dict(width=0),

            showlegend=False
        ),

        row=1,
        col=1
    )

    fig.add_trace(

        go.Scatter(

            x=hours,
            y=bl["lower"],

            mode="lines",

            fill="tonexty",

            fillcolor=
            "rgba(41,128,185,.20)",

            line=dict(width=0),

            name=
            f"±2 std baseline (n={n_days})"
        ),

        row=1,
        col=1
    )

    fig.add_trace(

        go.Scatter(

            x=hours,
            y=bl["mean"],

            mode="lines+markers",

            line=dict(
                color="#2980b9",
                dash="dash"
            ),

            name=
            "Historical mean"
        ),

        row=1,
        col=1
    )

    # ACTUAL

    if not is_future and actual_occ.notna().any():

        colors = [

            [
                '#2ecc71',
                '#f1c40f',
                '#e67e22',
                '#e74c3c'
            ][stress_label(v)]

            if stress_label(v)>=0
            else '#ccc'

            for v in actual_occ.values
        ]

        fig.add_trace(

            go.Bar(

                x=hours,
                y=actual_occ.values,

                marker_color=colors,

                opacity=.6,

                name="Actual"
            ),

            row=1,
            col=1
        )

        fig.add_trace(

            go.Scatter(

                x=hours,
                y=actual_occ.values,

                mode=
                "lines+markers",

                line=dict(
                    color="#c0392b",
                    width=2.5
                ),

                name="Observed"
            ),

            row=1,
            col=1
        )

    # FLOW + STOCK

    occ_data = (
        bl["mean"]
        if is_future
        else actual_occ.values
    )

    cong_data = (
        bl["mean"]*1000
        if is_future
        else actual_cong.values
    )

    fig.add_trace(

        go.Scatter(

            x=hours,
            y=occ_data,

            mode="lines+markers",

            line=dict(
                color="#e74c3c",
                width=2.5
            ),

            name=
            "Parking Stock"
        ),

        row=2,
        col=1,
        secondary_y=False
    )

    fig.add_trace(

        go.Scatter(

            x=hours,
            y=cong_data,

            mode="lines+markers",

            line=dict(
                color="#2980b9",
                dash="dash"
            ),

            name=
            "Street Flow"
        ),

        row=2,
        col=1,
        secondary_y=True
    )

    # LAYOUT

    fig.update_layout(

        template="plotly_white",

        hovermode=
        "x unified",

        title=dict(

            text=
            f"Parking Analytics — "
            f"{target_date}",

            font=dict(
                size=18,
                family="Inter"
            )
        ),

        margin=dict(
            l=50,
            r=50,
            t=90,
            b=50
        ),

        legend=dict(
            orientation="h"
        )
    )

    fig.update_yaxes(

        title_text=
        "Occupancy",

        tickformat=".0%",

        range=[0,1.05],

        row=1,
        col=1
    )

    fig.update_yaxes(

        title_text=
        "Parking",

        tickformat=".0%",

        range=[0,1.05],

        row=2,
        col=1,
        secondary_y=False
    )

    fig.update_yaxes(

        title_text=
        "Congestion",

        row=2,
        col=1,
        secondary_y=True
    )

    # ======================================
# AI PARKING INSIGHT
# ======================================
# ======================================
# RETURN GRAPH ONLY
# ======================================

    return json.loads(
    plotly.utils
    .PlotlyJSONEncoder()
    .encode(fig)
)