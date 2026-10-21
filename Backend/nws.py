import httpx

from spots import SPOTS
from datetime import datetime, timedelta, timezone

NWS_HEADERS = {
    "User-Agent": "CSUNFreshwaterFishing/0.1",
    "Accept": "application/geo+json",
}
def average_pressure_hpa(readings: list[dict]) -> float | None:
    values = [reading["value"] for reading in readings]
    return round(sum(values) / len(values), 2) if values else None

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
        details = observation["properties"]
        pressure = details.get("barometricPressure") or {}

        if pressure.get("value") is None:
            continue

        readings.append({
            "timestamp": details["timestamp"],
            "value": pressure["value"] / 100,  # Convert from Pa to hPa
            "unitCode": "wmoUnit:hPa",
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
    wind_readings = extract_wind_readings(observations)
    return {
        "status": "ok" if len(readings) >= 3 else "pressure_unavailable",
        "spot": spot,
        "station": station,
        "pressureField": "barometricPressure",
        "readings": readings,
        "windReadings": wind_readings,
        "averagePressureHpa": average_pressure_hpa(readings),
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