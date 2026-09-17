"""Shared paths and helpers for LA28 Equity Watch."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_CURATED = ROOT / "data" / "curated"
OUTPUTS = ROOT / "outputs"
SITE = ROOT / "site"

# Study area
STATE_FIPS = "06"
COUNTY_FIPS = "037"  # Los Angeles County
COUNTY_NAME = "Los Angeles"

# Geography vintage (align CES 4.0 + HPI 3.0)
TRACT_VINTAGE = 2010
ACS_YEAR = 2019  # last ACS 5-year on 2010 tract boundaries

# Projected CRS for distance calculations (meters)
ANALYSIS_CRS = "EPSG:3310"  # NAD83 California Albers


def load_dotenv(path: Path | None = None) -> None:
    """Minimal .env loader (no external dependency)."""
    env_path = path or (ROOT / ".env")
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def ensure_dirs(*paths: Path) -> None:
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


def zfill_geoid10(value) -> str:
    """Normalize a tract identifier to 11-digit GEOID10 (state+county+tract)."""
    s = str(value).strip()
    if s.endswith(".0"):
        s = s[:-2]
    s = s.replace(" ", "")
    if s.startswith("1400000US"):
        s = s[9:]
    # numeric without leading zero (e.g., 6037101110)
    if s.isdigit() and len(s) == 10:
        s = "0" + s
    if s.isdigit() and len(s) == 11:
        return s
    raise ValueError(f"Cannot normalize GEOID10 from value: {value!r}")
