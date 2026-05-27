from fastapi import APIRouter
from pydantic import BaseModel
from services.agent import ask_agent
from services.analysis import get_full_ai_context

router = APIRouter(tags=["AI"])


class Question(BaseModel):
    question: str


@router.post("/ask")
def ask(q: Question):
    context = get_full_ai_context()
    return {"answer": ask_agent(q.question, context)}


@router.get("/insight")
def insight():
    context = get_full_ai_context()
    text    = ask_agent("Give ONE short urban insight from the Kolding data. Maximum 1 sentence.", context)
    return {"insight": text}
