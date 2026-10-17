import httpx

from spots import SPOTS
from datetime import datetime, timedelta, timezone

NWS_HEADERS = {
    "User-Agent": "CSUNFreshwaterFishing/0.1",
    "Accept": "application/geo+json",
}

# Function to retrieve point data from the NWS API
def get_point_data(latitude: float, longitude: float) -> dict:
    url = f"https://api.weather.gov/points/{latitude:.4f},{longitude:.4f}"

    response = httpx.get(url, headers=NWS_HEADERS, timeout=15.0)
    response.raise_for_status()
    return response.json()


# Function to retrieve observation stations from the NWS API
def get_observation_stations(stations_url: str) -> list[dict]:
    response = httpx.get(stations_url, headers=NWS_HEADERS, timeout=15.0)
    response.raise_for_status()
    return response.json()["features"]

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

def get_pressure_data_for_spot(spot: dict) -> dict:
    point_data = get_point_data(spot["latitude"], spot["longitude"])
    stations_url = point_data["properties"]["observationStations"]
    stations = get_observation_stations(stations_url)

    for station in stations[:3]:
        station_details = station["properties"]
        station_id = station_details["stationIdentifier"]

        try:
            observations = get_recent_observations(station_id)
        except httpx.HTTPError:
            continue

        readings = extract_pressure_readings(observations)

        if len(readings) < 3:
            continue

        station_longitude, station_latitude = station["geometry"]["coordinates"][:2]

        return {
            "status": "ok",
            "spot": spot,
            "station": {
                "id": station_id,
                "name": station_details["name"],
                "latitude": station_latitude,
                "longitude": station_longitude,
            },
            "pressureField": "barometricPressure",
            "readings": readings,
        }

    return {
        "status": "pressure_unavailable",
        "spot": spot,
        "station": None,
        "pressureField": "barometricPressure",
        "readings": [],
    }

# Main execution block to demonstrate the usage of the functions
if __name__ == "__main__":
    for spot in SPOTS:
        result = get_pressure_data_for_spot(spot)

        print(
            result["spot"]["name"],
            "| status:", result["status"],
            "| station:", result["station"]["id"] if result["station"] else None,
            "| readings:", len(result["readings"]),
        )