"""
Integrate Euclidean proximity, network accessibility, scenarios, and disadvantage
into a single tract-level analysis table + equity statistics.
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


def _nearest_distance_km(origins, destinations: gpd.GeoDataFrame) -> np.ndarray:
    origins_p = gpd.GeoSeries(origins, crs=origins.crs).to_crs(ANALYSIS_CRS)
    dest_p = destinations.to_crs(ANALYSIS_CRS)
    tree = cKDTree(np.column_stack([dest_p.geometry.x.values, dest_p.geometry.y.values]))
    dist, _ = tree.query(np.column_stack([origins_p.x.values, origins_p.y.values]), k=1)
    return dist / 1000.0


def access_index(dist_km):
    return 1.0 / (1.0 + np.asarray(dist_km, dtype=float))


def main() -> None:
    ensure_dirs(OUTPUTS / "tables", DATA_PROCESSED)
    tracts = gpd.read_file(DATA_PROCESSED / "tracts_la_2010.geojson")
    ces = pd.read_csv(DATA_PROCESSED / "calenviroscreen_la.csv", dtype={"geoid10": str})
    hpi = pd.read_csv(DATA_PROCESSED / "hpi_la.csv", dtype={"geoid10": str})
    acs = pd.read_csv(DATA_PROCESSED / "acs_la_2019.csv", dtype={"geoid10": str})
    disadv = pd.read_csv(DATA_PROCESSED / "disadvantage_index.csv", dtype={"geoid10": str})
    net = pd.read_csv(DATA_PROCESSED / "network_accessibility.csv", dtype={"geoid10": str})
    venues = gpd.read_file(DATA_PROCESSED / "la28_venues.geojson")
    projects = gpd.read_file(DATA_PROCESSED / "metro_28x28.geojson")
    stops = gpd.read_file(DATA_PROCESSED / "metro_stops.geojson")
    rail = stops[stops["feed"] == "rail"].copy()

    gdf = tracts.merge(ces, on="geoid10", how="left")
    gdf = gdf.merge(hpi, on="geoid10", how="left")
    gdf = gdf.merge(
        acs.drop(columns=[c for c in acs.columns if c == "name"], errors="ignore"),
        on="geoid10",
        how="left",
    )
    gdf = gdf.merge(
        disadv[
            [
                "geoid10",
                "disadvantage_index",
                "disadvantage_decile",
                "disadvantage_quartile",
                "n_components",
            ]
        ],
        on="geoid10",
        how="left",
    )
    gdf = gdf.merge(net, on="geoid10", how="left")

    reps = gdf.geometry.representative_point()
    gdf["dist_venue_km"] = _nearest_distance_km(reps, venues)
    gdf["dist_28x28_km"] = _nearest_distance_km(reps, projects)
    gdf["dist_stop_km"] = _nearest_distance_km(reps, rail)
    gdf["venue_access"] = access_index(gdf["dist_venue_km"])
    gdf["a_base"] = access_index(gdf["dist_stop_km"])
    gdf["a_plan"] = access_index(np.minimum(gdf["dist_stop_km"], gdf["dist_28x28_km"]))
    gdf["access_change"] = gdf["a_plan"] - gdf["a_base"]

    # Equity comparisons by composite quartile
    complete = gdf.dropna(subset=["disadvantage_quartile", "access_change", "walk_min_venue"])
    complete["disadvantage_quartile"] = complete["disadvantage_quartile"].astype(int)

    q_summary = (
        complete.groupby("disadvantage_quartile")
        .agg(
            n=("geoid10", "count"),
            mean_access_change=("access_change", "mean"),
            mean_S2_delta=("scenario_S2_delta", "mean"),
            median_walk_min_venue=("walk_min_venue", "median"),
            share_30min_walk_venue=("venues_within_30min_walk", lambda s: (s >= 1).mean()),
            share_30min_transit=("within_30min_transit_venue", "mean"),
            mean_poverty=("poverty_rate", "mean"),
            mean_no_vehicle=("pct_no_vehicle", "mean"),
        )
        .reset_index()
    )
    q_summary.to_csv(OUTPUTS / "tables" / "equity_by_disadvantage_quartile.csv", index=False)

    # Stats
    spearman_change = stats.spearmanr(complete["disadvantage_decile"], complete["access_change"])
    spearman_walk = stats.spearmanr(complete["disadvantage_decile"], complete["walk_min_venue"])
    spearman_s2 = stats.spearmanr(complete["disadvantage_decile"], complete["scenario_S2_delta"])
    spearman_transit = stats.spearmanr(
        complete["disadvantage_decile"], complete["within_30min_transit_venue"].astype(float)
    )
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        complete["disadvantage_index"].astype(float), complete["scenario_S2_delta"].astype(float)
    )

    q1 = complete[complete["disadvantage_quartile"] == 1]
    q4 = complete[complete["disadvantage_quartile"] == 4]
    results = {
        "research_question": (
            "How are LA28-related infrastructure investments and accessibility gains "
            "distributed across communities with different levels of socioeconomic disadvantage?"
        ),
        "unit_of_analysis": "2010 census tracts, Los Angeles County",
        "n_tracts": int(len(gdf)),
        "n_complete": int(len(complete)),
        "spearman_access_change_vs_disadvantage_decile": {
            "correlation": float(spearman_change.correlation),
            "pvalue": float(spearman_change.pvalue),
        },
        "spearman_walk_min_venue_vs_disadvantage_decile": {
            "correlation": float(spearman_walk.correlation),
            "pvalue": float(spearman_walk.pvalue),
        },
        "spearman_S2_delta_vs_disadvantage_decile": {
            "correlation": float(spearman_s2.correlation),
            "pvalue": float(spearman_s2.pvalue),
        },
        "spearman_30min_transit_vs_disadvantage_decile": {
            "correlation": float(spearman_transit.correlation),
            "pvalue": float(spearman_transit.pvalue),
        },
        "ols_S2_delta_on_disadvantage_index": {
            "slope": float(slope),
            "intercept": float(intercept),
            "r_squared": float(r_value**2),
            "pvalue": float(p_value),
            "std_err": float(std_err),
        },
        "Q1_least_disadvantaged": {
            "median_walk_min_venue": float(q1["walk_min_venue"].median()),
            "share_30min_transit": float(q1["within_30min_transit_venue"].mean()),
            "mean_S2_delta": float(q1["scenario_S2_delta"].mean()),
        },
        "Q4_most_disadvantaged": {
            "median_walk_min_venue": float(q4["walk_min_venue"].median()),
            "share_30min_transit": float(q4["within_30min_transit_venue"].mean()),
            "mean_S2_delta": float(q4["scenario_S2_delta"].mean()),
        },
        "Q4_minus_Q1_S2_delta": float(q4["scenario_S2_delta"].mean() - q1["scenario_S2_delta"].mean()),
        "Q4_minus_Q1_median_walk_min": float(
            q4["walk_min_venue"].median() - q1["walk_min_venue"].median()
        ),
    }
    (OUTPUTS / "tables" / "stats_summary.json").write_text(json.dumps(results, indent=2))

    keep = [
        "geoid10",
        "disadvantage_index",
        "disadvantage_decile",
        "disadvantage_quartile",
        "ces_percentile",
        "hpi_percentile",
        "disadvantage_pctile",
        "population",
        "median_hh_income",
        "poverty_rate",
        "pct_no_vehicle",
        "pct_rent_burden_30plus",
        "pct_overcrowded",
        "pct_hispanic",
        "pct_nh_black",
        "dist_venue_km",
        "dist_28x28_km",
        "dist_stop_km",
        "venue_access",
        "access_change",
        "walk_min_venue",
        "walk_min_rail",
        "transit_min_to_venue_via_rail",
        "venues_within_15min_walk",
        "venues_within_30min_walk",
        "venues_within_45min_walk",
        "within_30min_transit_venue",
        "scenario_S0_access",
        "scenario_S1_delta",
        "scenario_S2_delta",
        "scenario_S3_delta",
        "geometry",
    ]
    keep = [c for c in keep if c in gdf.columns]
    gdf[keep].to_file(DATA_PROCESSED / "tract_analysis.geojson", driver="GeoJSON")
    gdf.drop(columns="geometry").to_csv(DATA_PROCESSED / "tract_analysis.csv", index=False)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
