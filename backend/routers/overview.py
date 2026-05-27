from fastapi import APIRouter
from services.analysis import get_overview, get_movement, get_stay, get_events, get_vitality

router = APIRouter(tags=["Overview"])


@router.get("/overview")
def overview():
    return get_overview()


@router.get("/movement")
def movement():
    return get_movement()


@router.get("/stay")
def stay():
    return get_stay()


@router.get("/events")
def events():
    return get_events()


@router.get("/vitality")
def vitality():
    return get_vitality()
