"""
DATA DICTIONARY — ACS 2019 5-year estimates (LA County tracts, 2010 geography)

Socioeconomic / demographic variables for the Equity Watch disadvantage framework:

  population              B01003_001E
  median_hh_income        B19013_001E
  households              B08201_001E
  hh_no_vehicle           B08201_002E
  pct_no_vehicle          derived
  poverty_universe        B17001_001E
  poverty_count           B17001_002E
  poverty_rate            derived
  rent_universe           B25070_001E
  rent_burden_30plus      sum B25070_007E..010E (≥30% of income on rent)
  pct_rent_burden_30plus  derived
  occupied_units          B25014_001E
  overcrowded_units       owner+renter 1.01+ occupants/room cells
  pct_overcrowded         derived (housing vulnerability proxy)
  race_universe           B03002_001E
  pct_hispanic            B03002_012E / univ
  pct_nh_black            B03002_004E / univ
  pct_nh_asian            B03002_006E / univ
  pct_nh_white            B03002_003E / univ

Access: Census API if CENSUS_API_KEY set; else ACS 2019 Summary File sequences.
"""
from __future__ import annotations

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

SF_BASE = (
    "https://www2.census.gov/programs-surveys/acs/summary_file/2019/data/"
    "5_year_seq_by_state/California/Tracts_Block_Groups_Only"
)

# Absolute 0-based columns from 2019_5yr_Summary_FileTemplates.zip
SEQ_SPECS = {
    "0002": {"zip": "20195ca0002000.zip", "est": "e20195ca0002000.txt", "cols": {129: "B01003_001E"}},
    "0004": {
        "zip": "20195ca0004000.zip",
        "est": "e20195ca0004000.txt",
        "cols": {
            37: "B03002_001E",
            39: "B03002_003E",
            40: "B03002_004E",
            42: "B03002_006E",
            48: "B03002_012E",
        },
    },
    "0027": {
        "zip": "20195ca0027000.zip",
        "est": "e20195ca0027000.txt",
        "cols": {74: "B08201_001E", 75: "B08201_002E"},
    },
    "0047": {
        "zip": "20195ca0047000.zip",
        "est": "e20195ca0047000.txt",
        "cols": {6: "B17001_001E", 7: "B17001_002E"},
    },
    "0058": {"zip": "20195ca0058000.zip", "est": "e20195ca0058000.txt", "cols": {176: "B19013_001E"}},
    "0111": {
        "zip": "20195ca0111000.zip",
        "est": "e20195ca0111000.txt",
        "cols": {
            182: "B25014_001E",
            186: "B25014_005E",
            187: "B25014_006E",
            188: "B25014_007E",
            192: "B25014_011E",
            193: "B25014_012E",
            194: "B25014_013E",
        },
    },
    "0114": {
        "zip": "20195ca0114000.zip",
        "est": "e20195ca0114000.txt",
        "cols": {
            112: "B25070_001E",
            118: "B25070_007E",
            119: "B25070_008E",
            120: "B25070_009E",
            121: "B25070_010E",
        },
    },
}

API_VARS = [
    "NAME",
    "B01003_001E",
    "B19013_001E",
    "B08201_001E",
    "B08201_002E",
    "B17001_001E",
    "B17001_002E",
    "B25070_001E",
    "B25070_007E",
    "B25070_008E",
    "B25070_009E",
    "B25070_010E",
    "B25014_001E",
    "B25014_005E",
    "B25014_006E",
    "B25014_007E",
    "B25014_011E",
    "B25014_012E",
    "B25014_013E",
    "B03002_001E",
    "B03002_003E",
    "B03002_004E",
    "B03002_006E",
    "B03002_012E",
]


