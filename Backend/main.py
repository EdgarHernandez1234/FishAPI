from datetime import datetime
import time
import json
from pathlib import Path
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from nws import get_pressure_data_for_spot, get_hourly_forecast, precip_chance_now, get_wind_for_spot
from spots import SPOTS
from nws import get_hourly_pressure_forecast
from math import asin, cos, radians, sin, sqrt
from cities import CITY_SEARCH_AREAS
from core_factors.precipitation_scorer import score_precipitation
from core_factors.season import score_season
from core_factors.sky_scorer import score_sky
from core_factors.wind_scorer import score_wind
from core_factors.time_of_day import score_time_of_day, get_sun_times
from location_dependent_factors.barometric_pressure_scorer import pressure_scorer
from fishing_score import build_days, combine_scores, explain_day
from core_factors.water_temp_scorer import score_water_temp
from Database.db import db, posts
from Database import community
from Database.models import PostCreate, CommentCreate, VoteRequest

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
        "https://fishscorer.onrender.com",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

cdfw_file = Path(__file__).with_name("cdfw_approved_spots.json")
CDFW_SPOTS = json.loads(cdfw_file.read_text(encoding="utf-8"))
ALL_SPOTS = SPOTS + CDFW_SPOTS

_cache = {}               # (lat, lon) -> (saved_at, temperature in °C)
CACHE_SECONDS = 3600


def estimate_water_temps_c(lat: float, lon: float, past_days: int = 14,
                           forecast_days: int = 7, k: float = 0.15) -> dict[str, float]:
    """Estimated water temperature (°C) for each date, from past and forecast air temperatures."""
    key = (round(lat, 3), round(lon, 3))
    saved = _cache.get(key)
    if saved and time.time() - saved[0] < CACHE_SECONDS:
        return saved[1]

    response = httpx.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": lat, "longitude": lon, "daily": "temperature_2m_mean",
                "past_days": past_days, "forecast_days": forecast_days, "timezone": "auto"},
        timeout=15.0,
    )
    response.raise_for_status()
    daily = response.json()["daily"]

    water = None
    result = {}
    for date, air in zip(daily["time"], daily["temperature_2m_mean"]):
        if air is None:
            if water is None:
                continue
        elif water is None:
            water = air
        else:
            water += k * (air - water)
        result[date] = water

    _cache[key] = (time.time(), result)
    return result

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


@app.get("/api/spots/{spot_id}/time-score")
def get_spot_time_score(spot_id: str) -> dict:
    spot = next((item for item in ALL_SPOTS if item["id"] == spot_id), None)

    if spot is None:
        raise HTTPException(status_code=404, detail="Spot not found")

    try:
        local_time, sunrise, sunset = get_sun_times(
            latitude=spot["latitude"],
            longitude=spot["longitude"],
        )

        score = score_time_of_day(local_time, sunrise, sunset)

        return {
            "status": "ok",
            "local_time": local_time.isoformat(),
            "sunrise": sunrise.isoformat(),
            "sunset": sunset.isoformat(),
            "score": score,
        }

    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/api/spots/{spot_id}/season-score")
def get_spot_season_score(spot_id: str) -> dict:
    spot = next((item for item in ALL_SPOTS if item["id"] == spot_id), None)

    if spot is None:
        raise HTTPException(status_code=404, detail="Spot not found")

    try:
        local_time, _, _ = get_sun_times(
            latitude=spot["latitude"],
            longitude=spot["longitude"],
        )

        score = score_season(local_time.month)

        return {
            "status": "ok",
            "month": local_time.month,
            "score": score,
        }

    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))



