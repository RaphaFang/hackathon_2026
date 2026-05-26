# =====================================================
# CITY ACTIVITY ANALYSIS
# People present vs places open
# Weekday / Weekend / Public Holiday
# =====================================================

import pandas as pd
import plotly.express as px
from pathlib import Path
from agent import city_ai_insight
# =====================================================
# 1. LOAD DATA
# =====================================================

# =====================================================
# LOAD DATA (DYNAMIC PATHS)
# =====================================================

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

movement = pd.read_csv(
    DATA_DIR / "movement_stats_hourly.csv"
)

locations = pd.read_csv(
    DATA_DIR / "akseltorv_locations_cleaned_data.csv"
)

holidays = pd.read_csv(
    DATA_DIR / "Holidays_data_updated"
)

# =====================================================
# 2. PREPARE MOVEMENT DATA
# =====================================================

movement["timestamp"] = pd.to_datetime(
    movement["timestamp"],
    utc=True
).dt.tz_convert(
    "Europe/Copenhagen"
)

movement["date"] = (
    movement["timestamp"]
    .dt.date
)

movement["hour"] = (
    movement["timestamp"]
    .dt.hour
)

movement["weekday_num"] = (
    movement["timestamp"]
    .dt.weekday
)

movement["weekday_short"] = (
    movement["timestamp"]
    .dt.day_name()
    .str.lower()
    .str[:3]
)

# =====================================================
# 3. HOLIDAYS
# =====================================================

holidays["date"] = pd.to_datetime(
    holidays["date"]
).dt.date

holiday_dates = set(
    holidays["date"]
)

movement["is_public_holiday"] = (
    movement["date"]
    .isin(holiday_dates)
)

# =====================================================
# 4. DAY GROUPS
# =====================================================

movement["day_group"] = "Weekday"

movement.loc[
    movement["weekday_num"] >= 5,
    "day_group"
] = "Weekend"

movement.loc[
    movement["is_public_holiday"],
    "day_group"
] = "Public holiday"

# =====================================================
# 5. PEDESTRIAN MOVEMENT
# =====================================================

pedestrian_hourly = (

    movement[
        movement["category"]
        == "pedestrian"
    ]

    .groupby(
        [
            "day_group",
            "weekday_short",
            "hour"
        ],
        as_index=False
    )["amount"]

    .mean()

    .rename(
        columns={
            "amount":
            "avg_pedestrian_movement"
        }
    )
)

# =====================================================
# 6. CLEAN PLACE TYPES
# =====================================================

type_labels = {

    "food":
    "Restaurants / cafés",

    "retail":
    "Retail",

    "service":
    "Services",

    "public service":
    "Public services",

    "school":
    "Schools",

    "parking":
    "Parking",

    "nightclub":
    "Nightlife"
}

locations["place_type"] = (

    locations["type"]
    .map(type_labels)
    .fillna(
        locations["type"]
    )
)

# =====================================================
# 7. OPENING HOURS HELPERS
# =====================================================

def time_to_hour(value):

    if pd.isna(value):
        return None

    value = str(value).strip().lower()

    if value in [
        "closed",
        ""
    ]:
        return None

    try:
        return int(
            value.split(":")[0]
        )

    except:
        return None


def is_open_at_hour(
    row,
    day,
    hour,
    is_public_holiday=False
):

    if is_public_holiday:

        public_open = row.get(
            "public_holiday_open"
        )

        if (
            pd.isna(public_open)
            or
            str(public_open)
            .strip()
            .lower()
            in [
                "closed",
                ""
            ]
        ):
            return False

        public_close = row.get(
            "public_holiday_close"
        )

        if (
            public_close is not None
            and
            not pd.isna(public_close)
        ):

            open_hour = time_to_hour(
                public_open
            )

            close_hour = time_to_hour(
                public_close
            )

        else:

            open_hour = time_to_hour(
                row.get("open_sun")
            )

            close_hour = time_to_hour(
                row.get("close_sun")
            )

    else:

        open_hour = time_to_hour(
            row.get(
                f"open_{day}"
            )
        )

        close_hour = time_to_hour(
            row.get(
                f"close_{day}"
            )
        )

    if (
        open_hour is None
        or
        close_hour is None
    ):
        return False

    # Normal hours

    if open_hour < close_hour:

        return (
            open_hour
            <= hour
            < close_hour
        )

    # Overnight

    if open_hour > close_hour:

        return (
            hour >= open_hour
            or hour < close_hour
        )

    return False

# =====================================================
# 8. COUNT OPEN PLACES
# =====================================================

rows = []

