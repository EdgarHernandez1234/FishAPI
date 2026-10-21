import json
from pathlib import Path
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from nws import get_pressure_data_for_spot
from spots import SPOTS
from math import asin, cos, radians, sin, sqrt
from cities import CITY_SEARCH_AREAS

def distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    )
    return 2 * 3958.8 * asin(min(1, sqrt(a)))

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
def list_spots(city: str | None = None) -> list[dict]:
    if city is None:
        return ALL_SPOTS

    city_id = city.strip().lower().replace(" ", "-")
    search_area = CITY_SEARCH_AREAS.get(city_id)

    if search_area is None:
        raise HTTPException(status_code=404, detail="City not supported yet")

    return [
        spot for spot in ALL_SPOTS
        if distance_miles(
            search_area["latitude"],
            search_area["longitude"],
            spot["latitude"],
            spot["longitude"],
        ) <= search_area["radius_miles"]
    ]

@app.get("/api/spots/{spot_id}/pressure")
def get_spot_pressure(spot_id: str) -> dict:
    spot = next((item for item in ALL_SPOTS if item["id"] == spot_id), None)

    if spot is None:
        raise HTTPException(status_code=404, detail="Spot not found")

    try:
        return get_pressure_data_for_spot(spot)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="NWS request failed")