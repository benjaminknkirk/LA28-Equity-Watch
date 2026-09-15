"""
DATA DICTIONARY — Healthy Places Index 3.0 (LA County tracts)

Primary source (automated, no personal API key required for LA County):
  LA County Open Data Feature Service — HPI Score (3.0)
  https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Healthy_Places_Index_3_0/FeatureServer/20
  Provenance note from service: HPI 3.0 file acquired 2022-04-25 from Public Health Institute
  on behalf of the Public Health Alliance of Southern California.

Optional source (statewide / official API):
  Set HPI_API_KEY after signing in at https://map.healthyplacesindex.org/
  See docs/hpi_api_notes.md. If a manual statewide file is dropped at
  data/raw/hpi/hpi30_manual.csv it will be preferred when --prefer-manual is set.

Columns kept in data/processed/hpi_la.csv:
  geoid10              — 11-digit 2010 census tract GEOID
  hpi_score            — HPI composite score (hpi; higher = healthier conditions)
  hpi_percentile       — Statewide percentile 0–1 (hpi_pctile; higher = healthier)
  hpi_quartile         — Quartile 1–4 (1 = least healthy / lowest conditions)
  hpi_least_healthy_25 — Yes/No flag for lowest statewide quartile
  disadvantage_pctile  — 1 - hpi_percentile (aligned with CES: higher = more disadvantaged)
  leb                  — Life expectancy at birth estimate
  pop_hpi              — Population used in HPI calculations

IMPORTANT ORIENTATION:
  Unlike CalEnviroScreen, higher HPI = healthier. We derive disadvantage_pctile
  by inverting hpi_percentile for cross-index comparison.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import DATA_PROCESSED, DATA_RAW, ensure_dirs, load_dotenv, zfill_geoid10  # noqa: E402

SERVICE = (
    "https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/"
    "Healthy_Places_Index_3_0/FeatureServer/20/query"
)
OUT_FIELDS = (
    "GEOID10,hpi,hpi_pctile,hpi_quartile,hpi_least_healthy_25pct,LEB,pop"
)


def fetch_lacounty_open_data() -> pd.DataFrame:
    rows = []
    offset = 0
    page = 2000
    while True:
        params = {
            "where": "1=1",
            "outFields": OUT_FIELDS,
            "returnGeometry": "false",
            "f": "json",
            "resultOffset": offset,
            "resultRecordCount": page,
            "orderByFields": "OBJECTID_1 ASC",
        }
        r = requests.get(SERVICE, params=params, timeout=120)
        r.raise_for_status()
        payload = r.json()
        if "error" in payload:
            raise RuntimeError(payload["error"])
        features = payload.get("features") or []
        if not features:
            break
        for feat in features:
            rows.append(feat["attributes"])
        if len(features) < page and not payload.get("exceededTransferLimit"):
            break
        offset += len(features)
        if offset > 10000:
            break
    return pd.DataFrame(rows)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    pct = pd.to_numeric(df["hpi_pctile"], errors="coerce")
    out = pd.DataFrame(
        {
            "geoid10": df["GEOID10"].map(zfill_geoid10),
            "hpi_score": pd.to_numeric(df["hpi"], errors="coerce"),
            "hpi_percentile": pct,
            "hpi_quartile": pd.to_numeric(df["hpi_quartile"], errors="coerce").astype("Int64"),
            "hpi_least_healthy_25": df["hpi_least_healthy_25pct"].astype(str),
            "disadvantage_pctile": 1.0 - pct,
            "leb": pd.to_numeric(df["LEB"], errors="coerce"),
            "pop_hpi": pd.to_numeric(df["pop"], errors="coerce"),
        }
    )
    out = out.drop_duplicates(subset=["geoid10"]).sort_values("geoid10").reset_index(drop=True)
    if len(out) < 2000:
        raise ValueError(f"Unexpectedly few HPI tracts: {len(out)}")
    return out


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prefer-manual",
        action="store_true",
        help="Use data/raw/hpi/hpi30_manual.csv if present",
    )
    args = parser.parse_args()

    ensure_dirs(DATA_RAW / "hpi", DATA_PROCESSED)
    raw_path = DATA_RAW / "hpi" / "hpi30_la_raw.csv"
    out_path = DATA_PROCESSED / "hpi_la.csv"
    manual = DATA_RAW / "hpi" / "hpi30_manual.csv"

    if args.prefer_manual and manual.exists():
        print(f"Loading manual HPI file {manual}")
        raw = pd.read_csv(manual, dtype=str)
    else:
        print("Fetching HPI 3.0 from LA County Open Data FeatureServer…")
        raw = fetch_lacounty_open_data()
        raw.to_csv(raw_path, index=False)
        print(f"  raw rows: {len(raw)} → {raw_path}")

    cleaned = clean(raw)
    cleaned.to_csv(out_path, index=False)
    print(f"  cleaned rows: {len(cleaned)} → {out_path}")
    print(
        "Note: Official HPI API key still recommended for provenance/updates; "
        "see docs/hpi_registration_status.md"
    )


if __name__ == "__main__":
    main()
