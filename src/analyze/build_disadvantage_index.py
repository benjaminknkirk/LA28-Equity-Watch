"""
Transparent composite socioeconomic disadvantage index for LA County tracts.

DATA DICTIONARY — data/processed/disadvantage_index.csv
  geoid10
  z_poverty, z_income_inv, z_no_vehicle, z_rent_burden, z_overcrowd, z_ces
  disadvantage_index          — equal-weight mean of available z-scores (higher = more disadvantaged)
  disadvantage_decile         — county-relative decile 1–10
  disadvantage_quartile       — 1 (least) … 4 (most)
  n_components                — how many indicators entered the mean

Framework (equal weights; documented in METHODOLOGY.md):
  1. Poverty rate (ACS)
  2. Median household income (inverted)
  3. % households with no vehicle
  4. % renter households spending ≥30% of income on rent
  5. % overcrowded housing units (>1 occupant/room)
  6. CalEnviroScreen 4.0 percentile (environmental + socioeconomic cumulative burden)

Race/ethnicity shares are retained as covariates for stratified tables but are
NOT folded into the default index (analytically available; see METHODOLOGY).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import DATA_PROCESSED, ensure_dirs  # noqa: E402


def zscore(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    mu, sigma = s.mean(skipna=True), s.std(skipna=True)
    if sigma == 0 or np.isnan(sigma):
        return pd.Series(np.nan, index=s.index)
    return (s - mu) / sigma


def main() -> None:
    ensure_dirs(DATA_PROCESSED)
    acs = pd.read_csv(DATA_PROCESSED / "acs_la_2019.csv", dtype={"geoid10": str})
    ces = pd.read_csv(DATA_PROCESSED / "calenviroscreen_la.csv", dtype={"geoid10": str})
    df = acs.merge(ces[["geoid10", "ces_percentile"]], on="geoid10", how="left")

    components = pd.DataFrame(
        {
            "geoid10": df["geoid10"],
            "z_poverty": zscore(df["poverty_rate"]),
            "z_income_inv": zscore(-df["median_hh_income"]),
            "z_no_vehicle": zscore(df["pct_no_vehicle"]),
            "z_rent_burden": zscore(df["pct_rent_burden_30plus"]),
            "z_overcrowd": zscore(df["pct_overcrowded"]),
            "z_ces": zscore(df["ces_percentile"]),
        }
    )
    zcols = [c for c in components.columns if c.startswith("z_")]
    components["n_components"] = components[zcols].notna().sum(axis=1)
    components["disadvantage_index"] = components[zcols].mean(axis=1, skipna=True)

    pct = components["disadvantage_index"].rank(method="average", pct=True)
    components["disadvantage_decile"] = np.ceil(pct * 10).clip(1, 10).astype("Int64")
    components["disadvantage_quartile"] = np.ceil(pct * 4).clip(1, 4).astype("Int64")

    # attach raw SES fields for tables
    out = components.merge(
        df[
            [
                "geoid10",
                "poverty_rate",
                "median_hh_income",
                "pct_no_vehicle",
                "pct_rent_burden_30plus",
                "pct_overcrowded",
                "ces_percentile",
                "pct_hispanic",
                "pct_nh_black",
                "pct_nh_asian",
                "pct_nh_white",
                "population",
            ]
        ],
        on="geoid10",
        how="left",
    )
    path = DATA_PROCESSED / "disadvantage_index.csv"
    out.to_csv(path, index=False)
    print(f"Wrote {path} n={len(out)} mean_index={out['disadvantage_index'].mean():.3f}")


if __name__ == "__main__":
    main()
