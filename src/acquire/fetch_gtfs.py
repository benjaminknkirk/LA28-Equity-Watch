"""
DATA DICTIONARY — LA Metro GTFS stops (bus + rail)

Sources (evergreen GitLab raw archives from LACMTA):
  Bus:  https://gitlab.com/LACMTA/gtfs_bus/-/raw/master/gtfs_bus.zip
  Rail: https://gitlab.com/LACMTA/gtfs_rail/-/raw/master/gtfs_rail.zip
Attribution: provided by LA Metro (http://developer.metro.net)

Columns kept in data/processed/metro_stops.csv:
  stop_id       — GTFS stop_id (prefixed with agency feed: bus_ / rail_)
  stop_name     — Stop name
  stop_lat      — Latitude (WGS84)
  stop_lon      — Longitude (WGS84)
  feed          — 'bus' or 'rail'
  location_type — GTFS location_type when present

Also writes data/processed/metro_stops.geojson (points).

Notes:
  - This is the *current* network baseline, not the planned Twenty-Eight by '28 set.
  - Stops are clipped loosely to LA County bounding box to drop out-of-area outliers.
"""
from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Point

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import DATA_PROCESSED, DATA_RAW, ensure_dirs  # noqa: E402

FEEDS = {
    "bus": "https://gitlab.com/LACMTA/gtfs_bus/-/raw/master/gtfs_bus.zip",
    "rail": "https://gitlab.com/LACMTA/gtfs_rail/-/raw/master/gtfs_rail.zip",
}

# Approximate LA County bbox (WGS84)
BBOX = (-119.0, 32.7, -117.4, 34.9)


def download_zip(url: str, dest: Path) -> Path:
    print(f"  downloading {url}")
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest


def read_stops(zip_path: Path, feed: str) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as zf:
        name = "stops.txt"
        if name not in zf.namelist():
            raise FileNotFoundError(f"stops.txt missing in {zip_path}")
        with zf.open(name) as f:
            df = pd.read_csv(io.TextIOWrapper(f, encoding="utf-8-sig"))
    keep = [c for c in ["stop_id", "stop_name", "stop_lat", "stop_lon", "location_type"] if c in df.columns]
    df = df[keep].copy()
    df["feed"] = feed
    df["stop_id"] = feed + "_" + df["stop_id"].astype(str)
    df["stop_lat"] = pd.to_numeric(df["stop_lat"], errors="coerce")
    df["stop_lon"] = pd.to_numeric(df["stop_lon"], errors="coerce")
    df = df.dropna(subset=["stop_lat", "stop_lon"])
    # Prefer station/stop nodes; keep all non-null coords
    west, south, east, north = BBOX
    df = df[
        (df["stop_lon"] >= west)
        & (df["stop_lon"] <= east)
        & (df["stop_lat"] >= south)
        & (df["stop_lat"] <= north)
    ]
    return df


def main() -> None:
    ensure_dirs(DATA_RAW / "gtfs", DATA_PROCESSED)
    frames = []
    for feed, url in FEEDS.items():
        dest = DATA_RAW / "gtfs" / f"gtfs_{feed}.zip"
        download_zip(url, dest)
        frames.append(read_stops(dest, feed))

    stops = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["stop_id"])
    out_csv = DATA_PROCESSED / "metro_stops.csv"
    stops.to_csv(out_csv, index=False)

    gdf = gpd.GeoDataFrame(
        stops,
        geometry=[Point(xy) for xy in zip(stops["stop_lon"], stops["stop_lat"])],
        crs="EPSG:4326",
    )
    out_geo = DATA_PROCESSED / "metro_stops.geojson"
    gdf.to_file(out_geo, driver="GeoJSON")
    print(f"stops: {len(stops)} (bus={sum(stops.feed=='bus')}, rail={sum(stops.feed=='rail')})")
    print(f"  → {out_csv}")
    print(f"  → {out_geo}")


if __name__ == "__main__":
    main()
