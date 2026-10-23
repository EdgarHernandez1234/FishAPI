
import httpx

from spots import SPOTS
from datetime import datetime, timedelta, timezone

NWS_HEADERS = {
    "User-Agent": "CSUNFreshwaterFishing/0.1",
    "Accept": "application/geo+json",
}
# Function to retrieve recent observations from a specific station
def get_recent_observations(station_id: str, hours: int = 3) -> list[dict]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)
    url = f"https://api.weather.gov/stations/{station_id}/observations"

    response = httpx.get(
        url,
        headers=NWS_HEADERS,
        params={"start": start.isoformat(), "end": end.isoformat()},
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json()["features"]

def average_pressure_hpa(readings: list[dict]) -> float | None:
    if not readings:
        return None

    return round(
        sum(reading["value"] for reading in readings) / len(readings),
        2,
    )

def extract_wind_readings(observations):
    readings = []

    for observation in observations:
        data = observation.get("properties", observation)
        speed = data.get("windSpeed") or {}

        if speed.get("value") is None:
            continue

        readings.append({
            "timestamp": data["timestamp"],
            "windSpeed": speed,
            "windDirection": data.get("windDirection"),
            "windGust": data.get("windGust"),
        })

    readings.sort(key=lambda reading: reading["timestamp"])
    return readings

def extract_pressure_readings(observations: list[dict]) -> list[dict]:
    readings = []

    for observation in observations:
        props = observation.get("properties", {})
        pressure = props.get("barometricPressure") or {}
        value = pressure.get("value")

        if value is None:
            continue

        unit_code = pressure.get("unitCode", "")

        # NWS commonly reports barometric pressure in pascals.
        if unit_code.endswith(":Pa") or unit_code == "Pa":
            value_hpa = float(value) / 100
        elif unit_code.endswith(":hPa") or unit_code == "hPa":
            value_hpa = float(value)
        else:
            # Do not guess if the API reports an unexpected unit.
            continue

        timestamp = props.get("timestamp")
        if not timestamp:
            continue

        readings.append({
            "timestamp": timestamp,
            "value": value_hpa,
            "unitCode": "wmoUnit:hPa",
        })

    return sorted(readings, key=lambda r: r["timestamp"])


def get_pressure_data_for_spot(spot: dict) -> dict:
    station = {
        "id": spot["station_id"],
        "name": spot["station_name"],
        "latitude": spot["station_latitude"],
        "longitude": spot["station_longitude"],
    }

    observations = get_recent_observations(station["id"], hours=12)
    readings = extract_pressure_readings(observations)
    wind_readings = extract_wind_readings(observations)
    # Keep the public average limited to the most recent three hours.
    average_readings = []
    if readings:
        latest_time = datetime.fromisoformat(
            readings[-1]["timestamp"].replace("Z", "+00:00")
        )
        cutoff = latest_time - timedelta(hours=3)
        average_readings = [
            reading for reading in readings
            if datetime.fromisoformat(
                reading["timestamp"].replace("Z", "+00:00")
            ) >= cutoff
        ]

    result = {
        "status": "ok" if len(readings) >= 3 else "pressure_unavailable",
        "spot": spot,
        "station": station,
        "pressureField": "barometricPressure",
        "pressure_hpa": None,
        "pressure_3h_ago_hpa": None,
        "change_hpa_3h": None,
        "readings": readings,
        "windReadings": wind_readings,
        "averagePressureHpa": average_pressure_hpa(average_readings),
    }
    

    if len(readings) < 2:
        return result

    # Use the latest available observation as the current reference.
    current = readings[-1]
    current_time = datetime.fromisoformat(
        current["timestamp"].replace("Z", "+00:00")
    )

    target_time = current_time - timedelta(hours=3)

    # Find the reading closest to three hours before the latest reading.
    previous = min(
        readings[:-1],
        key=lambda r: abs(
            datetime.fromisoformat(
                r["timestamp"].replace("Z", "+00:00")
            ) - target_time
        ),
    )

    previous_time = datetime.fromisoformat(
        previous["timestamp"].replace("Z", "+00:00")
    )

    # Reject comparisons that are too far from the desired three-hour interval.
    if abs(previous_time - target_time) > timedelta(minutes=90):
        return result

    current_hpa = current["value"]
    previous_hpa = previous["value"]

    result.update({
        "pressure_hpa": round(current_hpa, 2),
        "pressure_3h_ago_hpa": round(previous_hpa, 2),
        "change_hpa_3h": round(current_hpa - previous_hpa, 2),
    })

    return result


# Function to discover nearby weather stations based on latitude and longitude
def discover_station_candidates(latitude: float, longitude: float) -> list[dict]:
    point_url = f"https://api.weather.gov/points/{latitude:.4f},{longitude:.4f}"

    point_response = httpx.get(
        point_url, headers=NWS_HEADERS, timeout=15.0
    )
    point_response.raise_for_status()

    stations_url = point_response.json()["properties"]["observationStations"]

    stations_response = httpx.get(
        stations_url, headers=NWS_HEADERS, timeout=15.0
    )
    stations_response.raise_for_status()

    candidates = []
    for feature in stations_response.json()["features"][:5]:
        properties = feature["properties"]
        station_longitude, station_latitude = feature["geometry"]["coordinates"][:2]

        candidates.append({
            "id": properties["stationIdentifier"],
            "name": properties["name"],
            "latitude": station_latitude,
            "longitude": station_longitude,
        })

    return candidates

CLOUD_PCT = {"CLR": 0, "SKC": 0, "FEW": 18, "SCT": 40, "BKN": 75, "OVC": 100}


def _first_value(observations, getter):
    """Return the first non-None value from newest to oldest."""
    for obs in observations:
        value = getter(obs["properties"])
        if value is not None:
            return value
    return None


def _sky_pct(props):
    layers = props.get("cloudLayers") or []
    if not layers:
        return None
    return max(CLOUD_PCT.get(layer["amount"], 0) for layer in layers)

def get_hourly_forecast(spot: dict) -> list[dict]:
    lat = round(spot["latitude"], 4)
    lon = round(spot["longitude"], 4)

    point = httpx.get(
        f"https://api.weather.gov/points/{lat},{lon}",
        headers=NWS_HEADERS,
        timeout=15.0,
        follow_redirects=True,
    )
    point.raise_for_status()
    hourly_url = point.json()["properties"]["forecastHourly"]

    forecast = httpx.get(
        hourly_url,
        headers=NWS_HEADERS,
        timeout=15.0,
        follow_redirects=True,
    )
    forecast.raise_for_status()
    return forecast.json()["properties"]["periods"]

def precip_chance_now(periods: list[dict], now: datetime | None = None) -> int | None:
    """Return the chance of precipitation (0-100) for the hour containing `now`.

    periods: the list returned by get_hourly_forecast(spot).
    now: a timezone-aware datetime. Defaults to the current time.
    Returns None if no period matches or the forecast has no value.
    """
    now = now or datetime.now(timezone.utc)

    for period in periods:
        start = datetime.fromisoformat(period["startTime"])
        end = datetime.fromisoformat(period["endTime"])
        if start <= now < end:
            return period["probabilityOfPrecipitation"]["value"]

    return None



def extract_wind(observations: list[dict]) -> dict:
    wind_kmh = _first_value(observations, lambda p: p["windSpeed"]["value"])

    return {
        "wind_mph": None if wind_kmh is None else wind_kmh * 0.621371,
    }

def get_wind_for_spot(spot: dict) -> dict:
    observations = get_recent_observations(spot["station_id"])
    return extract_wind(observations)


# Main execution block to demonstrate the usage of the functions
if __name__ == "__main__":
    for spot in SPOTS:
        result = get_pressure_data_for_spot(spot)
        average = average_pressure_hpa(result["readings"])

        print(
            result["spot"]["name"],
            "| status:", result["status"],
            "| station:", result["station"]["id"] if result["station"] else None,
            "| readings:", len(result["readings"]),
            "| 3-hour average:", average, "hPa",
        )
        print(get_hourly_forecast(spot))