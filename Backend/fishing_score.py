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

FACTOR_LABELS = {
    "precipitation": "Rain chance", "water_temp": "Water temperature",
    "wind": "Wind", "pressure": "Pressure trend", "season": "Season",
    "sky": "Cloud cover", "moon": "Moon phase",
}


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
    """Calculate a weighted score and compress the high end."""
    available = {
        key: value
        for key, value in factors.items()
        if value is not None
    }

    if not available:
        return None

    total_weight = sum(WEIGHTS[key] for key in available)

    raw_score = sum(
        value * WEIGHTS[key]
        for key, value in available.items()
    ) / total_weight

    # Leave scores at or below 75 unchanged.
    # Compress higher scores so 90+ is less common.
    if raw_score <= 75:
        calibrated_score = raw_score
    else:
        calibrated_score = 75 + (raw_score - 75) * 0.7

    return round(max(0, min(100, calibrated_score)))


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


def build_days(periods: list[dict], max_days: int = 7, water_temp_scores: dict[str, int] | None = None) -> list[dict]:
    by_date = {}

    for period in periods:
        start = datetime.fromisoformat(period["startTime"])
        by_date.setdefault(start.date(), []).append((start, period))

    days = []

    for day in sorted(by_date)[:max_days]:
        start, period = min(
            by_date[day],
            key=lambda e: abs(e[0].hour - TARGET_HOUR),
        )

        factors = score_period(start, period)

        factors["water_temp"] = (water_temp_scores or {}).get(
            day.isoformat()
        )

        score = combine_scores(factors)

        if score is not None:
            days.append({
                "date": day.isoformat(), "score": score, "factors": factors,
                "inputs": {
                    "wind": wind_mph_from_period(period),
                    "sky": sky_pct_from_text(period.get("shortForecast")),
                    "precipitation": (period.get("probabilityOfPrecipitation") or {}).get("value"),
                    "season": start.month,
                    "moon": moon.phase(start.date()),
                    "pressure": None,
                    "water_temp": None,
                },
                "forecast_time": start.isoformat(),
            })
    return days


def explain_day(day: dict) -> dict:
    """Describe the exact inputs and available weights used for this daily score."""
    factors = day["factors"]
    inputs = day["inputs"]
    total_weight = sum(WEIGHTS[key] for key, value in factors.items() if value is not None)
    explanations = {}

    for key, score in factors.items():
        if score is None:
            explanations[key] = "Data unavailable; excluded from the overall score."
            continue

        value = inputs.get(key)
        weight = round(100 * WEIGHTS[key] / total_weight)
        if key == "wind":
            detail = f"Forecast wind: {value:g} mph" if value is not None else "Wind forecast"
        elif key == "sky":
            detail = f"About {value:g}% cloud cover, inferred from the forecast description" if value is not None else "Sky forecast"
        elif key == "precipitation":
            detail = f"Forecast chance of rain: {value:g}%" if value is not None else "Precipitation forecast"
        elif key == "pressure":
            detail = f"Pressure changed {value:+.2f} hPa over approximately 3 hours at the nearby station" if value is not None else "Pressure trend"
        elif key == "water_temp":
            detail = f"Estimated water temperature: {value:.1f}°C" if value is not None else "Estimated water temperature"
        elif key == "season":
            detail = f"Month: {datetime(2000, value, 1):%B}" if value is not None else "Seasonal estimate"
        else:
            detail = "Lunar phase estimate"

        explanations[key] = f"{detail}. Factor score: {score}/100; share of available weighting: {weight}%."

    ranked = sorted(
        (key for key, value in factors.items() if value is not None),
        key=lambda key: factors[key] * WEIGHTS[key], reverse=True,
    )
    leaders = " and ".join(FACTOR_LABELS[key].lower() for key in ranked[:2])
    time = datetime.fromisoformat(day["forecast_time"])
    forecast_hour = time.strftime("%I:%M %p").lstrip("0")
    summary = f"{leaders.capitalize()} contributed most to this {day['score']/10:.1f}/10 estimate, based on a forecast near {forecast_hour}."
    if factors["pressure"] is None:
        summary += " Pressure trend was unavailable and excluded."
    if inputs.get("water_temp") is not None:
        summary += " Water temperature is estimated from air temperatures."
    return {"summary": summary, "factors": explanations}
