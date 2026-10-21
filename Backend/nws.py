
import httpx

from spots import SPOTS
from datetime import datetime, timedelta, timezone

NWS_HEADERS = {
    "User-Agent": "CSUNFreshwaterFishing/0.1",
    "Accept": "application/geo+json",
}

# Function to retrieve recent observations from a specific station
def get_recent_observations(station_id: str, hours: int = 12) -> list[dict]:
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

def extract_pressure_readings(observations: list[dict]) -> list[dict]:
    readings = []

    for observation in observations:
        details = observation["properties"]
        pressure = details.get("barometricPressure") or {}

        if pressure.get("value") is None:
            continue

        readings.append({
            "timestamp": details["timestamp"],
            "value": pressure["value"],
            "unitCode": pressure.get("unitCode"),
        })

    return sorted(readings, key=lambda reading: reading["timestamp"])

# Function to get pressure data for a specific spot
def get_pressure_data_for_spot(spot: dict) -> dict:
    station = {
        "id": spot["station_id"],
        "name": spot["station_name"],
        "latitude": spot["station_latitude"],
        "longitude": spot["station_longitude"],
    }

    observations = get_recent_observations(station["id"])
    readings = extract_pressure_readings(observations)

    return {
        "status": "ok" if len(readings) >= 3 else "pressure_unavailable",
        "spot": spot,
        "station": station,
        "pressureField": "barometricPressure",
        "readings": readings,
    }

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
        print(get_hourly_forecast(spot))
