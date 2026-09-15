"""
DATA DICTIONARY — ACS 2019 5-year estimates (LA County tracts, 2010 geography)

Variables:
  B01003_001E — Total population
  B19013_001E — Median household income (2019 inflation-adjusted dollars)
  B08201_001E — Total households (vehicles-available universe)
  B08201_002E — Households with no vehicle available

Derived:
  pct_no_vehicle = hh_no_vehicle / households

Access strategy (in order):
  1. Census Data API if CENSUS_API_KEY is set (.env)
  2. Else ACS 2019 Summary File sequences for California tracts (no key required):
       sequences 0002 (B01003), 0027 (B08201), 0058 (B19013)
       https://www2.census.gov/programs-surveys/acs/summary_file/2019/data/5_year_seq_by_state/California/Tracts_Block_Groups_Only/

Columns in data/processed/acs_la_2019.csv:
  geoid10, name, population, median_hh_income, households, hh_no_vehicle, pct_no_vehicle
"""
from __future__ import annotations

import io
import os
import sys
import zipfile
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import (  # noqa: E402
    ACS_YEAR,
    COUNTY_FIPS,
    DATA_PROCESSED,
    DATA_RAW,
    STATE_FIPS,
    ensure_dirs,
    load_dotenv,
    zfill_geoid10,
)

VARS = ["NAME", "B01003_001E", "B19013_001E", "B08201_001E", "B08201_002E"]

SF_BASE = (
    "https://www2.census.gov/programs-surveys/acs/summary_file/2019/data/"
    "5_year_seq_by_state/California/Tracts_Block_Groups_Only"
)
# Sequence → (estimate column positions, 0-based after FILEID..LOGRECNO prefix of 6 cols)
# Estimate files: FILEID, FILETYPE, STUSAB, CHARITER, SEQUENCE, LOGRECNO, then estimates…
# B01003 total = first estimate in seq 0002 after many other tables — use template positions.
# Safer approach: use Census sequence templates / known positions from lookup:
# For seq 0002, B01003 starts at estimate position per lookup line "130" → column index.
#
# From ACS_5yr_Seq_Table_Number_Lookup.txt:
#   B01003 seq 0002 position 130 → 1 cell (Total)
#   B08201 seq 0027 position 75 → cell1 Total, cell2 No vehicle
#   B19013 seq 0058 position 177 → 1 cell Median income
#
# Positions in the lookup are 1-based positions WITHIN the estimate portion of the sequence file.


def fetch_via_api(api_key: str) -> pd.DataFrame:
    url = f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5"
    params = {
        "get": ",".join(VARS),
        "for": "tract:*",
        "in": f"state:{STATE_FIPS} county:{COUNTY_FIPS}",
        "key": api_key,
    }
    r = requests.get(url, params=params, timeout=180)
    if r.status_code != 200:
        raise RuntimeError(f"Census API error {r.status_code}: {r.text[:300]}")
    data = r.json()
    header, *rows = data
    return pd.DataFrame(rows, columns=header)