def _download(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        return
    print(f"  downloading {url}")
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    dest.write_bytes(r.content)


def _read_estimate_file(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, header=None, dtype=str, low_memory=False)
    return df.rename(columns={5: "LOGRECNO"})


def fetch_via_api(api_key: str) -> pd.DataFrame:
    url = f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5"
    # Census API limits ~50 vars; split if needed
    params = {
        "get": ",".join(API_VARS),
        "for": "tract:*",
        "in": f"state:{STATE_FIPS} county:{COUNTY_FIPS}",
        "key": api_key,
    }
    r = requests.get(url, params=params, timeout=180)
    if r.status_code != 200:
        raise RuntimeError(f"Census API error {r.status_code}: {r.text[:300]}")
    header, *rows = r.json()
    return pd.DataFrame(rows, columns=header)


def fetch_via_summary_file(work: Path) -> pd.DataFrame:
    ensure_dirs(work)
    geo_path = work / "g20195ca.csv"
    _download(f"{SF_BASE}/g20195ca.csv", geo_path)

    frames = []
    for seq, meta in SEQ_SPECS.items():
        zpath = work / meta["zip"]
        _download(f"{SF_BASE}/{meta['zip']}", zpath)
        out_dir = work / f"seq{seq}"
        out_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(zpath) as zf:
            zf.extractall(out_dir)
        e = _read_estimate_file(out_dir / meta["est"])
        keep = ["LOGRECNO"] + list(meta["cols"].keys())
        part = e[keep].rename(columns=meta["cols"])
        frames.append(part)

    merged = frames[0]
    for part in frames[1:]:
        merged = merged.merge(part, on="LOGRECNO", how="outer")

    geo = pd.read_csv(geo_path, header=None, dtype=str, encoding="latin-1", low_memory=False)
    geo = geo.rename(columns={2: "SUMLEVEL", 4: "LOGRECNO", 48: "GEOID", 49: "NAME"})
    tracts = geo[geo["SUMLEVEL"] == "140"].copy()
    tracts["geoid10"] = tracts["GEOID"].str.replace("14000US", "", regex=False)
    tracts = tracts[tracts["geoid10"].str.startswith(STATE_FIPS + COUNTY_FIPS)]
    tracts = tracts[["LOGRECNO", "geoid10", "NAME"]]
    out = tracts.merge(merged, on="LOGRECNO", how="left")
    out["state"] = STATE_FIPS
    out["county"] = COUNTY_FIPS
    out["tract"] = out["geoid10"].str[-6:]
    return out


def _num(s: pd.Series) -> pd.Series:
    v = pd.to_numeric(s, errors="coerce")
    return v.mask(v < 0)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "geoid10" not in df.columns:
        df["geoid10"] = (
            df["state"].astype(str) + df["county"].astype(str) + df["tract"].astype(str)
        ).map(zfill_geoid10)
    else:
        df["geoid10"] = df["geoid10"].map(zfill_geoid10)

    for col in [c for c in df.columns if c.startswith("B")]:
        df[col] = _num(df[col])

    rent_burden = (
        df["B25070_007E"].fillna(0)
        + df["B25070_008E"].fillna(0)
        + df["B25070_009E"].fillna(0)
        + df["B25070_010E"].fillna(0)
    )
    overcrowded = (
        df["B25014_005E"].fillna(0)
        + df["B25014_006E"].fillna(0)
        + df["B25014_007E"].fillna(0)
        + df["B25014_011E"].fillna(0)
        + df["B25014_012E"].fillna(0)
        + df["B25014_013E"].fillna(0)
    )

    out = pd.DataFrame(
        {
            "geoid10": df["geoid10"],
            "name": df["NAME"],
            "population": df["B01003_001E"],
            "median_hh_income": df["B19013_001E"],
            "households": df["B08201_001E"],
            "hh_no_vehicle": df["B08201_002E"],
            "poverty_universe": df["B17001_001E"],
            "poverty_count": df["B17001_002E"],
            "rent_universe": df["B25070_001E"],
            "rent_burden_30plus": rent_burden,
            "occupied_units": df["B25014_001E"],
            "overcrowded_units": overcrowded,
            "race_universe": df["B03002_001E"],
            "nh_white": df["B03002_003E"],
            "nh_black": df["B03002_004E"],
            "nh_asian": df["B03002_006E"],
            "hispanic": df["B03002_012E"],
        }
    )
    out["pct_no_vehicle"] = out["hh_no_vehicle"] / out["households"]
    out["poverty_rate"] = out["poverty_count"] / out["poverty_universe"]
    out["pct_rent_burden_30plus"] = out["rent_burden_30plus"] / out["rent_universe"]
    out["pct_overcrowded"] = out["overcrowded_units"] / out["occupied_units"]
    out["pct_hispanic"] = out["hispanic"] / out["race_universe"]
    out["pct_nh_black"] = out["nh_black"] / out["race_universe"]
    out["pct_nh_asian"] = out["nh_asian"] / out["race_universe"]
    out["pct_nh_white"] = out["nh_white"] / out["race_universe"]

    out = out.drop_duplicates("geoid10").sort_values("geoid10").reset_index(drop=True)
    if len(out) < 2000:
        raise ValueError(f"Unexpectedly few ACS tracts: {len(out)}")
    if out["population"].isna().mean() > 0.1:
        raise ValueError("Too many missing population values")
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
        print(f"No CENSUS_API_KEY — using ACS {ACS_YEAR} Summary File…")
        raw = fetch_via_summary_file(DATA_RAW / "acs" / "summary2019")
        source = "summary_file"

    raw_path = DATA_RAW / "acs" / f"acs{ACS_YEAR}_la_raw_{source}.csv"
    raw.to_csv(raw_path, index=False)
    cleaned = clean(raw)
    out_path = DATA_PROCESSED / "acs_la_2019.csv"
    cleaned.to_csv(out_path, index=False)
    print(f"  source={source} rows={len(cleaned)} → {out_path}")
    print(cleaned[["poverty_rate", "pct_rent_burden_30plus", "pct_overcrowded", "pct_no_vehicle"]].describe())


if __name__ == "__main__":
    main()
