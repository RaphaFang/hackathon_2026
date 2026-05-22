import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------
# PAGE CONFIG
# -----------------------------------

st.set_page_config(
    page_title="Kolding Pulse",
    page_icon="📍",
    layout="wide"
)

# -----------------------------------
# TITLE
# -----------------------------------

st.title("📍 Kolding Pulse")
st.subheader(
    "Understanding Urban Life in Kolding Centrum"
)

# -----------------------------------
# LOAD DATA
# -----------------------------------

movement = pd.read_excel(
    "Movement.xlsx"
)

stay = pd.read_excel(
    "StayDuration.xlsx"
)

events = pd.read_csv(
    "clean_kolding_events.csv"
)

# -----------------------------------
# FIX TIMESTAMPS
# -----------------------------------

movement["timestamp"] = pd.to_datetime(
    movement["timestamp"],
    utc=True,
    errors="coerce"
)

stay["timestamp"] = pd.to_datetime(
    stay["timestamp"],
    utc=True,
    errors="coerce"
)

movement = movement.dropna(
    subset=["timestamp"]
)

stay = stay.dropna(
    subset=["timestamp"]
)

# -----------------------------------
# PREPARE DATA
# -----------------------------------

stay["avg_stay_min"] = (
    stay["sum_ms"]
    /
    stay["objects"]
) / 1000 / 60

# safer pedestrian filter
pedestrian_mask = movement[
    "category"
].astype(str).str.lower().str.contains(
    "pedestrian",
    na=False
)

# -----------------------------------
# KPI ROW
# -----------------------------------

st.header("City Overview")

total_movement = (
    movement["amount"].sum()
)

pedestrians = (
    movement.loc[
        pedestrian_mask,
        "amount"
    ].sum()
)

total_events = len(events)

avg_stay = (
    stay["avg_stay_min"]
    .mean()
)

c1,c2,c3,c4 = st.columns(4)

c1.metric(
    "Total Movement",
    f"{int(total_movement):,}"
)

c2.metric(
    "Pedestrian Movement",
    f"{int(pedestrians):,}"
)

c3.metric(
    "Events",
    total_events
)

c4.metric(
    "Avg Stay (min)",
    f"{avg_stay:.1f}"
)

st.divider()

# -----------------------------------
# MOVEMENT TIMELINE
# -----------------------------------

st.header(
    "📈 City Activity Timeline"
)

move_time = (
    movement
    .groupby("timestamp")[
        "amount"
    ]
    .sum()
    .reset_index()
)

fig1 = px.line(
    move_time,
    x="timestamp",
    y="amount",
    title="Movement Over Time"
)

fig1.update_layout(
    xaxis_title="Time",
    yaxis_title="Movement Count"
)

st.plotly_chart(
    fig1,
    use_container_width=True
)

# -----------------------------------
# MOVEMENT CATEGORY
# -----------------------------------

st.header(
    "🚶 Mobility Composition"
)

cat = (
    movement
    .groupby("category")[
        "amount"
    ]
    .sum()
    .reset_index()
    .sort_values(
        "amount",
        ascending=False
    )
)

fig2 = px.bar(
    cat,
    x="category",
    y="amount",
    color="category",
    title="Movement by Category"
)

fig2.update_layout(
    xaxis_title="Category",
    yaxis_title="Movement"
)

st.plotly_chart(
    fig2,
    use_container_width=True
)

# -----------------------------------
# STAY DURATION
# -----------------------------------

st.header(
    "⏳ Where People Stay Longest"
)

stay_zone = (
    stay
    .groupby("sensor")[
        "avg_stay_min"
    ]
    .mean()
    .reset_index()
    .sort_values(
        "avg_stay_min",
        ascending=False
    )
)

fig3 = px.bar(
    stay_zone.head(10),
    x="avg_stay_min",
    y="sensor",
    orientation="h",
    title="Top Stay Duration Zones"
)

fig3.update_layout(
    xaxis_title="Average Stay (min)",
    yaxis_title="Sensor"
)

st.plotly_chart(
    fig3,
    use_container_width=True
)

# -----------------------------------
# MOVEMENT VS STAY
# -----------------------------------

st.header(
    "🔥 Movement vs Stay Behaviour"
)

move_daily = (
    movement
    .groupby(
        movement["timestamp"].dt.date
    )["amount"]
    .sum()
    .reset_index()
)

stay_daily = (
    stay
    .groupby(
        stay["timestamp"].dt.date
    )["avg_stay_min"]
    .mean()
    .reset_index()
)

merged = move_daily.merge(
    stay_daily,
    on="timestamp",
    how="inner"
)

fig4 = px.scatter(
    merged,
    x="amount",
    y="avg_stay_min",
    size="amount",
    title="Movement vs Stay Duration"
)

fig4.update_layout(
    xaxis_title="Movement",
    yaxis_title="Avg Stay (min)"
)

st.plotly_chart(
    fig4,
    use_container_width=True
)

# -----------------------------------
# EVENTS
# -----------------------------------

st.header(
    "🎭 Event Activity"
)

events["Year"] = (
    events["Date"]
    .astype(str)
    .str.extract(r'(20\d{2})')
)

event_count = (
    events["Year"]
    .value_counts()
    .sort_index()
    .reset_index()
)

event_count.columns = [
    "Year",
    "Events"
]

fig5 = px.bar(
    event_count,
    x="Year",
    y="Events",
    title="Events by Year"
)

fig5.update_layout(
    xaxis_title="Year",
    yaxis_title="Event Count"
)

st.plotly_chart(
    fig5,
    use_container_width=True
)
# -----------------------------------
# EVENT PREVIEW
# -----------------------------------

st.header(
    "📄 Event Dataset Preview"
)

st.dataframe(
    events.head(20),
    use_container_width=True
)

# -----------------------------------
# FOOTER
# -----------------------------------

st.divider()

st.caption(
    "Kolding Pulse • Urban vitality insights for Kolding Kommune"
)