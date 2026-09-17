"""
DATA DICTIONARY — TIGER/Line 2010 census tracts (Los Angeles County)

Source: U.S. Census Bureau TIGER/Line Shapefiles 2010
URL: https://www2.census.gov/geo/tiger/TIGER2010/TRACT/2010/tl_2010_06037_tract10.zip

Columns kept in data/processed/tracts_la_2010.geojson / .parquet:
  geoid10   — GEOID10 (11-digit)
  tractce10 — Tract code
  aland10   — Land area (sq meters)
  awater10  — Water area (sq meters)
  geometry  — Polygon (WGS84 in GeoJSON; analysis uses EPSG:3310)

Notes:
  - 2010 vintage matches CalEnviroScreen 4.0 and HPI 3.0 tract definitions.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import DATA_PROCESSED, DATA_RAW, ensure_dirs, zfill_geoid10  # noqa: E402

URL = "https://www2.census.gov/geo/tiger/TIGER2010/TRACT/2010/tl_2010_06037_tract10.zip"


def main() -> None:
    ensure_dirs(DATA_RAW / "tiger", DATA_PROCESSED)
    zip_path = DATA_RAW / "tiger" / "tl_2010_06037_tract10.zip"
    extract_dir = DATA_RAW / "tiger" / "tl_2010_06037_tract10"

    print(f"Downloading {URL}")
    r = requests.get(URL, timeout=300)
    r.raise_for_status()
    zip_path.write_bytes(r.content)
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_dir)

    shp = next(extract_dir.glob("*.shp"))
    gdf = gpd.read_file(shp)
    # Field names in 2010 files: GEOID10, TRACTCE10, ALAND10, AWATER10
    gdf = gdf.rename(
        columns={
            "GEOID10": "geoid10",
            "TRACTCE10": "tractce10",
            "ALAND10": "aland10",
            "AWATER10": "awater10",
        }
    )
    gdf["geoid10"] = gdf["geoid10"].map(zfill_geoid10)
    gdf = gdf[["geoid10", "tractce10", "aland10", "awater10", "geometry"]].copy()
    gdf = gdf.to_crs("EPSG:4326")

    out_geojson = DATA_PROCESSED / "tracts_la_2010.geojson"
    out_parquet = DATA_PROCESSED / "tracts_la_2010.parquet"
    gdf.to_file(out_geojson, driver="GeoJSON")
    try:
        gdf.to_parquet(out_parquet)
    except Exception as exc:  # pragma: no cover
        print(f"  parquet skipped ({exc})")
    print(f"tracts: {len(gdf)} → {out_geojson}")


if __name__ == "__main__":
    main()
