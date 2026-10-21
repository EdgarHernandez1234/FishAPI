import json
from pathlib import Path
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from nws import get_pressure_data_for_spot, get_hourly_forecast, precip_chance_now, get_wind_for_spot
from spots import SPOTS
from core_factors.precipitation_scorer import score_precipitation
from core_factors.season import score_season
from core_factors.sky_scorer import score_sky
from core_factors.wind_scorer import score_wind


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_methods=["GET"],
    allow_headers=["*"],
)

cdfw_file = Path(__file__).with_name("cdfw_approved_spots.json")
CDFW_SPOTS = json.loads(cdfw_file.read_text(encoding="utf-8"))
ALL_SPOTS = SPOTS + CDFW_SPOTS

@app.get("/api/spots")
def list_spots() -> list[dict]:
    return ALL_SPOTS


@app.get("/api/spots/{spot_id}/pressure")
def get_spot_pressure(spot_id: str) -> dict:
    spot = next((item for item in ALL_SPOTS if item["id"] == spot_id), None)

    if spot is None:
        raise HTTPException(status_code=404, detail="Spot not found")

    try:
        return get_pressure_data_for_spot(spot)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="NWS request failed")

@app.get("/api/spots/{spot_id}/precipitation-score")
def get_spot_precipitation_score(spot_id: str) -> dict:
    spot = next((item for item in ALL_SPOTS if item["id"] == spot_id), None)
    if spot is None:
        raise HTTPException(status_code=404, detail="Spot not found")

    try:
        periods = get_hourly_forecast(spot)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="NWS request failed")

    chance = precip_chance_now(periods)
    if chance is None:
        return {"status": "precipitation_unavailable", "chance_pct": None, "score": None}

    return {"status": "ok", "chance_pct": chance, "score": score_precipitation(chance)}

@app.get("/api/spots/{spot_id}/wind")
def get_spot_wind_score(spot_id: str) -> dict:
    spot = next((item for item in ALL_SPOTS if item["id"] == spot_id), None)

    if spot is None:
        raise HTTPException(status_code=404, detail="Spot not found")
    try:
        wind = get_wind_for_spot(spot)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="NWS request failed")

    wind_mph = wind["wind_mph"]
    if wind_mph is None:
        return {"status": "wind_unavailable", "wind_mph": None, "score": None}

    return {"status": "ok", "wind_mph": round(wind_mph, 1), "score": score_wind(wind_mph)}