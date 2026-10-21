import httpx

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