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

# Main execution block to demonstrate the usage of the functions
if __name__ == "__main__":
    spot = SPOTS[0]  # Lake Balboa
    point_data = get_point_data(spot["latitude"], spot["longitude"])
    stations_url = point_data["properties"]["observationStations"]
    stations = get_observation_stations(stations_url)

    print("Spot:", spot["name"])
    print("Candidate stations:", len(stations))

    for station in stations[:5]:
        details = station["properties"]
        coordinates = station["geometry"]["coordinates"]
        print(details["stationIdentifier"], "|", details["name"], "|", coordinates)
        station_id = stations[0]["properties"]["stationIdentifier"]
    observations = get_recent_observations(station_id)

    print("Checking pressure at station:", station_id)
    print("Observations returned:", len(observations))

    for observation in observations[:10]:
        details = observation["properties"]
        pressure = details.get("barometricPressure") or {}

        print(
            details.get("timestamp"),
            "| pressure:",
            pressure.get("value"),
            pressure.get("unitCode"),
        )
    readings = extract_pressure_readings(observations)
    print("Usable pressure readings:", len(readings))
    print("Earliest:", readings[0] if readings else None)
    print("Latest:", readings[-1] if readings else None)