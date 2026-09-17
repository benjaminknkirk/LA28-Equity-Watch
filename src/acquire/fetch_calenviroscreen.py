"""
DATA DICTIONARY — CalEnviroScreen 4.0 (LA County tracts)

Source: OEHHA CalEnviroScreen 4.0 Results ArcGIS Feature Service
URL: https://services1.arcgis.com/PCHfdHz4GlDNAhBb/arcgis/rest/services/CalEnviroScreen_4_0_Results_/FeatureServer/0
Access: Public (no API key). Filtered to Los Angeles County via tract FIPS range.

Columns kept in data/processed/calenviroscreen_la.csv:
  geoid10          — 11-digit 2010 census tract GEOID
  ces_score        — CalEnviroScreen 4.0 composite score (CIscore)
  ces_percentile   — Statewide percentile of composite score (CIscoreP; higher = more burdened)
  ces_decile       — Statewide decile 1–10 (CIdecile; 10 = most burdened)
  pollution_pctile — Pollution Burden percentile (PollutionP)
  popchar_pctile   — Population Characteristics percentile (PopCharP)
  total_pop_acs2019 — ACS 2019 total population from CES attributes (ACS2019TotalPop)

Notes:
  - CES 4.0 uses 2010 census tract boundaries.
  - Tract IDs in the service omit the leading state zero (e.g., 6037...); we restore it.
  - Higher scores/percentiles = greater cumulative burden (disadvantage orientation).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import DATA_PROCESSED, DATA_RAW, ensure_dirs, zfill_geoid10  # noqa: E402

SERVICE = (
    "https://services1.arcgis.com/PCHfdHz4GlDNAhBb/arcgis/rest/services/"
    "CalEnviroScreen_4_0_Results_/FeatureServer/0/query"
)
# LA County tracts: 6037xxxxxxxxx (without leading 0)
WHERE = "tract >= 6037000000 AND tract < 6038000000"
OUT_FIELDS = (
    "tract,TractTXT,CIscore,CIscoreP,CIdecile,PollutionP,PopCharP,ACS2019TotalPop"
)


def fetch_all() -> pd.DataFrame:
    rows = []
    offset = 0
    page = 2000
    while True:
        params = {
            "where": WHERE,
            "outFields": OUT_FIELDS,
            "returnGeometry": "false",
            "f": "json",
            "resultOffset": offset,
            "resultRecordCount": page,
            "orderByFields": "OBJECTID ASC",
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
        if not payload.get("exceededTransferLimit"):
            break
        offset += len(features)
    return pd.DataFrame(rows)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "geoid10": df["tract"].map(zfill_geoid10),
            "ces_score": pd.to_numeric(df["CIscore"], errors="coerce"),
            "ces_percentile": pd.to_numeric(df["CIscoreP"], errors="coerce"),
            "ces_decile": pd.to_numeric(df["CIdecile"], errors="coerce").astype("Int64"),
            "pollution_pctile": pd.to_numeric(df["PollutionP"], errors="coerce"),
            "popchar_pctile": pd.to_numeric(df["PopCharP"], errors="coerce"),
            "total_pop_acs2019": pd.to_numeric(df["ACS2019TotalPop"], errors="coerce"),
        }
    )
    out = out.drop_duplicates(subset=["geoid10"]).sort_values("geoid10").reset_index(drop=True)
    if out["geoid10"].duplicated().any():
        raise ValueError("Duplicate geoid10 after CES clean")
    if len(out) < 2000:
        raise ValueError(f"Unexpectedly few LA County CES tracts: {len(out)}")
    missing = out["ces_percentile"].isna().mean()
    if missing > 0.05:
        raise ValueError(f"Too many missing CES percentiles: {missing:.1%}")
    return out


def main() -> None:
    ensure_dirs(DATA_RAW / "calenviroscreen", DATA_PROCESSED)
    raw_path = DATA_RAW / "calenviroscreen" / "ces40_la_raw.csv"
    out_path = DATA_PROCESSED / "calenviroscreen_la.csv"

    print("Fetching CalEnviroScreen 4.0 for LA County…")
    raw = fetch_all()
    raw.to_csv(raw_path, index=False)
    print(f"  raw rows: {len(raw)} → {raw_path}")

    cleaned = clean(raw)
    cleaned.to_csv(out_path, index=False)
    print(f"  cleaned rows: {len(cleaned)} → {out_path}")
    print(cleaned.describe(include="all").transpose().head(10))


if __name__ == "__main__":
    main()
