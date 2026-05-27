import json

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.utils
from plotly.subplots import make_subplots

from config import DATA_DIR

# ── Load data ──────────────────────────────────────────────────────────────────
try:
    df_cum   = pd.read_csv(DATA_DIR / "cache_parking_hourly_sim.csv")
    baseline = pd.read_csv(DATA_DIR / "cache_parking_baseline.csv")
    parking  = pd.read_csv(DATA_DIR / "parking_snapshot.csv")

    core_capacity  = int(parking[parking["distance_km"] <= 0.5]["spaceCount"].sum())
    total_capacity = int(parking[parking["distance_km"] <= 0.7]["spaceCount"].sum())
except FileNotFoundError as e:
    raise RuntimeError(f"Missing parking dataset: {e}")

# ── Stress thresholds ──────────────────────────────────────────────────────────
p50 = df_cum["occupancy_rate"].quantile(0.50)
p75 = df_cum["occupancy_rate"].quantile(0.75)
p90 = df_cum["occupancy_rate"].quantile(0.90)


def _stress_label(val: float) -> int:
    if pd.isna(val):
        return -1
    if val >= p90:
        return 3
    if val >= p75:
        return 2
    if val >= p50:
        return 1
    return 0


# ── Special event days ─────────────────────────────────────────────────────────
SPECIAL_DATES = {
    "2026-02-07", "2026-02-08", "2026-02-09", "2026-02-10", "2026-02-11",
    "2026-02-12", "2026-02-13", "2026-02-14", "2026-02-15", "2026-02-26",
    "2026-03-08", "2026-03-24", "2026-03-28", "2026-03-29", "2026-03-30",
    "2026-03-31", "2026-04-01", "2026-04-02", "2026-04-03", "2026-04-04",
    "2026-04-05", "2026-04-06", "2026-04-12", "2026-04-25", "2026-05-01",
    "2026-05-06",
}
event_dates_set = set(pd.to_datetime(list(SPECIAL_DATES)).date)

STRESS_COLORS = ["#2ecc71", "#f1c40f", "#e67e22", "#e74c3c"]
ZONE_COLORS   = [
    (0,    p50,  "rgba(46,204,113,.08)"),
    (p50,  p75,  "rgba(241,196,15,.08)"),
    (p75,  p90,  "rgba(230,126,34,.08)"),
    (p90,  1.05, "rgba(231,76,60,.08)"),
]


# ── Main analytics function ────────────────────────────────────────────────────

def get_parking_analytics(date: str = "2026-02-14") -> dict:
    target_date = pd.to_datetime(date).date()
    is_future   = target_date > pd.to_datetime(df_cum["date"].max()).date()
    weekday     = pd.to_datetime(target_date).dayofweek
    day_type    = "weekend" if weekday >= 5 else "weekday"
    is_special  = 1 if target_date in event_dates_set else 0
    target_group = f"{day_type}_{'special' if is_special else 'regular'}"

    bl = (
        baseline[baseline["group"] == target_group]
        .sort_values("hour")
        .set_index("hour")
        .reindex(range(24))
    )

    n_days     = bl["n"].iloc[0] if not bl.empty else 0
    stay_hours = (
        df_cum[df_cum["group"] == target_group]["stay_hours"].iloc[0]
        if not df_cum[df_cum["group"] == target_group].empty
        else 0
    )

    if is_future:
        actual_occ  = pd.Series([np.nan] * 24)
        actual_cong = pd.Series([np.nan] * 24)
    else:
        day_match   = (
            df_cum[df_cum["date"] == str(target_date)]
            .sort_values("hour")
            .set_index("hour")
        )
        actual_occ  = day_match["occupancy_rate"].reindex(range(24))
        actual_cong = day_match["congestion_score"].reindex(range(24))

    # ── Build figure ──────────────────────────────────────────────────────────
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        row_heights=[0.6, 0.4],
        subplot_titles=(
            f"Parking Occupancy | Assumed Stay: {stay_hours}h",
            "Street Flow vs Parking Stock",
        ),
        specs=[[{}], [{"secondary_y": True}]],
    )

    hours = [f"{h:02d}:00" for h in range(24)]

    for y0, y1, color in ZONE_COLORS:
        for row in (1, 2):
            fig.add_hrect(y0=y0, y1=y1, fillcolor=color, line_width=0, layer="below", row=row, col=1)

    # Baseline band
    fig.add_trace(
        go.Scatter(x=hours, y=bl["upper"], mode="lines", line=dict(width=0), showlegend=False),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=hours, y=bl["lower"], mode="lines",
            fill="tonexty", fillcolor="rgba(41,128,185,.20)",
            line=dict(width=0), name=f"±2 std baseline (n={n_days})",
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=hours, y=bl["mean"], mode="lines+markers",
            line=dict(color="#2980b9", dash="dash"), name="Historical mean",
        ),
        row=1, col=1,
    )

    # Actual bars
    if not is_future and actual_occ.notna().any():
        colors = [
            STRESS_COLORS[_stress_label(v)] if _stress_label(v) >= 0 else "#ccc"
            for v in actual_occ.values
        ]
        fig.add_trace(
            go.Bar(x=hours, y=actual_occ.values, marker_color=colors, opacity=0.6, name="Actual"),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=hours, y=actual_occ.values, mode="lines+markers",
                line=dict(color="#c0392b", width=2.5), name="Observed",
            ),
            row=1, col=1,
        )

    occ_data  = bl["mean"]            if is_future else actual_occ.values
    cong_data = bl["mean"] * 1000     if is_future else actual_cong.values

    fig.add_trace(
        go.Scatter(
            x=hours, y=occ_data, mode="lines+markers",
            line=dict(color="#e74c3c", width=2.5), name="Parking Stock",
        ),
        row=2, col=1, secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=hours, y=cong_data, mode="lines+markers",
            line=dict(color="#2980b9", dash="dash"), name="Street Flow",
        ),
        row=2, col=1, secondary_y=True,
    )

    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        title=dict(text=f"Parking Analytics — {target_date}", font=dict(size=18, family="Inter")),
        margin=dict(l=50, r=50, t=90, b=50),
        legend=dict(orientation="h"),
    )
    fig.update_yaxes(title_text="Occupancy", tickformat=".0%", range=[0, 1.05], row=1, col=1)
    fig.update_yaxes(title_text="Parking",   tickformat=".0%", range=[0, 1.05], row=2, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Congestion", row=2, col=1, secondary_y=True)

    return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))


