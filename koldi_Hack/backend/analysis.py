
import pandas as pd

movement = pd.read_excel("data/Movement.xlsx")
stay = pd.read_excel("data/StayDuration.xlsx")
events = pd.read_csv("data/clean_kolding_events.csv")

movement["timestamp"] = pd.to_datetime(movement["timestamp"], utc=True, errors="coerce")
stay["timestamp"] = pd.to_datetime(stay["timestamp"], utc=True, errors="coerce")

movement = movement.dropna(subset=["timestamp"])
stay = stay.dropna(subset=["timestamp"])

stay["avg_stay_min"] = (stay["sum_ms"]/stay["objects"])/1000/60

def get_overview():
    return {
        "movement": float(movement["amount"].sum()),
        "events": int(len(events)),
        "avg_stay": float(stay["avg_stay_min"].mean())
    }

def get_movement():
    df = movement.groupby("timestamp")["amount"].sum().reset_index()
    df["timestamp"] = df["timestamp"].astype(str)
    return df.to_dict(orient="records")

def get_stay():
    df = stay.groupby("sensor")["avg_stay_min"].mean().reset_index().sort_values("avg_stay_min", ascending=False).head(10)
    return df.to_dict(orient="records")

def get_events():
    events["Year"] = events["Date"].astype(str).str.extract(r'(20\d{2})')
    df = events["Year"].value_counts().sort_index().reset_index()
    df.columns=["year","events"]
    return df.to_dict(orient="records")

def get_vitality():
    move_daily = movement.groupby(movement["timestamp"].dt.date)["amount"].sum().reset_index()
    stay_daily = stay.groupby(stay["timestamp"].dt.date)["avg_stay_min"].mean().reset_index()
    merged = move_daily.merge(stay_daily,on="timestamp",how="inner")
    return merged.to_dict(orient="records")
