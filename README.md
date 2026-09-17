# LA28 Equity Watch

**Mapping Access to Olympic Investment Across Los Angeles**

Author: **Benjamin Kirk**

Reproducible research prototype: how are LA28-related infrastructure investments and accessibility gains distributed across Los Angeles County census tracts with different levels of socioeconomic disadvantage? Built as the Fulbright predecessor to a Brisbane 2032 / Hickman transport-accessibility agenda.

Live site (GitHub Pages): configure Pages to deploy the `site/` folder via the included workflow (or open `site/index.html` locally).

---

## What this repo covers (22-item Fulbright predecessor checklist)

See [`docs/FULBRIGHT_PREDECESSOR_CHECKLIST.md`](docs/FULBRIGHT_PREDECESSOR_CHECKLIST.md) for the full status table. Highlights:

| Element | Implementation |
| --- | --- |
| Precise equity question + tract unit | Composite disadvantage × venue/28×28 access |
| Multi-indicator SES | Poverty, income, rent burden, vehicle access, overcrowding + CES |
| Network accessibility | Walk thresholds + GTFS rail graph; 15/30/45 min |
| Prospective scenarios | S0–S3 baseline / announced / delayed |
| Sensitivity | Detour factors, thresholds, facility defs, SES measures |
| Benefits vs burdens | [`docs/BENEFITS_BURDENS_AND_COMMUNITY.md`](docs/BENEFITS_BURDENS_AND_COMMUNITY.md) |
| Brisbane / Hickman gap | [`docs/RESEARCH_AGENDA_LA28_TO_BRISBANE.md`](docs/RESEARCH_AGENDA_LA28_TO_BRISBANE.md) |

---

## Folder structure

```
data/
  raw/           # downloaded originals (gitignored; re-fetchable)
  processed/     # cleaned analysis-ready tables / geojson
  curated/       # version-controlled venue & 28×28 seed CSVs
src/
  acquire/       # download + clean scripts
  analyze/       # disadvantage index, network access, equity stats
  viz/           # maps, charts, brief/PDF
outputs/
  figures/ tables/ maps/ brief/
site/            # static research website (GitHub Pages)
docs/            # checklist, research agenda, benefits/burdens, API notes
METHODOLOGY.md   # full methods & limitations
scripts/run_all.sh
```

---

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional: CENSUS_API_KEY, HPI_API_KEY

bash scripts/run_all.sh
# or stepwise:
# bash scripts/run_acquire.sh
# python -m src.analyze.build_disadvantage_index
# python -m src.analyze.run_network_accessibility
# python -m src.analyze.run_spatial_analysis
# python -m src.viz.make_maps_and_charts
# python -m src.viz.build_brief
```

Open `site/index.html` in a browser.

Optional OSM walk network: place GraphML at `data/raw/osm/la_walk.graphml` (otherwise documented detour factors are used).

---

## Data notes (important)

| Source | Automated? | Notes |
| --- | --- | --- |
| CalEnviroScreen 4.0 | Yes | OEHHA ArcGIS Feature Service |
| Healthy Places Index 3.0 | Yes (LA County) | Via LA County Open Data; official HPI API key still recommended for provenance |
| ACS 2019 5-year | Yes | Summary File (no key) or Census API if key set |
| TIGER 2010 tracts | Yes | Census Bureau |
| LA Metro GTFS | Yes | Bus + rail (rail used in network graph) |
| LA28 venues | **Curated** | No official coordinate CSV; seed + Nominatim |
| Metro 28×28 | **Curated** | Board PDF list → representative points |

See [METHODOLOGY.md](METHODOLOGY.md) for accessibility formulas, scenarios, sensitivity, and limitations.

---

## License / attribution

Analysis code: MIT (unless otherwise noted). Upstream data retain their original terms (OEHHA, PHI/HPI, Census, LA Metro).
