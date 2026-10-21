import httpx
from spots import CSUN_LATITUDE, CSUN_LONGITUDE, MAX_DISTANCE_MILES
import json
from pathlib import Path
from cities import CITY_SEARCH_AREAS
CDFW_PLANTING_URL = (
    "https://services2.arcgis.com/Uq9r85Potqm3MfRV/arcgis/rest/services/"
    "biosds2897_fmu/FeatureServer/0/query"
)

def extract_candidate_waters(features: list[dict]) -> list[dict]:
    unique_waters = {}

    for feature in features:
        details = feature["attributes"]
        name = details.get("WaterName")
        latitude = details.get("Lat")
        longitude = details.get("Lon")

        if not name or latitude is None or longitude is None:
            continue

        key = (name.strip().casefold(), latitude, longitude)
        unique_waters.setdefault(key, {
            "name": name,
            "latitude": latitude,
            "longitude": longitude,
            "county": details.get("Counties"),
        })

    return list(unique_waters.values())

def get_sample_planting_locations(city: dict) -> list[dict]:
    params = {
        "where": "1=1",
        "geometry": f"{city['longitude']},{city['latitude']}",
        "geometryType": "esriGeometryPoint",
        "inSR": 4326,
        "distance": city["radius_miles"],
        "units": "esriSRUnit_StatuteMile",
        "outFields": "WaterName,Lat,Lon,FishType,Counties,DfwWaterId",
        "returnGeometry": "false",
        "resultRecordCount": 2000,
        "f": "json",
    }

    response = httpx.get(CDFW_PLANTING_URL, params=params, timeout=15.0)
    response.raise_for_status()
    data = response.json()

    if "error" in data:
        raise RuntimeError(f"CDFW query failed: {data['error']}")
    if data.get("exceededTransferLimit"):
        raise RuntimeError("CDFW returned more records than fit in one response")

    return data["features"]

def get_approved_cdfw_spots(candidates):
    approved_stations = {
        "rancho simi park lake": {
            "id": "rancho-simi-park-lake",
            "station_id": "SV",
            "station_name": "Simi Valley - Cochran",
            "station_latitude": 34.2764,
            "station_longitude": -118.68375,
        },
        "kenneth hahn lake": {
            "id": "kenneth-hahn-lake",
            "station_id": "KSMO",
            "station_name": "Santa Monica, Santa Monica Municipal Airport",
            "station_latitude": 34.01583,
            "station_longitude": -118.45139,
        },
        "merced lake north": {
            "id": "merced-lake-north",
            "station_id": "KSFO",
            "station_name": "San Francisco, San Francisco International Airport",
            "station_latitude": 37.61961,
            "station_longitude": -122.36558,
        },
        "southside park pond": {
            "id": "southside-park-pond",
            "station_id": "KSAC",
            "station_name": "Sacramento Executive Airport",
            "station_latitude": 38.50674,
            "station_longitude": -121.49597,
        },
    }

    approved = []

    for candidate in candidates:
        station = approved_stations.get(candidate["name"].strip().casefold())
        if station is None:
            continue

        approved.append({
            "id": station["id"],
            "name": candidate["name"],
            "latitude": candidate["latitude"],
            "longitude": candidate["longitude"],
            "station_id": station["station_id"],
            "station_name": station["station_name"],
            "station_latitude": station["station_latitude"],
            "station_longitude": station["station_longitude"],
            "source": "CDFW Planting Locations",
        })

    return approved
if __name__ == "__main__":
    all_features = []

    for city_id in ("los-angeles", "san-francisco", "sacramento"):
        city = CITY_SEARCH_AREAS[city_id]
        features = get_sample_planting_locations(city)
        all_features.extend(features)
        print(f"{city['name']}: {len(features)} planting records")

    candidates = extract_candidate_waters(all_features)
    print("Distinct candidate waters:", len(candidates))

    for water in candidates:
        print(
            water["name"],
            "| county:", water["county"],
            "| coordinates:", water["latitude"], water["longitude"],
        )

    approved_spots = get_approved_cdfw_spots(candidates)
    print("Approved CDFW spots:", approved_spots)

    expected_ids = {
        "rancho-simi-park-lake",
        "kenneth-hahn-lake",
        "merced-lake-north",
        "southside-park-pond",
    }
    found_ids = {spot["id"] for spot in approved_spots}
    missing_ids = expected_ids - found_ids

    if missing_ids:
        raise RuntimeError(
            f"Approved spots missing from CDFW results: {sorted(missing_ids)}; "
            "saved file was not changed"
        )

    output_path = Path(__file__).with_name("cdfw_approved_spots.json")
    output_path.write_text(
        json.dumps(approved_spots, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Saved approved spots to:", output_path)