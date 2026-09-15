"""
Build curated LA28 venue points and Metro Twenty-Eight by '28 investment points.

DATA DICTIONARY — data/processed/la28_venues.csv
  venue_id, name, zone, city, state, latitude, longitude,
  in_la_county, geocode_query, source, coord_method, notes

DATA DICTIONARY — data/processed/metro_28x28.csv
  project_id, name, status, category, latitude, longitude,
  geocode_query, source, coord_method, notes

Both datasets are MANUALLY CURATED. Coordinates come from Nominatim/OpenStreetMap
geocoding of documented queries, with a small set of verified landmark fallbacks.
This is not an official LA28 or Metro GIS product — see METHODOLOGY.md.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Point

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import DATA_CURATED, DATA_PROCESSED, DATA_RAW, ensure_dirs, load_dotenv  # noqa: E402

NOMINATIM = "https://nominatim.openstreetmap.org/search"
UA = "LA28-Equity-Watch/0.1 (academic research; contact: benjaminknkirk@gmail.com)"

# Verified landmark fallbacks (WGS84) used only if Nominatim fails.
# Sourced from well-known public coordinates (OSM / venue websites); QA in notes.
LANDMARK_FALLBACKS = {
    "Los Angeles Memorial Coliseum": (34.0141, -118.2879),
    "SoFi Stadium": (33.9535, -118.3392),
    "Crypto.com Arena": (34.0430, -118.2673),
    "Dodger Stadium": (34.0739, -118.2400),
    "Rose Bowl": (34.1613, -118.1676),
    "Intuit Dome": (33.9447, -118.3426),
    "Dignity Health Sports Park": (33.8644, -118.2611),
    "BMO Stadium": (34.0129, -118.2841),
    "Honda Center": (33.8078, -117.8765),
    "UCLA": (34.0689, -118.4452),
    "Union Station Los Angeles": (34.0561, -118.2342),
    "7th Street/Metro Center": (34.0486, -118.2587),
}


def geocode(query: str, cache: dict) -> tuple[float, float, str] | None:
    if query in cache:
        return cache[query]
    r = requests.get(
        NOMINATIM,
        params={"q": query, "format": "json", "limit": 1},
        headers={"User-Agent": UA},
        timeout=60,
    )
    time.sleep(1.1)  # Nominatim usage policy
    if r.status_code != 200:
        cache[query] = None
        return None
    data = r.json()
    if not data:
        cache[query] = None
        return None
    lat, lon = float(data[0]["lat"]), float(data[0]["lon"])
    cache[query] = (lat, lon, data[0].get("display_name", ""))
    return cache[query]


def resolve_coords(name: str, query: str, cache: dict) -> tuple[float, float, str, str]:
    hit = geocode(query, cache)
    if hit:
        return hit[0], hit[1], "nominatim", hit[2]
    if name in LANDMARK_FALLBACKS:
        lat, lon = LANDMARK_FALLBACKS[name]
        return lat, lon, "landmark_fallback", name
    for alt in (
        f"{name}, Los Angeles County, California",
        f"{name}, Los Angeles, CA",
        query.split(",")[0] + ", Los Angeles, CA",
    ):
        hit = geocode(alt, cache)
        if hit:
            return hit[0], hit[1], "nominatim_fallback", hit[2]
    raise RuntimeError(f"Could not geocode: {name} / {query}")


def build_venues(cache: dict) -> pd.DataFrame:
    seed = pd.read_csv(DATA_CURATED / "la28_venues_seed.csv")
    rows = []
    for _, s in seed.iterrows():
        lat, lon, method, detail = resolve_coords(s["name"], s["geocode_query"], cache)
        rows.append(
            {
                **s.to_dict(),
                "latitude": lat,
                "longitude": lon,
                "coord_method": method,
                "geocode_detail": detail,
            }
        )
        print(f"  venue {s['venue_id']}: {s['name']} → {lat:.5f},{lon:.5f} ({method})")
    return pd.DataFrame(rows)


def build_28x28(cache: dict) -> pd.DataFrame:
    seed = pd.read_csv(DATA_CURATED / "metro_28x28_seed.csv")
    rows = []
    for _, s in seed.iterrows():
        if pd.notna(s.get("latitude")) and pd.notna(s.get("longitude")):
            lat, lon = float(s["latitude"]), float(s["longitude"])
            method, detail = "seed_curated", "coordinates supplied in seed CSV"
        else:
            lat, lon, method, detail = resolve_coords(s["name"], s["geocode_query"], cache)
        row = s.to_dict()
        row.update(
            {
                "latitude": lat,
                "longitude": lon,
                "coord_method": method,
                "geocode_detail": detail,
            }
        )
        rows.append(row)
        print(f"  project {s['project_id']}: {s['name'][:50]} → {lat:.5f},{lon:.5f} ({method})")
    return pd.DataFrame(rows)


def to_geojson(df: pd.DataFrame, path: Path) -> None:
    gdf = gpd.GeoDataFrame(
        df,
        geometry=[Point(xy) for xy in zip(df["longitude"], df["latitude"])],
        crs="EPSG:4326",
    )
    gdf.to_file(path, driver="GeoJSON")


def main() -> None:
    load_dotenv()
    ensure_dirs(DATA_CURATED, DATA_PROCESSED, DATA_RAW / "curated")
    cache_path = DATA_RAW / "curated" / "geocode_cache.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}

    print("Building LA28 venues…")
    venues = build_venues(cache)
    venues_out = DATA_PROCESSED / "la28_venues.csv"
    venues.to_csv(venues_out, index=False)
    to_geojson(venues, DATA_PROCESSED / "la28_venues.geojson")
    print(f"  → {venues_out} ({len(venues)} rows)")

    print("Building Metro 28x28 points…")
    projects = build_28x28(cache)
    proj_out = DATA_PROCESSED / "metro_28x28.csv"
    projects.to_csv(proj_out, index=False)
    to_geojson(projects, DATA_PROCESSED / "metro_28x28.geojson")
    print(f"  → {proj_out} ({len(projects)} rows)")

    cache_path.write_text(json.dumps({k: v for k, v in cache.items() if v}, indent=2))


if __name__ == "__main__":
    main()
