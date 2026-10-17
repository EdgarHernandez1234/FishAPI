import httpx

from spots import SPOTS

# Constants for CSUN's latitude and longitude, and the maximum distance in miles
def get_point_data(latitude: float, longitude: float) -> dict:
    url = f"https://api.weather.gov/points/{latitude:.4f},{longitude:.4f}"

    response = httpx.get(
        url,
        headers={
            "User-Agent": "CSUNFreshwaterFishing/0.1",
            "Accept": "application/geo+json",
        },
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json()

# Example usage
if __name__ == "__main__":
    spot = SPOTS[0]  # Lake Balboa
    data = get_point_data(spot["latitude"], spot["longitude"])
    properties = data["properties"]

    print("Spot:", spot["name"])
    print("NWS forecast grid:", properties.get("gridId"),
          properties.get("gridX"), properties.get("gridY"))
    print("Observation stations URL:", properties.get("observationStations"))