def _download(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        return
    print(f"  downloading {url}")
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    dest.write_bytes(r.content)


def _read_estimate_file(path: Path) -> pd.DataFrame:
    # No header; comma-separated
    df = pd.read_csv(path, header=None, dtype=str, low_memory=False)
    # cols 0-5 metadata; col 5 = LOGRECNO
    df = df.rename(columns={5: "LOGRECNO"})
    return df


def fetch_via_summary_file(work: Path) -> pd.DataFrame:
    ensure_dirs(work)
    geo_path = work / "g20195ca.csv"
    _download(f"{SF_BASE}/g20195ca.csv", geo_path)

    sequences = {
        "0002": {"zip": "20195ca0002000.zip", "est": "e20195ca0002000.txt"},
        "0027": {"zip": "20195ca0027000.zip", "est": "e20195ca0027000.txt"},
        "0058": {"zip": "20195ca0058000.zip", "est": "e20195ca0058000.txt"},
    }
    for seq, meta in sequences.items():
        zpath = work / meta["zip"]
        _download(f"{SF_BASE}/{meta['zip']}", zpath)
        out_dir = work / f"seq{seq}"
        out_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(zpath) as zf:
            zf.extractall(out_dir)

    # Geography file: Latin-1 encoded; SUMLEVEL col index 2, LOGRECNO col 4, GEOID-ish near end
    geo = pd.read_csv(geo_path, header=None, dtype=str, encoding="latin-1", low_memory=False)
    # ACS SF geo layout (2019): 
    # 0 FILEID, 1 STUSAB, 2 SUMLEVEL, 3 COMPONENT, 4 LOGRECNO, ... 
    # GEOID is typically column 48 (0-based) as '14000US06037101110'
    # NAME is column 49
    geo = geo.rename(columns={2: "SUMLEVEL", 4: "LOGRECNO", 48: "GEOID", 49: "NAME"})
    tracts = geo[geo["SUMLEVEL"] == "140"].copy()
    tracts["geoid10"] = tracts["GEOID"].str.replace("14000US", "", regex=False)
    tracts = tracts[tracts["geoid10"].str.startswith(STATE_FIPS + COUNTY_FIPS)]
    tracts = tracts[["LOGRECNO", "geoid10", "NAME"]]

    e0002 = _read_estimate_file(work / "seq0002" / "e20195ca0002000.txt")
    e0027 = _read_estimate_file(work / "seq0027" / "e20195ca0027000.txt")
    e0058 = _read_estimate_file(work / "seq0058" / "e20195ca0058000.txt")

    # Absolute 0-based column indices from 2019_5yr_Summary_FileTemplates.zip
    # (seq2.xlsx / seq27.xlsx / seq58.xlsx headers).
    pop = e0002[["LOGRECNO", 129]].rename(columns={129: "B01003_001E"})
    veh_total = e0027[["LOGRECNO", 74]].rename(columns={74: "B08201_001E"})
    veh_none = e0027[["LOGRECNO", 75]].rename(columns={75: "B08201_002E"})
    income = e0058[["LOGRECNO", 176]].rename(columns={176: "B19013_001E"})

    out = tracts.merge(pop, on="LOGRECNO", how="left")
    out = out.merge(veh_total, on="LOGRECNO", how="left")
    out = out.merge(veh_none, on="LOGRECNO", how="left")
    out = out.merge(income, on="LOGRECNO", how="left")
    # Fabricate API-like columns for shared cleaner
    out["state"] = STATE_FIPS
    out["county"] = COUNTY_FIPS
    out["tract"] = out["geoid10"].str[-6:]
    return out


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "geoid10" not in df.columns:
        df["geoid10"] = (
            df["state"].astype(str) + df["county"].astype(str) + df["tract"].astype(str)
        ).map(zfill_geoid10)
    else:
        df["geoid10"] = df["geoid10"].map(zfill_geoid10)

    for col in ["B01003_001E", "B19013_001E", "B08201_001E", "B08201_002E"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df.loc[df[col] < 0, col] = pd.NA

    out = pd.DataFrame(
        {
            "geoid10": df["geoid10"],
            "name": df["NAME"],
            "population": df["B01003_001E"],
            "median_hh_income": df["B19013_001E"],
            "households": df["B08201_001E"],
            "hh_no_vehicle": df["B08201_002E"],
        }
    )
    out["pct_no_vehicle"] = out["hh_no_vehicle"] / out["households"]
    out = out.drop_duplicates("geoid10").sort_values("geoid10").reset_index(drop=True)
    if len(out) < 2000:
        raise ValueError(f"Unexpectedly few ACS tracts: {len(out)}")
    # sanity: population should be mostly non-null
    if out["population"].isna().mean() > 0.1:
        raise ValueError("Too many missing population values — check sequence column mapping")
    return out


def main() -> None:
    load_dotenv()
    ensure_dirs(DATA_RAW / "acs", DATA_PROCESSED)
    api_key = os.environ.get("CENSUS_API_KEY", "").strip()

    if api_key:
        print(f"Fetching ACS {ACS_YEAR} via Census API…")
        raw = fetch_via_api(api_key)
        source = "census_api"
    else:
        print(f"No CENSUS_API_KEY — using ACS {ACS_YEAR} Summary File (no key)…")
        raw = fetch_via_summary_file(DATA_RAW / "acs" / "summary2019")
        source = "summary_file"

    raw_path = DATA_RAW / "acs" / f"acs{ACS_YEAR}_la_raw_{source}.csv"
    raw.to_csv(raw_path, index=False)
    cleaned = clean(raw)
    out_path = DATA_PROCESSED / "acs_la_2019.csv"
    cleaned.to_csv(out_path, index=False)
    print(f"  source={source} rows={len(cleaned)} → {out_path}")
    print(cleaned[["population", "median_hh_income", "pct_no_vehicle"]].describe())


if __name__ == "__main__":
    main()
