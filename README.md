# LA28 Equity Watch

**Mapping Access to Olympic Investment Across Los Angeles**

Author: **Benjamin Kirk**

Research prototype analyzing whether planned LA28 Olympic venues and Metro’s Twenty-Eight by ’28 projects disproportionately benefit or bypass historically disadvantaged communities in Los Angeles County. Built as a reproducible methodology pilot for a Fulbright proposal comparing LA28 with Brisbane 2032.

Live site (GitHub Pages): configure Pages to deploy the `site/` folder via the included workflow (or serve `site/index.html` locally).

---

## Folder structure

```
data/
  raw/           # downloaded originals (gitignored; re-fetchable)
  processed/     # cleaned analysis-ready tables / geojson
  curated/       # version-controlled venue & 28×28 seed CSVs
notebooks/       # reserved (not used in v1)
src/
  acquire/       # download + clean scripts
  analyze/       # spatial joins, metrics, stats
  viz/           # maps, charts, brief/PDF
outputs/
  figures/ tables/ maps/ brief/
site/            # static research website (GitHub Pages)
docs/            # API registration notes
METHODOLOGY.md   # full methods & limitations
```

---

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional: CENSUS_API_KEY, HPI_API_KEY

bash scripts/run_acquire.sh
python -m src.analyze.run_spatial_analysis
python -m src.viz.make_maps_and_charts
python -m src.viz.build_brief
```

Open `site/index.html` in a browser.

---

## Data notes (important)

| Source | Automated? | Notes |
| --- | --- | --- |
| CalEnviroScreen 4.0 | Yes | OEHHA ArcGIS Feature Service |
| Healthy Places Index 3.0 | Yes (LA County) | Via LA County Open Data; official HPI API key still recommended for provenance |
| ACS 2019 5-year | Yes | Summary File (no key) or Census API if key set |
| TIGER 2010 tracts | Yes | Census Bureau |
| LA Metro GTFS | Yes | Bus + rail |
| LA28 venues | **Curated** | No official coordinate CSV; seed + Nominatim |
| Metro 28×28 | **Curated** | Board PDF list → representative points |

See [METHODOLOGY.md](METHODOLOGY.md) for the accessibility formula and limitations.

---

## License / attribution

Analysis code: MIT (unless otherwise noted). Upstream data retain their original terms (OEHHA, PHI/HPI, Census, LA Metro).
