
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


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from analysis import *
from agent import ask_agent

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