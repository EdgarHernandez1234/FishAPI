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
    for spot in SPOTS:  # Lake Balboa and Hansen Dam
        point_data = get_point_data(spot["latitude"], spot["longitude"])
        stations_url = point_data["properties"]["observationStations"]
        stations = get_observation_stations(stations_url)

        print("\nSpot:", spot["name"])
        print("Candidate stations:", len(stations))

        if not stations:
            print("No observation stations found.")
            continue

        station = stations[0]
        station_id = station["properties"]["stationIdentifier"]
        print("Checking station:", station_id, "-", station["properties"]["name"])

        observations = get_recent_observations(station_id)
        readings = extract_pressure_readings(observations)

        print("Observations returned:", len(observations))
        print("Usable pressure readings:", len(readings))
        print("Earliest:", readings[0] if readings else None)
        print("Latest:", readings[-1] if readings else None)