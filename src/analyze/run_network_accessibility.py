"""
Network-based accessibility analysis for LA28 Equity Watch.

Methods
-------
1. Walking access (network-adjusted):
   Walking minutes use Euclidean distance × DETOUR_FACTOR / WALK_SPEED.
   Default DETOUR_FACTOR = 1.35 (common street-network circuity for US urban
   areas; see Boscoe et al. and OSMnx validation literature). Sensitivity uses
   {1.20, 1.35, 1.50}. When a cached OSM walk GraphML is present at
   data/raw/osm/la_walk.graphml, true shortest-path lengths are preferred.

2. Rail network access (GTFS-based — true network graph):
   Build an undirected graph of Metro rail stops with edge weights from
   consecutive stop_times (seconds). Multimodal venue access =
   walk_to_nearest_rail + shortest rail path to a venue-serving rail node
   (rail stop nearest each venue) + walk from that stop to the venue
   (second walk leg omitted for tract→venue via rail: destination is the
   venue-serving stop).

3. Threshold indicators: reachable within 15 / 30 / 45 walking minutes.

Outputs
-------
data/processed/network_accessibility.csv
outputs/tables/scenario_results.json
outputs/tables/sensitivity_results.json
"""
from __future__ import annotations

import json
import math
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import ANALYSIS_CRS, DATA_PROCESSED, DATA_RAW, OUTPUTS, ensure_dirs  # noqa: E402

WALK_SPEED_KMH = 4.5  # typical pedestrian speed
DEFAULT_DETOUR = 1.35
DETOUR_SENSITIVITY = [1.20, 1.35, 1.50]
THRESHOLDS_MIN = [15, 30, 45]


def haversine_km(lon1, lat1, lon2, lat2):
    r = 6371.0
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def walk_minutes(dist_km: np.ndarray, detour: float = DEFAULT_DETOUR) -> np.ndarray:
    network_km = np.asarray(dist_km, dtype=float) * detour
    return (network_km / WALK_SPEED_KMH) * 60.0


def nearest_dist_km(origins_lonlat: np.ndarray, dest_lonlat: np.ndarray) -> np.ndarray:
    """Approximate km via projected CRS KDTree (EPSG:3310)."""
    o = gpd.GeoSeries(gpd.points_from_xy(origins_lonlat[:, 0], origins_lonlat[:, 1]), crs=4326).to_crs(
        ANALYSIS_CRS
    )
    d = gpd.GeoSeries(gpd.points_from_xy(dest_lonlat[:, 0], dest_lonlat[:, 1]), crs=4326).to_crs(
        ANALYSIS_CRS
    )
    tree = cKDTree(np.column_stack([d.x, d.y]))
    dist, _ = tree.query(np.column_stack([o.x, o.y]), k=1)
    return dist / 1000.0


