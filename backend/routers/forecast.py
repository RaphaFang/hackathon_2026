from fastapi import APIRouter
from services.forecast import get_forecast_data, build_forecast_insight_prompt
from services.agent import forecast_ai_insight

router = APIRouter(tags=["Forecast"])


@router.get("/forecast-data")
def forecast_data():
    return get_forecast_data()


@router.post("/forecast-insight")
def forecast_insight(data: dict):
    try:
        stats_text = (
            f"Scenario: {data['scenario']}\n"
            f"Expected arrivals: {data['expected']}\n"
            f"Likely range: {data['range']}\n"
            f"Peak hour: {data['peak']}"
        )
        return {"insight": forecast_ai_insight(stats_text)}
    except Exception:
        return {"insight": "AI forecast insight temporarily unavailable."}
