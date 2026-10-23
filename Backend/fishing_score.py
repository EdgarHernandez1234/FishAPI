import re
from datetime import datetime

from core_factors.precipitation_scorer import score_precipitation
from core_factors.season import score_season
from core_factors.sky_scorer import score_sky
from core_factors.wind_scorer import score_wind
from core_factors.time_of_day import score_moon, score_time_of_day
from astral import moon

# placeholder weights: tune with your team
WEIGHTS = {
    "precipitation": 0.25,
    "water_temp": 0.15,
    "wind": 0.20,
    "pressure": 0.15,
    "season": 0.10,
    "sky": 0.10,
    "moon": 0.05,
}
TARGET_HOUR = 8   # each day is scored at the forecast hour closest to 8 AM local


def sky_pct_from_text(description: str | None) -> float | None:
    d = (description or "").lower()
    if "overcast" in d: return 100
    if "mostly cloudy" in d: return 75
    if "partly cloudy" in d or "partly sunny" in d: return 50
    if "mostly sunny" in d or "mostly clear" in d: return 20
    if "cloudy" in d: return 75
    if "sunny" in d or "clear" in d: return 0
    if "rain" in d or "shower" in d or "storm" in d: return 90
    return None


def wind_mph_from_period(period: dict) -> float | None:
    nums = [int(n) for n in re.findall(r"\d+", period.get("windSpeed") or "")]
    return sum(nums) / len(nums) if nums else None   # '5 to 10 mph' -> 7.5


def combine_scores(factors: dict) -> int | None:
    """Weighted average of the factors that have data (missing ones are skipped)."""
    available = {k: v for k, v in factors.items() if v is not None}
    if not available:
        return None
    total_weight = sum(WEIGHTS[k] for k in available)
    return round(sum(v * WEIGHTS[k] for k, v in available.items()) / total_weight)


def score_period(start: datetime, period: dict) -> dict:
    wind = wind_mph_from_period(period)
    sky = sky_pct_from_text(period.get("shortForecast"))
    precip = (period.get("probabilityOfPrecipitation") or {}).get("value")
    return {
        "wind": None if wind is None else score_wind(wind),
        "sky": None if sky is None else score_sky(sky),
        "precipitation": None if precip is None else score_precipitation(precip),
        "pressure": None,                       # added for today by the route
        "season": score_season(start.month),
        "moon": score_moon(moon.phase(start.date())),
    }


def build_days(periods: list[dict], max_days: int = 7, water_temp_scores: int | None = None) -> list[dict]:
    by_date = {}
    for period in periods:
        start = datetime.fromisoformat(period["startTime"])
        by_date.setdefault(start.date(), []).append((start, period))

    days = []
    for day in sorted(by_date)[:max_days]:
        start, period = min(by_date[day], key=lambda e: abs(e[0].hour - TARGET_HOUR))
        factors = score_period(start, period)
        factors["water_temp"] = (water_temp_scores or {}).get(day.isoformat())
        score = combine_scores(factors)
        if score is not None:
            days.append({"date": day.isoformat(), "score": score, "factors": factors})
    return days