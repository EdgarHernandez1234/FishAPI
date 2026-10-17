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