# ── Congestion data (loaded once) ──────────────────────────────────────────────
try:
    df_congestion   = pd.read_csv(DATA_DIR / "precomputed_hourly_congestion.csv")
    df_cong_baseline = pd.read_csv(DATA_DIR / "precomputed_baseline.csv")
except FileNotFoundError as e:
    raise RuntimeError(f"Missing congestion dataset: {e}")


def get_congestion_analytics(date: str = "2026-02-14") -> dict:
    target_date  = pd.to_datetime(date).date()
    max_hist     = pd.to_datetime(df_congestion["date"].max()).date()
    is_future    = target_date > max_hist
    weekday      = pd.to_datetime(target_date).dayofweek
    day_type     = "weekend" if weekday >= 5 else "weekday"
    is_special   = 1 if target_date in event_dates_set else 0
    target_group = f"{day_type}_{'special' if is_special else 'regular'}"

    bl = (
        df_cong_baseline[df_cong_baseline["group"] == target_group]
        .sort_values("hour")
        .set_index("hour")
        .reindex(range(24))
    )
    n_days = int(bl["n"].iloc[0]) if not bl.empty else 0

    if is_future:
        actual = pd.Series([None] * 24, index=range(24))
    else:
        day_rows = df_congestion[df_congestion["date"] == str(target_date)]
        actual   = day_rows.set_index("hour")["congestion_score"].reindex(range(24))

    hours = [f"{h:02d}:00" for h in range(24)]

    fig = go.Figure()

    # Band
    fig.add_trace(go.Scatter(
        x=hours, y=bl["upper"], mode="lines", line=dict(width=0), showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=hours, y=bl["lower"], mode="lines", line=dict(width=0),
        fill="tonexty", fillcolor="rgba(31,119,180,.15)",
        name=f"±2 std range (n={n_days} days)",
    ))

    # Mean baseline
    fig.add_trace(go.Scatter(
        x=hours, y=bl["mean"], mode="lines+markers",
        line=dict(color="#1f77b4", width=2, dash="dash"),
        marker=dict(size=4, symbol="square"),
        name="Historical mean",
    ))

    # Actual
    if not is_future and actual.notna().any():
        fig.add_trace(go.Scatter(
            x=hours, y=actual.values, mode="lines+markers",
            line=dict(color="#d62728", width=2.5),
            marker=dict(size=5),
            name=f"Actual ({target_date})",
        ))

        # Congested hours (above upper band)
        congested = [
            h for h in range(24)
            if pd.notna(actual.iloc[h]) and pd.notna(bl["upper"].iloc[h])
            and actual.iloc[h] > bl["upper"].iloc[h]
        ]
        if congested:
            fig.add_trace(go.Scatter(
                x=[hours[h] for h in congested],
                y=[actual.iloc[h] for h in congested],
                mode="markers",
                marker=dict(color="#d62728", size=10, symbol="triangle-up"),
                name="Above expected (congested)",
            ))

    mode_label = "Future Forecast" if is_future else "Historical Analytics"
    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        title=dict(
            text=f"Street Congestion — {mode_label} | {target_date}",
            font=dict(size=16, family="Inter"),
        ),
        legend=dict(orientation="h"),
        margin=dict(l=50, r=30, t=70, b=50),
        xaxis=dict(title="Hour of day"),
        yaxis=dict(title="Estimated vehicles on street", gridcolor="#eee", zeroline=False),
    )

    return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))