import json
from pathlib import Path
import httpx
from fastapi import FastAPI, HTTPException

from nws import get_pressure_data_for_spot
from spots import SPOTS

app = FastAPI()
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