"""
Spatial equity analysis for LA28 investment accessibility vs disadvantage.

For each LA County 2010 census tract:
  - Join CES, HPI, ACS attributes
  - Distance (km) from tract centroid to nearest LA28 venue
  - Distance (km) to nearest Metro 28x28 project representative point
  - Distance (km) to nearest existing Metro stop (baseline transit)
  - County-relative disadvantage deciles (CES + inverted HPI)
  - Accessibility change metric (documented below)
  - Cross-tabs and Spearman / OLS association tests

ACCESSIBILITY CHANGE FORMULA
----------------------------
Let d_stop, d_28, d_venue be Euclidean distances (km) in EPSG:3310 from the
tract polygon centroid to the nearest existing Metro stop, nearest 28×28
project point, and nearest LA28 venue, respectively.

Define a simple inverse-distance accessibility index (unitless):

    A(d) = 1 / (1 + d)

Baseline transit access:     A_base  = A(d_stop)
Planned transit access:      A_plan  = A(min(d_stop, d_28))
Accessibility change:        access_change = A_plan - A_base

Interpretation: access_change > 0 only when a 28×28 point is closer than the
nearest existing Metro stop, i.e., the curated investment point would improve
proximity relative to today's network. This is a conservative proximity proxy,
not a travel-time or ridership model.

Olympic venue proximity (separate from change): venue_access = A(d_venue)

Primary equity test: association between access_change (and venue_access) and
ces_disadvantage_decile (1=least burdened in LA County, 10=most burdened).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import ANALYSIS_CRS, DATA_PROCESSED, OUTPUTS, ensure_dirs  # noqa: E402


def _nearest_distance_km(origins: gpd.GeoSeries, destinations: gpd.GeoDataFrame) -> np.ndarray:
    """Projected Euclidean nearest-neighbor distance in km."""
    origins_p = gpd.GeoSeries(origins, crs=origins.crs).to_crs(ANALYSIS_CRS)
    dest_p = destinations.to_crs(ANALYSIS_CRS)
    coords_o = np.column_stack([origins_p.x.values, origins_p.y.values])
    coords_d = np.column_stack([dest_p.geometry.x.values, dest_p.geometry.y.values])
    tree = cKDTree(coords_d)
    dist, _ = tree.query(coords_o, k=1)
    return dist / 1000.0  # meters → km


def access_index(dist_km: np.ndarray | pd.Series) -> np.ndarray:
    d = np.asarray(dist_km, dtype=float)
    return 1.0 / (1.0 + d)


def county_decile(series: pd.Series, higher_is_disadvantaged: bool = True) -> pd.Series:
    s = series.copy()
    if not higher_is_disadvantaged:
        s = -s
    # qcut with duplicates='drop' can yield fewer than 10; use rank percentiles
    pct = s.rank(method="average", pct=True)
    dec = np.ceil(pct * 10).clip(1, 10)
    return dec.astype("Int64")


def main() -> None:
    ensure_dirs(OUTPUTS / "tables", OUTPUTS / "figures", OUTPUTS / "maps", DATA_PROCESSED)

    tracts = gpd.read_file(DATA_PROCESSED / "tracts_la_2010.geojson")
    ces = pd.read_csv(DATA_PROCESSED / "calenviroscreen_la.csv", dtype={"geoid10": str})
    hpi = pd.read_csv(DATA_PROCESSED / "hpi_la.csv", dtype={"geoid10": str})
    acs = pd.read_csv(DATA_PROCESSED / "acs_la_2019.csv", dtype={"geoid10": str})
    venues = gpd.read_file(DATA_PROCESSED / "la28_venues.geojson")
    projects = gpd.read_file(DATA_PROCESSED / "metro_28x28.geojson")
    stops = gpd.read_file(DATA_PROCESSED / "metro_stops.geojson")

    # Prefer rail stops for baseline "high-capacity" access; fall back to all stops
    rail = stops[stops["feed"] == "rail"].copy()
    baseline_stops = rail if len(rail) >= 50 else stops

    gdf = tracts.merge(ces, on="geoid10", how="left")
    gdf = gdf.merge(hpi, on="geoid10", how="left")
    gdf = gdf.merge(acs, on="geoid10", how="left")

    # Use representative point to stay inside polygons
    reps = gdf.geometry.representative_point()

    print("Computing nearest distances…")
    gdf["dist_venue_km"] = _nearest_distance_km(reps, venues)
    gdf["dist_28x28_km"] = _nearest_distance_km(reps, projects)
    gdf["dist_stop_km"] = _nearest_distance_km(reps, baseline_stops)

    gdf["venue_access"] = access_index(gdf["dist_venue_km"])
    gdf["a_base"] = access_index(gdf["dist_stop_km"])
    gdf["a_plan"] = access_index(np.minimum(gdf["dist_stop_km"], gdf["dist_28x28_km"]))
    gdf["access_change"] = gdf["a_plan"] - gdf["a_base"]

    # Disadvantage deciles within LA County
    gdf["ces_disadvantage_decile"] = county_decile(gdf["ces_percentile"], True)
    gdf["hpi_disadvantage_decile"] = county_decile(gdf["disadvantage_pctile"], True)

    # Binary proximity flags
    gdf["venue_within_3km"] = gdf["dist_venue_km"] <= 3
    gdf["project_within_3km"] = gdf["dist_28x28_km"] <= 3
    gdf["project_closer_than_stop"] = gdf["dist_28x28_km"] < gdf["dist_stop_km"]

    # Cross-tabs
    xtab_change = (
        gdf.groupby("ces_disadvantage_decile", dropna=True)["access_change"]
        .agg(["count", "mean", "median", "std"])
        .reset_index()
    )
    xtab_venue = (
        gdf.groupby("ces_disadvantage_decile", dropna=True)["dist_venue_km"]
        .agg(["count", "mean", "median"])
        .reset_index()
    )
    xtab_share = (
        gdf.groupby("ces_disadvantage_decile", dropna=True)
        .agg(
            pct_venue_3km=("venue_within_3km", "mean"),
            pct_project_3km=("project_within_3km", "mean"),
            pct_project_improves=("project_closer_than_stop", "mean"),
            mean_access_change=("access_change", "mean"),
            mean_venue_access=("venue_access", "mean"),
        )
        .reset_index()
    )

    # Stats on complete cases
    complete = gdf.dropna(
        subset=["access_change", "ces_disadvantage_decile", "ces_percentile", "venue_access"]
    )
    spearman_change = stats.spearmanr(
        complete["ces_disadvantage_decile"], complete["access_change"]
    )
    spearman_venue = stats.spearmanr(
        complete["ces_disadvantage_decile"], complete["venue_access"]
    )
    # Simple OLS: access_change ~ ces_percentile
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        complete["ces_percentile"].astype(float), complete["access_change"].astype(float)
    )

    # HPI validation
    complete_hpi = gdf.dropna(subset=["access_change", "hpi_disadvantage_decile"])
    spearman_hpi = stats.spearmanr(
        complete_hpi["hpi_disadvantage_decile"], complete_hpi["access_change"]
    )

    results = {
        "n_tracts": int(len(gdf)),
        "n_complete_ces": int(len(complete)),
        "spearman_access_change_vs_ces_decile": {
            "correlation": float(spearman_change.correlation),
            "pvalue": float(spearman_change.pvalue),
        },
        "spearman_venue_access_vs_ces_decile": {
            "correlation": float(spearman_venue.correlation),
            "pvalue": float(spearman_venue.pvalue),
        },
        "ols_access_change_on_ces_percentile": {
            "slope": float(slope),
            "intercept": float(intercept),
            "r_squared": float(r_value**2),
            "pvalue": float(p_value),
            "std_err": float(std_err),
        },
        "spearman_access_change_vs_hpi_decile": {
            "correlation": float(spearman_hpi.correlation),
            "pvalue": float(spearman_hpi.pvalue),
        },
        "mean_access_change": float(gdf["access_change"].mean()),
        "share_project_improves_proximity": float(gdf["project_closer_than_stop"].mean()),
        "baseline_stop_feed": "rail" if len(rail) >= 50 else "bus+rail",
        "n_venues": int(len(venues)),
        "n_projects": int(len(projects)),
        "n_baseline_stops": int(len(baseline_stops)),
    }

    out_path = DATA_PROCESSED / "tract_analysis.geojson"
    # Drop huge unused cols for web friendliness
    keep_cols = [
        "geoid10",
        "ces_score",
        "ces_percentile",
        "ces_decile",
        "ces_disadvantage_decile",
        "hpi_percentile",
        "disadvantage_pctile",
        "hpi_disadvantage_decile",
        "population",
        "median_hh_income",
        "pct_no_vehicle",
        "dist_venue_km",
        "dist_28x28_km",
        "dist_stop_km",
        "venue_access",
        "a_base",
        "a_plan",
        "access_change",
        "venue_within_3km",
        "project_within_3km",
        "project_closer_than_stop",
        "geometry",
    ]
    gdf[keep_cols].to_file(out_path, driver="GeoJSON")
    gdf.drop(columns="geometry").to_csv(DATA_PROCESSED / "tract_analysis.csv", index=False)

    xtab_change.to_csv(OUTPUTS / "tables" / "access_change_by_ces_decile.csv", index=False)
    xtab_venue.to_csv(OUTPUTS / "tables" / "venue_distance_by_ces_decile.csv", index=False)
    xtab_share.to_csv(OUTPUTS / "tables" / "proximity_share_by_ces_decile.csv", index=False)
    (OUTPUTS / "tables" / "stats_summary.json").write_text(json.dumps(results, indent=2))

    print(json.dumps(results, indent=2))
    print("Wrote", out_path)


if __name__ == "__main__":
    main()
