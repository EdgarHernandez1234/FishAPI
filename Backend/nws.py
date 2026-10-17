import httpx

from spots import SPOTS


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