@app.get("/api/spots/{spot_id}/sky-score")
def get_spot_sky_score(spot_id: str) -> dict:
    spot = next(
        (item for item in ALL_SPOTS if item["id"] == spot_id),
        None,
    )

    if spot is None:
        raise HTTPException(status_code=404, detail="Spot not found")

    try:
        periods = get_hourly_forecast(spot)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="NWS request failed")

    if not periods:
        return {
            "status": "sky_unavailable",
            "cloud_cover_pct": None,
            "score": None,
        }

    # Find the forecast period containing the current time.
    now = datetime.now().astimezone()
    current_period = None

    for period in periods:
        start = datetime.fromisoformat(period["startTime"])
        end = datetime.fromisoformat(period["endTime"])

        if start <= now < end:
            current_period = period
            break

    if current_period is None:
        return {
            "status": "sky_unavailable",
            "cloud_cover_pct": None,
            "score": None,
        }

    # Prefer an actual sky-cover value if the API provides one.
    cloud_cover = current_period.get("skyCover")

    if isinstance(cloud_cover, dict):
        cloud_cover = cloud_cover.get("value")

    if cloud_cover is not None:
        try:
            cloud_cover = float(cloud_cover)
        except (ValueError, TypeError):
            cloud_cover = None

    # Otherwise estimate cloud cover from the forecast description.
    if cloud_cover is None:
        description = (
            current_period.get("shortForecast") or ""
        ).lower()

        if "overcast" in description:
            cloud_cover = 100
        elif "mostly cloudy" in description:
            cloud_cover = 75
        elif "partly cloudy" in description:
            cloud_cover = 50
        elif "mostly sunny" in description or "mostly clear" in description:
            cloud_cover = 20
        elif "cloudy" in description:
            cloud_cover = 75
        elif "partly sunny" in description:
            cloud_cover = 50
        elif "sunny" in description or "clear" in description:
            cloud_cover = 0

    if cloud_cover is None:
        return {
            "status": "sky_unavailable",
            "cloud_cover_pct": None,
            "score": None,
        }

    score = score_sky(cloud_cover)

    return {
        "status": "ok",
        "cloud_cover_pct": cloud_cover,
        "score": score,
    }


@app.get("/api/spots/{spot_id}/pressure-score")
def get_spot_pressure_score(spot_id: str) -> dict:
    spot = next(
        (item for item in ALL_SPOTS if item["id"] == spot_id),
        None,
    )

    if spot is None:
        raise HTTPException(status_code=404, detail="Spot not found")

    try:
        data = get_pressure_data_for_spot(spot)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="NWS request failed")

    change = data["change_hpa_3h"]

    if change is None:
        return {
            "status": "pressure_unavailable",
            "pressure_hpa": data["pressure_hpa"],
            "change_hpa_3h": None,
            "score": None,
        }

    return {
        "status": "ok",
        "pressure_hpa": data["pressure_hpa"],
        "pressure_3h_ago_hpa": data["pressure_3h_ago_hpa"],
        "change_hpa_3h": change,
        "score": pressure_scorer(change),
    }

@app.get("/api/spots/{spot_id}/score")
def get_spot_score(spot_id: str) -> dict:
    spot = next((item for item in ALL_SPOTS if item["id"] == spot_id), None)
    if spot is None:
        raise HTTPException(status_code=404, detail="Spot not found")

    try:
        periods = get_hourly_forecast(spot)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="NWS request failed")

    try:
        water_by_date = estimate_water_temps_c(spot["latitude"], spot["longitude"])
    except (httpx.HTTPError, KeyError):
        water_by_date = {}
    water_scores = {d: score_water_temp(t) for d, t in water_by_date.items()}

    days = build_days(periods, water_temp_scores=water_scores)
    for day in days:
        day["inputs"]["water_temp"] = water_by_date.get(day["date"])
  
    # pressure only exists for right now, so it only goes on the first day
    try:
        change = get_pressure_data_for_spot(spot)["change_hpa_3h"]
        if days and change is not None:
            days[0]["factors"]["pressure"] = pressure_scorer(change)
            days[0]["inputs"]["pressure"] = change
            days[0]["score"] = combine_scores(days[0]["factors"])
    except (httpx.HTTPError, KeyError):
        pass   # pressure is optional

    for day in days:
        day["explanation"] = explain_day(day)

    return {"spot": spot,
            "water_temps_c": {d["date"]: round(water_by_date[d["date"]], 1)
                              for d in days if d["date"] in water_by_date},
            "water_temp_estimated": True, "days": days}

@app.get("/api/posts")
def get_posts() -> list[dict]:
    return community.list_posts()


@app.post("/api/posts", status_code=201)
def create_post(post: PostCreate) -> dict:
    return community.create_post(post.model_dump())


@app.post("/api/posts/{post_id}/comments", status_code=201)
def add_comment(post_id: str, comment: CommentCreate) -> dict:
    result = community.add_comment(post_id, comment.model_dump())
    if result is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return result


@app.post("/api/posts/{post_id}/vote")
def vote_on_post(post_id: str, body: VoteRequest) -> dict:
    result = community.vote(post_id, body.direction, body.previous)
    if result is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return result