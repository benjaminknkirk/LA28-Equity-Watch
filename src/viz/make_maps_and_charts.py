"""Generate static choropleth, supporting charts, and Folium interactive map."""
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


def load_data():
    gdf = gpd.read_file(DATA_PROCESSED / "tract_analysis.geojson")
    venues = gpd.read_file(DATA_PROCESSED / "la28_venues.geojson")
    projects = gpd.read_file(DATA_PROCESSED / "metro_28x28.geojson")
    stops = gpd.read_file(DATA_PROCESSED / "metro_stops.geojson")
    rail = stops[stops["feed"] == "rail"].copy()
    stats = json.loads((OUTPUTS / "tables" / "stats_summary.json").read_text())
    xtab = pd.read_csv(OUTPUTS / "tables" / "proximity_share_by_ces_decile.csv")
    return gdf, venues, projects, rail, stats, xtab


def make_choropleth(gdf, venues, projects, rail, out_png: Path):
    fig, ax = plt.subplots(figsize=(10, 12))
    gdf.plot(
        column="ces_percentile",
        cmap="YlOrRd",
        linewidth=0.05,
        edgecolor="none",
        legend=True,
        legend_kwds={"label": "CalEnviroScreen 4.0 percentile\n(higher = more burdened)", "shrink": 0.6},
        ax=ax,
        missing_kwds={"color": "lightgrey"},
    )
    # Rail stops as thin points
    rail.plot(ax=ax, color="#1a1a1a", markersize=2, alpha=0.35, label="Metro rail stops")
    projects.plot(ax=ax, color="#0b6e4f", markersize=28, marker="s", alpha=0.9, label="28×28 projects")
    venues.plot(ax=ax, color="#1d3557", markersize=36, marker="^", alpha=0.9, label="LA28 venues")
    ax.set_title(
        "LA County census tracts: CalEnviroScreen disadvantage\n"
        "with LA28 venues and Metro Twenty-Eight by '28 points"
    )
    ax.set_axis_off()
    handles = [
        Line2D([0], [0], marker="^", color="w", markerfacecolor="#1d3557", markersize=10, label="LA28 venues"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor="#0b6e4f", markersize=9, label="28×28 projects"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#1a1a1a", markersize=5, label="Metro rail stops"),
    ]
    ax.legend(handles=handles, loc="lower left", frameon=True)
    fig.tight_layout()
    fig.savefig(out_png, bbox_inches="tight")
    fig.savefig(SITE / "assets" / out_png.name, bbox_inches="tight")
    plt.close(fig)


def make_charts(xtab, gdf, stats, out_dir: Path):
    # Chart 1: mean access change by CES decile
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(xtab["ces_disadvantage_decile"], xtab["mean_access_change"], color="#4a6741", width=0.8)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("CES disadvantage decile (LA County; 10 = most burdened)")
    ax.set_ylabel("Mean accessibility change")
    ax.set_title("Accessibility change by CalEnviroScreen disadvantage decile")
    fig.tight_layout()
    p1 = out_dir / "access_change_by_decile.png"
    fig.savefig(p1, bbox_inches="tight")
    fig.savefig(SITE / "assets" / p1.name, bbox_inches="tight")
    plt.close(fig)

    # Chart 2: venue distance vs decile
    fig, ax = plt.subplots(figsize=(8, 4.5))
    summ = (
        gdf.dropna(subset=["ces_disadvantage_decile"])
        .groupby("ces_disadvantage_decile")["dist_venue_km"]
        .median()
    )
    ax.plot(summ.index, summ.values, marker="o", color="#1d3557")
    ax.set_xlabel("CES disadvantage decile (LA County; 10 = most burdened)")
    ax.set_ylabel("Median distance to nearest LA28 venue (km)")
    ax.set_title("Venue proximity by disadvantage decile")
    fig.tight_layout()
    p2 = out_dir / "venue_distance_by_decile.png"
    fig.savefig(p2, bbox_inches="tight")
    fig.savefig(SITE / "assets" / p2.name, bbox_inches="tight")
    plt.close(fig)

    # Chart 3: scatter access_change vs ces_percentile
    complete = gdf.dropna(subset=["ces_percentile", "access_change"])
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.scatter(
        complete["ces_percentile"],
        complete["access_change"],
        s=6,
        alpha=0.25,
        color="#333333",
        linewidths=0,
    )
    x = np.linspace(complete["ces_percentile"].min(), complete["ces_percentile"].max(), 100)
    slope = stats["ols_access_change_on_ces_percentile"]["slope"]
    intercept = stats["ols_access_change_on_ces_percentile"]["intercept"]
    ax.plot(x, intercept + slope * x, color="#9b2226", linewidth=2, label="OLS fit")
    ax.set_xlabel("CalEnviroScreen percentile (statewide)")
    ax.set_ylabel("Accessibility change")
    ax.set_title(
        f"Access change vs CES percentile "
        f"(R²={stats['ols_access_change_on_ces_percentile']['r_squared']:.4f}, "
        f"p={stats['ols_access_change_on_ces_percentile']['pvalue']:.3f})"
    )
    ax.legend()
    fig.tight_layout()
    p3 = out_dir / "scatter_access_vs_ces.png"
    fig.savefig(p3, bbox_inches="tight")
    fig.savefig(SITE / "assets" / p3.name, bbox_inches="tight")
    plt.close(fig)


def make_folium(gdf, venues, projects, out_html: Path):
    # Simplify for browser performance
    simple = gdf[["geoid10", "ces_percentile", "access_change", "dist_venue_km", "geometry"]].copy()
    simple["geometry"] = simple.geometry.simplify(0.001)
    center = [34.05, -118.25]
    m = folium.Map(location=center, zoom_start=10, tiles="OpenStreetMap")
    cmap = LinearColormap(
        colors=["#ffffcc", "#fd8d3c", "#800026"],
        vmin=float(simple["ces_percentile"].min()),
        vmax=float(simple["ces_percentile"].max()),
        caption="CalEnviroScreen percentile",
    )
    cmap.add_to(m)

    def style_fn(feature):
        val = feature["properties"].get("ces_percentile")
        return {
            "fillColor": cmap(val) if val is not None else "#cccccc",
            "color": "#666666",
            "weight": 0.2,
            "fillOpacity": 0.7,
        }

    folium.GeoJson(
        simple.__geo_interface__,
        style_function=style_fn,
        tooltip=folium.GeoJsonTooltip(
            fields=["geoid10", "ces_percentile", "access_change", "dist_venue_km"],
            aliases=["Tract", "CES %ile", "Access Δ", "Venue km"],
        ),
        name="CES disadvantage",
    ).add_to(m)

    venue_layer = folium.FeatureGroup(name="LA28 venues")
    for _, row in venues.iterrows():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=5,
            color="#1d3557",
            fill=True,
            fill_opacity=0.9,
            popup=row.get("name", ""),
        ).add_to(venue_layer)
    venue_layer.add_to(m)

    proj_layer = folium.FeatureGroup(name="28×28 projects")
    for _, row in projects.iterrows():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=4,
            color="#0b6e4f",
            fill=True,
            fill_opacity=0.9,
            popup=row.get("name", ""),
        ).add_to(proj_layer)
    proj_layer.add_to(m)

    folium.LayerControl().add_to(m)
    m.save(str(out_html))
    m.save(str(SITE / "maps" / out_html.name))


def main():
    ensure_dirs(OUTPUTS / "figures", OUTPUTS / "maps", SITE / "assets", SITE / "maps")
    gdf, venues, projects, rail, stats, xtab = load_data()
    make_choropleth(gdf, venues, projects, rail, OUTPUTS / "figures" / "choropleth_ces_investments.png")
    make_charts(xtab, gdf, stats, OUTPUTS / "figures")
    make_folium(gdf, venues, projects, OUTPUTS / "maps" / "interactive_ces_map.html")
    print("Figures written to outputs/figures and site/assets")


if __name__ == "__main__":
    main()
