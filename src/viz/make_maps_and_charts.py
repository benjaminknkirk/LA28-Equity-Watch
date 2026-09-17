"""Generate analytical maps/charts for disadvantage, access, scenarios, and gaps."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import folium
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from branca.colormap import LinearColormap
from matplotlib.lines import Line2D

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import DATA_PROCESSED, OUTPUTS, SITE, ensure_dirs  # noqa: E402

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.size": 10,
        "axes.titlesize": 12,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def save(fig, name: str):
    for folder in (OUTPUTS / "figures", SITE / "assets"):
        folder.mkdir(parents=True, exist_ok=True)
        fig.savefig(folder / name, bbox_inches="tight")
    plt.close(fig)


def main():
    ensure_dirs(OUTPUTS / "figures", OUTPUTS / "maps", SITE / "assets", SITE / "maps")
    gdf = gpd.read_file(DATA_PROCESSED / "tract_analysis.geojson")
    venues = gpd.read_file(DATA_PROCESSED / "la28_venues.geojson")
    projects = gpd.read_file(DATA_PROCESSED / "metro_28x28.geojson")
    stats = json.loads((OUTPUTS / "tables" / "stats_summary.json").read_text())
    equity = pd.read_csv(OUTPUTS / "tables" / "equity_by_disadvantage_quartile.csv")
    scenario = json.loads((OUTPUTS / "tables" / "scenario_results.json").read_text())

    # 1. Disadvantage choropleth + investments
    fig, ax = plt.subplots(figsize=(10, 12))
    gdf.plot(
        column="disadvantage_index",
        cmap="YlOrRd",
        linewidth=0.05,
        edgecolor="none",
        legend=True,
        legend_kwds={"label": "Composite disadvantage index\n(higher = more disadvantaged)", "shrink": 0.55},
        ax=ax,
        missing_kwds={"color": "lightgrey"},
    )
    projects.plot(ax=ax, color="#0b6e4f", markersize=22, marker="s", alpha=0.9)
    venues.plot(ax=ax, color="#1d3557", markersize=30, marker="^", alpha=0.9)
    ax.set_title("Composite socioeconomic disadvantage with LA28 venues\nand Metro Twenty-Eight by '28 points")
    ax.set_axis_off()
    ax.legend(
        handles=[
            Line2D([0], [0], marker="^", color="w", markerfacecolor="#1d3557", markersize=10, label="LA28 venues"),
            Line2D([0], [0], marker="s", color="w", markerfacecolor="#0b6e4f", markersize=9, label="28×28 projects"),
        ],
        loc="lower left",
    )
    save(fig, "choropleth_disadvantage_investments.png")

    # 2. Projected accessibility change (S2)
    fig, ax = plt.subplots(figsize=(10, 12))
    gdf.plot(
        column="scenario_S2_delta",
        cmap="RdYlGn",
        linewidth=0.05,
        edgecolor="none",
        legend=True,
        legend_kwds={"label": "S2 accessibility change\n(full announced 28×28 vs rail baseline)", "shrink": 0.55},
        ax=ax,
        missing_kwds={"color": "lightgrey"},
    )
    ax.set_title("Prospective accessibility change if announced 28×28 points are delivered")
    ax.set_axis_off()
    save(fig, "map_scenario_S2_delta.png")

    # 3. Persistent access deficit: high disadvantage + outside 30-min walk to venue
    fig, ax = plt.subplots(figsize=(10, 12))
    gdf.plot(color="#e8e4dc", linewidth=0.02, edgecolor="white", ax=ax)
    deficit = gdf[(gdf["disadvantage_quartile"] >= 4) & (gdf["venues_within_30min_walk"] < 1)]
    if len(deficit):
        deficit.plot(color="#9b2226", ax=ax, linewidth=0.05, edgecolor="none")
    venues.plot(ax=ax, color="#1d3557", markersize=28, marker="^", alpha=0.85)
    ax.set_title("Access deficit map: most-disadvantaged tracts (Q4)\noutside 30-minute walk of any LA28 venue")
    ax.set_axis_off()
    save(fig, "map_access_deficit_Q4.png")

    # 4. Baseline walk time to venue
    fig, ax = plt.subplots(figsize=(10, 12))
    gdf.plot(
        column="walk_min_venue",
        cmap="viridis_r",
        linewidth=0.05,
        edgecolor="none",
        legend=True,
        legend_kwds={"label": "Network-adjusted walk minutes\nto nearest LA28 venue", "shrink": 0.55},
        ax=ax,
        missing_kwds={"color": "lightgrey"},
    )
    ax.set_title("Baseline walking accessibility to nearest LA28 venue")
    ax.set_axis_off()
    save(fig, "map_walk_min_venue.png")

    # Charts
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(equity["disadvantage_quartile"], equity["mean_S2_delta"], color="#4a6741")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xlabel("Composite disadvantage quartile (4 = most disadvantaged)")
    ax.set_ylabel("Mean S2 accessibility change")
    ax.set_title("Prospective access gains by disadvantage quartile (full announced scenario)")
    save(fig, "chart_S2_delta_by_quartile.png")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(equity["disadvantage_quartile"], equity["median_walk_min_venue"], "o-", color="#1d3557")
    ax.set_xlabel("Composite disadvantage quartile (4 = most disadvantaged)")
    ax.set_ylabel("Median walk minutes to nearest venue")
    ax.set_title("Baseline venue walk time by disadvantage quartile")
    save(fig, "chart_walk_min_by_quartile.png")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(equity["disadvantage_quartile"], equity["share_30min_transit"], color="#457b9d")
    ax.set_xlabel("Composite disadvantage quartile (4 = most disadvantaged)")
    ax.set_ylabel("Share of tracts ≤30 min via walk+rail to venue")
    ax.set_title("30-minute multimodal transit access to venues by quartile")
    save(fig, "chart_30min_transit_by_quartile.png")

    # Scenario comparison chart
    fig, ax = plt.subplots(figsize=(8, 4.5))
    labels = ["S1 opened+\nconstruction", "S2 full\nannounced", "S3 operational\nonly (delayed)"]
    gaps = [
        scenario.get("S1_opened_plus_construction_Q4_minus_Q1", 0),
        scenario.get("S2_full_announced_Q4_minus_Q1", 0),
        scenario.get("S3_operational_only_delayed_Q4_minus_Q1", 0),
    ]
    ax.bar(labels, gaps, color=["#6a994e", "#2a9d8f", "#bc4749"])
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("Q4 − Q1 mean accessibility Δ")
    ax.set_title("Scenario equity gap (positive = more gain in most-disadvantaged quartile)")
    save(fig, "chart_scenario_equity_gaps.png")

    # Folium interactive
    simple = gdf[
        [
            "geoid10",
            "disadvantage_index",
            "scenario_S2_delta",
            "walk_min_venue",
            "within_30min_transit_venue",
            "geometry",
        ]
    ].copy()
    simple["geometry"] = simple.geometry.simplify(0.001)
    m = folium.Map(location=[34.05, -118.25], zoom_start=10, tiles="OpenStreetMap")
    cmap = LinearColormap(
        ["#ffffcc", "#fd8d3c", "#800026"],
        vmin=float(simple["disadvantage_index"].quantile(0.05)),
        vmax=float(simple["disadvantage_index"].quantile(0.95)),
        caption="Composite disadvantage index",
    )
    cmap.add_to(m)

    def style_fn(feat):
        val = feat["properties"].get("disadvantage_index")
        return {
            "fillColor": cmap(val) if val is not None else "#ccc",
            "color": "#666",
            "weight": 0.2,
            "fillOpacity": 0.7,
        }

    folium.GeoJson(
        simple.__geo_interface__,
        style_function=style_fn,
        tooltip=folium.GeoJsonTooltip(
            fields=["geoid10", "disadvantage_index", "walk_min_venue", "scenario_S2_delta"],
            aliases=["Tract", "Disadv. index", "Walk min venue", "S2 Δ access"],
        ),
    ).add_to(m)
    for _, row in venues.iterrows():
        folium.CircleMarker(
            [row.geometry.y, row.geometry.x], radius=5, color="#1d3557", fill=True, popup=row.get("name", "")
        ).add_to(m)
    for _, row in projects.iterrows():
        folium.CircleMarker(
            [row.geometry.y, row.geometry.x], radius=4, color="#0b6e4f", fill=True, popup=row.get("name", "")
        ).add_to(m)
    out_html = OUTPUTS / "maps" / "interactive_ces_map.html"
    m.save(str(out_html))
    m.save(str(SITE / "maps" / out_html.name))

    # Keep legacy filename alias for site
    import shutil

    shutil.copy(OUTPUTS / "figures" / "choropleth_disadvantage_investments.png", SITE / "assets" / "choropleth_ces_investments.png")
    print("Maps/charts written. Key Q4-Q1 S2 gap:", stats.get("Q4_minus_Q1_S2_delta"))


if __name__ == "__main__":
    main()
