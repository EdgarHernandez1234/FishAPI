import httpx
from math import asin, cos, radians, sin, sqrt
CITIES_URL = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/"
    "TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/11/query"
)

def get_california_cities() -> list[dict]:
    response = httpx.get(
        CITIES_URL,
        params={
            "where": "STATE='06'",  # California
            "outFields": "GEOID,BASENAME,CENTLAT,CENTLON",
            "returnGeometry": "false",
            "f": "json",
        },
        timeout=20.0,
    )
    response.raise_for_status()
    data = response.json()

    if "error" in data:
        raise RuntimeError(f"Census query failed: {data['error']}")
    if data.get("exceededTransferLimit"):
        raise RuntimeError("Census returned an incomplete city list")

    return [feature["attributes"] for feature in data["features"]]

CITY_SEARCH_AREAS = {
    "los-angeles": {
        "name": "Los Angeles / CSUN area",
        "latitude": 34.2389,
        "longitude": -118.5293,
        "radius_miles": 30,
    },
    "san-francisco": {
        "name": "San Francisco",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "radius_miles": 15,
    },
    "sacramento": {
        "name": "Sacramento",
        "latitude": 38.5816,
        "longitude": -121.4944,
        "radius_miles": 20,
    },
}
def distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))

    a = (
        sin((lat2 - lat1) / 2) ** 2
        + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    )
    return 3958.8 * 2 * asin(min(1.0, sqrt(a)))


def candidate_waters_near_city(
    city: dict, candidates: list[dict], radius_miles: float = 25.0
) -> list[dict]:
    nearby = []

    for water in candidates:
        if water.get("latitude") is None or water.get("longitude") is None:
            continue

        distance = distance_miles(
            float(city["CENTLAT"]),
            float(city["CENTLON"]),
            float(water["latitude"]),
            float(water["longitude"]),
        )

        if distance <= radius_miles:
            nearby.append({**water, "distance_miles": round(distance, 1)})

    return sorted(nearby, key=lambda water: water["distance_miles"])


if __name__ == "__main__":
    cities = get_california_cities()
    print("California cities returned:", len(cities))

    cities_by_name = {city["BASENAME"]: city for city in cities}

    for name in ("Los Angeles", "San Francisco", "Sacramento"):
        city = cities_by_name.get(name)

        if city is None:
            raise RuntimeError(f"Expected city missing: {name}")

        print(
            city["BASENAME"],
            "| GEOID:", city["GEOID"],
            "| coordinates:", city["CENTLAT"], city["CENTLON"],
        )