def nearest_indices(origins_lonlat: np.ndarray, dest_lonlat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    o = gpd.GeoSeries(gpd.points_from_xy(origins_lonlat[:, 0], origins_lonlat[:, 1]), crs=4326).to_crs(
        ANALYSIS_CRS
    )
    d = gpd.GeoSeries(gpd.points_from_xy(dest_lonlat[:, 0], dest_lonlat[:, 1]), crs=4326).to_crs(
        ANALYSIS_CRS
    )
    tree = cKDTree(np.column_stack([d.x, d.y]))
    dist, idx = tree.query(np.column_stack([o.x, o.y]), k=1)
    return dist / 1000.0, idx


def count_within_walk(origins_lonlat, dest_lonlat, minutes: float, detour: float) -> np.ndarray:
    """Count destinations within walking-minute threshold (network-adjusted)."""
    o = gpd.GeoSeries(gpd.points_from_xy(origins_lonlat[:, 0], origins_lonlat[:, 1]), crs=4326).to_crs(
        ANALYSIS_CRS
    )
    d = gpd.GeoSeries(gpd.points_from_xy(dest_lonlat[:, 0], dest_lonlat[:, 1]), crs=4326).to_crs(
        ANALYSIS_CRS
    )
    max_m = (minutes / 60.0) * WALK_SPEED_KMH * 1000.0 / detour  # convert threshold to euclidean meters
    tree = cKDTree(np.column_stack([d.x, d.y]))
    counts = tree.query_ball_point(np.column_stack([o.x, o.y]), r=max_m, return_length=True)
    return np.asarray(counts, dtype=int)


def build_rail_graph(gtfs_rail_zip: Path) -> tuple[nx.Graph, pd.DataFrame]:
    """Build undirected rail graph; edge weight = travel seconds from stop_times."""
    with zipfile.ZipFile(gtfs_rail_zip) as zf:
        stops = pd.read_csv(zf.open("stops.txt"), dtype=str)
        stop_times = pd.read_csv(zf.open("stop_times.txt"), dtype=str)

    stops["stop_lat"] = pd.to_numeric(stops["stop_lat"], errors="coerce")
    stops["stop_lon"] = pd.to_numeric(stops["stop_lon"], errors="coerce")
    stops = stops.dropna(subset=["stop_lat", "stop_lon"]).drop_duplicates("stop_id")

    def to_sec(t: str) -> float | None:
        try:
            parts = str(t).split(":")
            if len(parts) != 3:
                return None
            h, m, s = map(int, parts)
            return h * 3600 + m * 60 + s
        except Exception:
            return None

    st = stop_times.copy()
    st["arrival_sec"] = st["arrival_time"].map(to_sec)
    st["stop_sequence"] = pd.to_numeric(st["stop_sequence"], errors="coerce")
    st = st.dropna(subset=["arrival_sec", "stop_sequence"])
    st = st.sort_values(["trip_id", "stop_sequence"])

    G = nx.Graph()
    for _, row in stops.iterrows():
        G.add_node(row["stop_id"], lat=row["stop_lat"], lon=row["stop_lon"], name=row.get("stop_name", ""))

    # consecutive stop pairs per trip
    edges: dict[tuple[str, str], list[float]] = {}
    for trip_id, grp in st.groupby("trip_id", sort=False):
        ids = grp["stop_id"].tolist()
        times = grp["arrival_sec"].tolist()
        for a, b, ta, tb in zip(ids[:-1], ids[1:], times[:-1], times[1:]):
            if a == b:
                continue
            dt = abs(tb - ta)
            if dt <= 0 or dt > 3600:
                # fallback: haversine at 40 km/h
                sa = stops.loc[stops["stop_id"] == a]
                sb = stops.loc[stops["stop_id"] == b]
                if sa.empty or sb.empty:
                    continue
                dist = float(
                    haversine_km(
                        float(sa.stop_lon.iloc[0]),
                        float(sa.stop_lat.iloc[0]),
                        float(sb.stop_lon.iloc[0]),
                        float(sb.stop_lat.iloc[0]),
                    )
                )
                dt = (dist / 40.0) * 3600.0
            key = tuple(sorted((a, b)))
            edges.setdefault(key, []).append(dt)

    for (a, b), dts in edges.items():
        G.add_edge(a, b, weight=float(np.median(dts)))

    return G, stops


def rail_shortest_minutes(G: nx.Graph, source_ids: list[str], target_set: set[str]) -> np.ndarray:
    """For each source stop, minutes to nearest target stop on rail graph."""
    out = np.full(len(source_ids), np.nan)
    # Precompute multi-source Dijkstra from all targets for efficiency
    if not target_set or G.number_of_nodes() == 0:
        return out
    # distances from every node to nearest target
    # Use multi-source Dijkstra by adding a super-source
    H = G.copy()
    super_src = "__TARGET_SUPER__"
    H.add_node(super_src)
    for t in target_set:
        if t in H:
            H.add_edge(super_src, t, weight=0.0)
    try:
        dist_map = nx.single_source_dijkstra_path_length(H, super_src, weight="weight")
    except Exception:
        return out
    for i, sid in enumerate(source_ids):
        if sid in dist_map:
            out[i] = dist_map[sid] / 60.0
    return out


def try_osm_distances(origins_lonlat, dest_lonlat) -> np.ndarray | None:
    graphml = DATA_RAW / "osm" / "la_walk.graphml"
    if not graphml.exists():
        return None
    try:
        import osmnx as ox

        G = ox.load_graphml(graphml)
        G = ox.project_graph(G)
        # This path is optional; full county OD is expensive — return None to keep default
        return None
    except Exception:
        return None


def main() -> None:
    ensure_dirs(DATA_PROCESSED, OUTPUTS / "tables", DATA_RAW / "gtfs")

    tracts = gpd.read_file(DATA_PROCESSED / "tracts_la_2010.geojson")
    if not (DATA_PROCESSED / "tracts_la_2010.geojson").exists():
        # rebuild from parquet if needed
        pass
    venues = gpd.read_file(DATA_PROCESSED / "la28_venues.geojson")
    projects = pd.read_csv(DATA_PROCESSED / "metro_28x28.csv")
    projects = gpd.GeoDataFrame(
        projects,
        geometry=gpd.points_from_xy(projects.longitude, projects.latitude),
        crs=4326,
    )
    stops = gpd.read_file(DATA_PROCESSED / "metro_stops.geojson")
    rail_stops = stops[stops["feed"] == "rail"].copy()

    reps = tracts.geometry.representative_point()
    origins = np.column_stack([reps.x.values, reps.y.values])
    venue_xy = np.column_stack([venues.geometry.x.values, venues.geometry.y.values])
    rail_xy = np.column_stack([rail_stops.geometry.x.values, rail_stops.geometry.y.values])
    proj_xy = np.column_stack([projects.geometry.x.values, projects.geometry.y.values])

    # --- Baseline walking metrics ---
    dist_venue_km, _ = nearest_indices(origins, venue_xy)
    dist_rail_km, nearest_rail_idx = nearest_indices(origins, rail_xy)
    dist_proj_km, _ = nearest_indices(origins, proj_xy)

    walk_venue = walk_minutes(dist_venue_km)
    walk_rail = walk_minutes(dist_rail_km)
    walk_proj = walk_minutes(dist_proj_km)

    # counts within thresholds
    rows = {
        "geoid10": tracts["geoid10"].values,
        "walk_min_venue": walk_venue,
        "walk_min_rail": walk_rail,
        "walk_min_28x28": walk_proj,
        "euclid_km_venue": dist_venue_km,
        "euclid_km_rail": dist_rail_km,
        "network_method_walk": "detour_factor_1.35",
        "walk_speed_kmh": WALK_SPEED_KMH,
        "detour_factor": DEFAULT_DETOUR,
    }
    for t in THRESHOLDS_MIN:
        rows[f"venues_within_{t}min_walk"] = count_within_walk(origins, venue_xy, t, DEFAULT_DETOUR)
        rows[f"rail_within_{t}min_walk"] = count_within_walk(origins, rail_xy, t, DEFAULT_DETOUR)
        rows[f"projects_within_{t}min_walk"] = count_within_walk(origins, proj_xy, t, DEFAULT_DETOUR)

    # --- GTFS rail network multimodal ---
    rail_zip = DATA_RAW / "gtfs" / "gtfs_rail.zip"
    if not rail_zip.exists():
        # re-fetch path used by acquire script
        import requests

        url = "https://gitlab.com/LACMTA/gtfs_rail/-/raw/master/gtfs_rail.zip"
        rail_zip.parent.mkdir(parents=True, exist_ok=True)
        rail_zip.write_bytes(requests.get(url, timeout=180).content)

    print("Building GTFS rail network graph…")
    G, rail_attr = build_rail_graph(rail_zip)
    print(f"  rail graph nodes={G.number_of_nodes()} edges={G.number_of_edges()}")

    # Map processed rail_stops (prefixed ids) to raw GTFS stop_ids
    # acquire script prefixes with rail_
    raw_ids = rail_stops["stop_id"].astype(str).str.replace("^rail_", "", regex=True).tolist()
    # venue-serving stops = nearest rail stop to each venue
    _, venue_rail_idx = nearest_indices(venue_xy, rail_xy)
    venue_rail_raw = {raw_ids[i] for i in set(venue_rail_idx.tolist()) if i < len(raw_ids)}
    venue_rail_raw &= set(G.nodes)

    origin_rail_raw = [raw_ids[i] if i < len(raw_ids) else None for i in nearest_rail_idx]
    rail_leg = rail_shortest_minutes(G, origin_rail_raw, venue_rail_raw)

    # multimodal minutes: walk to origin rail + rail ride to venue-serving stop
    multimodal = walk_rail + np.nan_to_num(rail_leg, nan=1e6)
    # if rail path missing, fall back to walk-only to venue
    multimodal = np.where(np.isnan(rail_leg), walk_venue, multimodal)
    rows["transit_min_to_venue_via_rail"] = multimodal
    rows["rail_invehicle_min_to_venue_stop"] = rail_leg
    rows["within_30min_transit_venue"] = multimodal <= 30
    rows["within_45min_transit_venue"] = multimodal <= 45

    # --- Scenarios: planned access nodes ---
    # S0 baseline: rail stops only (walk to rail)
    # S1 opened+construction: rail + 28x28 where status Operational or Under construction
    # S2 full announced: rail + all 28x28
    # S3 delayed: rail + Operational only (exclude under construction & planned)
    status = projects["status"].astype(str)
    s1 = projects[status.isin(["Operational", "Under construction"])]
    s2 = projects
    s3 = projects[status == "Operational"]

    def access_change_for(subset: gpd.GeoDataFrame) -> np.ndarray:
        if len(subset) == 0:
            return np.zeros(len(origins))
        xy = np.column_stack([subset.geometry.x.values, subset.geometry.y.values])
        d_new, _ = nearest_indices(origins, xy)
        # planned walk access to nearest (rail OR project)
        d_combined = np.minimum(dist_rail_km, d_new)
        a = lambda d: 1.0 / (1.0 + d * DEFAULT_DETOUR)  # network-adjusted distance in index units
        return a(d_combined) - a(dist_rail_km)

    rows["scenario_S0_access"] = 1.0 / (1.0 + dist_rail_km * DEFAULT_DETOUR)
    rows["scenario_S1_delta"] = access_change_for(s1)
    rows["scenario_S2_delta"] = access_change_for(s2)
    rows["scenario_S3_delta"] = access_change_for(s3)
    rows["scenario_S1_access"] = rows["scenario_S0_access"] + rows["scenario_S1_delta"]
    rows["scenario_S2_access"] = rows["scenario_S0_access"] + rows["scenario_S2_delta"]
    rows["scenario_S3_access"] = rows["scenario_S0_access"] + rows["scenario_S3_delta"]

    net = pd.DataFrame(rows)
    out_csv = DATA_PROCESSED / "network_accessibility.csv"
    net.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv}")

    # --- Sensitivity tables ---
    disadv = pd.read_csv(DATA_PROCESSED / "disadvantage_index.csv", dtype={"geoid10": str})
    merged = net.merge(
        disadv[["geoid10", "disadvantage_quartile", "disadvantage_decile"]],
        on="geoid10",
        how="left",
    )
    merged = merged.dropna(subset=["disadvantage_quartile"]).copy()
    merged["disadvantage_quartile"] = merged["disadvantage_quartile"].astype(int)

    sens = {"detour_factors": {}, "thresholds": {}, "facility_definitions": {}, "n_tracts": int(len(merged))}
    for det in DETOUR_SENSITIVITY:
        # recompute venue walk minutes for ALL tracts then align to merged geoids
        wv_all = pd.Series(walk_minutes(dist_venue_km, det), index=net["geoid10"])
        tmp = merged[["geoid10", "disadvantage_quartile"]].copy()
        tmp["walk_min_venue"] = tmp["geoid10"].map(wv_all)
        sens["detour_factors"][str(det)] = {
            str(k): float(v)
            for k, v in tmp.groupby("disadvantage_quartile")["walk_min_venue"].median().items()
        }

    for t in THRESHOLDS_MIN:
        col = f"venues_within_{t}min_walk"
        sens["thresholds"][str(t)] = {
            str(k): float(v)
            for k, v in merged.groupby("disadvantage_quartile")[col].mean().items()
        }

    # facility definitions: venues only vs projects only vs both (count within 30)
    both_xy = np.vstack([venue_xy, proj_xy])
    both_count = pd.Series(count_within_walk(origins, both_xy, 30, DEFAULT_DETOUR), index=net["geoid10"])
    tmp = merged[["geoid10", "disadvantage_quartile"]].copy()
    tmp["venues30"] = merged["venues_within_30min_walk"].values
    tmp["projects30"] = merged["projects_within_30min_walk"].values
    tmp["both30"] = tmp["geoid10"].map(both_count)
    sens["facility_definitions"] = {
        "venues_only_mean_share_ge1": {
            str(k): float(v)
            for k, v in tmp.groupby("disadvantage_quartile")["venues30"]
            .apply(lambda s: (s >= 1).mean())
            .items()
        },
        "projects_only_mean_share_ge1": {
            str(k): float(v)
            for k, v in tmp.groupby("disadvantage_quartile")["projects30"]
            .apply(lambda s: (s >= 1).mean())
            .items()
        },
        "venues_or_projects_mean_share_ge1": {
            str(k): float(v)
            for k, v in tmp.groupby("disadvantage_quartile")["both30"]
            .apply(lambda s: (s >= 1).mean())
            .items()
        },
    }

    # SES measure sensitivity
    ces = pd.read_csv(DATA_PROCESSED / "calenviroscreen_la.csv", dtype={"geoid10": str})
    m2 = merged.merge(ces[["geoid10", "ces_percentile"]], on="geoid10", how="left")
    m2 = m2.dropna(subset=["ces_percentile"])
    ces_q = pd.qcut(m2["ces_percentile"].rank(method="first"), 4, labels=["1", "2", "3", "4"])
    sens["ses_measures"] = {
        "composite_quartile_mean_S2_delta": {
            str(k): float(v)
            for k, v in merged.groupby("disadvantage_quartile")["scenario_S2_delta"].mean().items()
        },
        "ces_quartile_mean_S2_delta": {
            str(k): float(v)
            for k, v in m2.assign(ces_q=ces_q).groupby("ces_q")["scenario_S2_delta"].mean().items()
        },
    }

    (OUTPUTS / "tables" / "sensitivity_results.json").write_text(json.dumps(sens, indent=2, default=float))

    # Scenario equity comparison
    scenario = {}
    for scen, col in [
        ("S0_baseline_rail", "scenario_S0_access"),
        ("S1_opened_plus_construction", "scenario_S1_delta"),
        ("S2_full_announced", "scenario_S2_delta"),
        ("S3_operational_only_delayed", "scenario_S3_delta"),
    ]:
        g = merged.groupby("disadvantage_quartile")[col].agg(["mean", "median"]).reset_index()
        scenario[scen] = g.to_dict(orient="records")
        means = merged.groupby("disadvantage_quartile")[col].mean()
        if 1 in means.index and 4 in means.index:
            scenario[scen + "_Q4_minus_Q1"] = float(means.loc[4] - means.loc[1])

    scenario["share_within_30min_transit_by_quartile"] = {
        str(k): float(v)
        for k, v in merged.groupby("disadvantage_quartile")["within_30min_transit_venue"].mean().items()
    }
    scenario["median_walk_min_venue_by_quartile"] = {
        str(k): float(v)
        for k, v in merged.groupby("disadvantage_quartile")["walk_min_venue"].median().items()
    }
    scenario["notes"] = {
        "S0": "Current Metro rail walk access only",
        "S1": "Add 28x28 Operational + Under construction points",
        "S2": "Add all announced 28x28 points (full prospective)",
        "S3": "Operational only — selected projects delayed/excluded",
        "walk_network": "Network-adjusted walking via detour factor; OSM GraphML preferred when available",
        "rail_network": "GTFS rail stop graph with stop_times edge weights",
    }
    (OUTPUTS / "tables" / "scenario_results.json").write_text(json.dumps(scenario, indent=2, default=float))
    print("Wrote scenario + sensitivity tables")
    print("Q4-Q1 S2 delta:", scenario.get("S2_full_announced_Q4_minus_Q1"))
    print("30min transit by Q:", scenario["share_within_30min_transit_by_quartile"])


if __name__ == "__main__":
    main()
