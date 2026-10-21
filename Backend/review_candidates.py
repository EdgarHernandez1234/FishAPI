from cdfw import get_all_planting_locations, extract_candidate_waters
from cities import get_california_cities, candidate_waters_near_city
import httpx

from cities import distance_miles
from nws import (
    get_recent_observations,
    extract_pressure_readings,
    extract_wind_readings,
)

ACCESS_SOURCES = {
    "Alondra Park Lake": "https://parks.lacounty.gov/frequently-asked-questions/",
    "Belvedere Lake": "https://parks.lacounty.gov/frequently-asked-questions/",
    "Legg Lakes": "https://parks.lacounty.gov/frequently-asked-questions/",
    "Mather Lake": (
        "https://regionalparks.saccounty.gov/us/en/parks/"
        "open-spaces/mather-regional-park.html"
    ),
}
def check_nearby_stations(water: dict, station_limit: int = 3) -> None:
    latitude = float(water["latitude"])
    longitude = float(water["longitude"])
    headers = {"User-Agent": "CSUNFreshwaterFishingHackathon/0.1"}

    points_response = httpx.get(
        f"https://api.weather.gov/points/{latitude},{longitude}",
        headers=headers,
        timeout=15.0,
        follow_redirects=True,
    )
    points_response.raise_for_status()

    stations_url = points_response.json()["properties"]["observationStations"]

    stations_response = httpx.get(
        stations_url,
        headers=headers,
        timeout=15.0,
        follow_redirects=True,
    )
    stations_response.raise_for_status()

    stations = []
    for feature in stations_response.json()["features"]:
        properties = feature.get("properties") or {}
        coordinates = (feature.get("geometry") or {}).get("coordinates") or []
        station_id = properties.get("stationIdentifier")

        if not station_id or len(coordinates) < 2:
            continue

        station_lon, station_lat = coordinates[:2]
        stations.append({
            "id": station_id,
            "name": properties.get("name", ""),
            "distance": distance_miles(
                latitude, longitude, station_lat, station_lon
            ),
        })

    stations.sort(key=lambda station: station["distance"])

    for station in stations[:station_limit]:
        try:
            observations = get_recent_observations(station["id"])
            pressure = extract_pressure_readings(observations)
            wind = extract_wind_readings(observations)
        except httpx.HTTPError as exc:
            print(" ", station["id"], "| NWS request failed:", exc)
            continue

        latest_pressure = max(
            (reading["timestamp"] for reading in pressure),
            default=None,
        )

        print(
            " ", station["id"],
            "|", station["name"],
            "| miles:", round(station["distance"], 1),
            "| pressure:", len(pressure),
            "| wind:", len(wind),
            "| latest pressure:", latest_pressure,
        )


if __name__ == "__main__":
    candidates = extract_candidate_waters(get_all_planting_locations())
    cities = {
        city["BASENAME"]: city
        for city in get_california_cities()
    }

    for city_name in ("Los Angeles", "Sacramento"):
        print(f"\n{city_name}:")
        nearby = candidate_waters_near_city(cities[city_name], candidates)

        for water in nearby:
            if water["name"] not in ACCESS_SOURCES:
                continue

            print(
                water["name"],
                "| coordinates:", water["latitude"], water["longitude"],
                "| miles:", water["distance_miles"],
                "| access source:", ACCESS_SOURCES[water["name"]],
            )

            station_limit = (
                10
                if water["name"] in {"Belvedere Lake", "Legg Lakes"}
                else 3
            )
            check_nearby_stations(water, station_limit=station_limit)
            
if __name__ == "__main__":
    candidates = extract_candidate_waters(get_all_planting_locations())
    cities = {
        city["BASENAME"]: city
        for city in get_california_cities()
    }

    for city_name in ("Los Angeles", "Sacramento"):
        print(f"\n{city_name}:")

        nearby = candidate_waters_near_city(cities[city_name], candidates)

        for water in nearby:
            if water["name"] not in ACCESS_SOURCES:
                continue

            print(
                water["name"],
                "| coordinates:", water["latitude"], water["longitude"],
                "| miles:", water["distance_miles"],
                "| access source:", ACCESS_SOURCES[water["name"]],
            )

            check_nearby_stations(water)