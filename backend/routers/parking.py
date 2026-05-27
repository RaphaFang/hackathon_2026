from fastapi import APIRouter, Query
from services.parking import get_parking_analytics, get_congestion_analytics
from services.agent import parking_ai_insight

router = APIRouter(tags=["Parking"])


@router.get("/parking-analysis")
def parking_analysis(date: str = Query("2026-02-14")):
    return get_parking_analytics(date)


@router.get("/congestion-analysis")
def congestion_analysis(date: str = Query("2026-02-14")):
    return get_congestion_analytics(date)


@router.get("/parking-insight")
def parking_insight():
    stats_text = "Peak occupancy 39%\nAverage occupancy 28%\nPeak hour 14:00"
    return {"insight": parking_ai_insight(stats_text)}