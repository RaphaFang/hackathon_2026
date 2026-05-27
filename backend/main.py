from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import ai, city, forecast, overview, parking

app = FastAPI(title="Kolding Pulse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(overview.router)
app.include_router(ai.router)
app.include_router(parking.router)
app.include_router(forecast.router)
app.include_router(city.router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


@app.get("/", tags=["Health"])
def home():
    return {"message": "Kolding Pulse Backend Running"}
