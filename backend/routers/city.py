from fastapi import APIRouter
from services.city import build_city_insight_prompts
from services.agent import city_ai_insight

router = APIRouter(tags=["City"])

# Cache populated on first request — avoids heavy computation at startup
_city_insights_cache: dict | None = None


def _get_city_insights() -> dict:
    global _city_insights_cache
    if _city_insights_cache is not None:
        return _city_insights_cache

    prompts = build_city_insight_prompts()
    result  = {}
    for group, prompt in prompts.items():
        try:
            result[group] = city_ai_insight(prompt)
        except Exception:
            result[group] = "AI city insight unavailable."

    _city_insights_cache = result
    return result


@router.get("/city-insight")
def city_insight():
    return _get_city_insights()