day_groups = {

    "Weekday":
    [
        "mon",
        "tue",
        "wed",
        "thu",
        "fri"
    ],

    "Weekend":
    [
        "sat",
        "sun"
    ],

    "Public holiday":
    [
        "sun"
    ]
}

place_types = sorted(
    locations[
        "place_type"
    ]
    .dropna()
    .unique()
)

for (
    day_group,
    days
) in day_groups.items():

    for day in days:

        for hour in range(24):

            open_mask = locations.apply(

                lambda row:
                is_open_at_hour(

                    row,
                    day,
                    hour,

                    is_public_holiday=(
                        day_group
                        ==
                        "Public holiday"
                    )
                ),

                axis=1
            )

            open_places = locations[
                open_mask
            ]

            for place_type in place_types:

                rows.append({

                    "day_group":
                    day_group,

                    "weekday_short":
                    day,

                    "hour":
                    hour,

                    "place_type":
                    place_type,

                    "open_count":
                    len(

                        open_places[
                            open_places[
                                "place_type"
                            ]
                            ==
                            place_type
                        ]
                    )
                })

open_by_type = pd.DataFrame(
    rows
)

# =====================================================
# 9. CONNECT PEOPLE + OPEN PLACES
# =====================================================

combined = open_by_type.merge(

    pedestrian_hourly,

    on=[
        "day_group",
        "weekday_short",
        "hour"
    ],

    how="left"
)

combined[
    "avg_pedestrian_movement"
] = combined[
    "avg_pedestrian_movement"
].fillna(0)

# Core metric

combined[
    "movement_while_open"
] = (

    combined[
        "open_count"
    ]

    *

    combined[
        "avg_pedestrian_movement"
    ]
)

# =====================================================
# 10. AGGREGATE
# =====================================================

heatmap_data = (

    combined

    .groupby(
        [
            "day_group",
            "place_type",
            "hour"
        ],
        as_index=False
    )

    .agg(

        open_count=(
            "open_count",
            "mean"
        ),

        avg_pedestrian_movement=(
            "avg_pedestrian_movement",
            "mean"
        ),

        movement_while_open=(
            "movement_while_open",
            "mean"
        )
    )
)

# =====================================================
# 11. CREATE HEATMAPS
# =====================================================
city_insights = {}

output_folder = Path(
    "plotly_heatmaps"
)

output_folder.mkdir(
    exist_ok=True
)

for group in [

    "Weekday",
    "Weekend",
    "Public holiday"

]:

    subset = heatmap_data[
        heatmap_data[
            "day_group"
        ]
        ==
        group
    ].copy()

    order = (

        subset
        .groupby(
            "place_type"
        )[
            "movement_while_open"
        ]
        .sum()
        .sort_values(
            ascending=False
        )
        .index
        .tolist()
    )

    matrix = (

        subset

        .pivot(
            index="place_type",
            columns="hour",
            values="movement_while_open"
        )

        .fillna(0)
        .reindex(order)
    )

    # =====================================
    # AI FROM GRAPH OUTPUT
    # =====================================

    peak_place = matrix.sum(
        axis=1
    ).idxmax()

    peak_hour = int(
        matrix.sum(
            axis=0
        ).idxmax()
    )

    peak_value = int(
        matrix.values.max()
    )

    stats_text = f"""
    Heatmap output:

    Day group:
    {group}

    Peak place:
    {peak_place}

    Peak hour:
    {peak_hour}:00

    Peak value:
    {peak_value}
    """

    try:

        insight = city_ai_insight(
            stats_text
        )

    except:

        insight = (
            "AI city insight "
            "unavailable."
        )

    city_insights[group] = insight

    fig = px.imshow(

        matrix,

        labels={

            "x":
            "Hour of day",

            "y":
            "Type of place",

            "color":
            "Open places × People present"
        },

        title=
        f"Urban Activity Pattern — {group}",

        aspect="auto",

        text_auto=".0f",

        color_continuous_scale="Blues"
    )

    fig.update_layout(

        height=650,
        width=1200,

        title_x=.5,

        font=dict(
            family="Inter"
        ),

        xaxis=dict(
            tickmode="linear",
            tick0=0,
            dtick=1
        )
    )

    file_name = (
        f"plotly_heatmap_"
        f"{group.lower().replace(' ','_')}"
        ".html"
    )

    file_path = (
        output_folder
        / file_name
    )

    fig.write_html(
        file_path
    )

    print(
    f"{group} AI:",
    insight
)

    print(
        f"Saved: {file_path}"
    )

print(
    "All city heatmaps generated."
)

CITY_INSIGHTS = city_insights