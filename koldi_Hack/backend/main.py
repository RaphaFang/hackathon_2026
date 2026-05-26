
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from analysis import *
# from agent import ask_agent
# from pydantic import BaseModel

# app = FastAPI(title="Kolding Pulse API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# class Question(BaseModel):
#     question: str

# @app.get("/")
# def home():
#     return {"message":"Kolding Pulse Backend Running"}

# @app.get("/overview")
# def overview():
#     return get_overview()

# @app.get("/movement")
# def movement():
#     return get_movement()

# @app.get("/stay")
# def stay():
#     return get_stay()

# @app.get("/events")
# def events():
#     return get_events()

# @app.get("/vitality")
# def vitality():
#     return get_vitality()

# @app.post("/ask")
# def ask(q: Question):
#     return {"answer": ask_agent(q.question)}


from fastapi import FastAPI , Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from analysis import *
from agent import ask_agent , parking_ai_insight , forecast_ai_insight
from parking_analysis import get_parking_analytics
from forecast_analysis import get_forecast_data, get_forecast_insight
from city_activity_analysis import CITY_INSIGHTS

app = FastAPI(
    title="Kolding Pulse API"
)

# CORS

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model

class Question(BaseModel):
    question:str


# HOME

@app.get("/")
def home():
    return {
        "message":
        "Kolding Pulse Backend Running"
    }


# OVERVIEW

@app.get("/overview")
def overview():
    return get_overview()


# MOVEMENT

@app.get("/movement")
def movement():
    return get_movement()


# STAY

@app.get("/stay")
def stay():
    return get_stay()


# EVENTS

@app.get("/events")
def events():
    return get_events()


# VITALITY

@app.get("/vitality")
def vitality():
    return get_vitality()


# ASK AI

@app.post("/ask")
def ask(q:Question):

    answer = ask_agent(
        q.question
    )

    return {
        "answer":answer
    }


# AI INSIGHT CARD

@app.get("/insight")
def insight():

    insight_text = ask_agent(
        """
Give ONE short urban insight from the Kolding data.
Maximum 1 sentence.
"""
    )

    return {
        "insight":
        insight_text
    }


# HEALTH CHECK

@app.get("/health")
def health():
    return {
        "status":"ok"
    }

# Parking

@app.get("/parking-analysis")
def parking_analysis(
    date: str = Query("2026-02-14")
):
    return get_parking_analytics(date)

# PARKING AI INSIGHT

@app.get("/parking-insight")
def parking_insight():

    stats_text = """
Peak occupancy 39%
Average occupancy 28%
Peak hour 14:00
"""

    insight = parking_ai_insight(
        stats_text
    )

    return {
        "insight": insight
    }

# ======================================
# FORECAST DATA
# ======================================

@app.get("/forecast-data")
def forecast_data():

    return get_forecast_data()


# ======================================
# FORECAST AI
# ======================================

@app.get("/forecast-insight")
def forecast_insight():

    return {
        "insight":
        get_forecast_insight()
    }

# CITY

@app.get("/city-insight")
def city_insight():

    return CITY_INSIGHTS

# =========================
# FORECAST AI INSIGHT
# =========================

@app.post("/forecast-insight")
def forecast_insight(
    data: dict
):

    try:

        stats_text = f"""
Scenario:
{data["scenario"]}

Expected arrivals:
{data["expected"]}

Likely range:
{data["range"]}

Peak hour:
{data["peak"]}
"""

        insight = forecast_ai_insight(
            stats_text
        )

        return {
            "insight":
            insight
        }

    except:

        return {
            "insight":
            "AI forecast insight temporarily unavailable."
        }