#!/usr/bin/env bash
# Full reproducible pipeline for LA28 Equity Watch
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck disable=SC1091
source .venv/bin/activate

echo "== Acquire =="
python -m src.acquire.fetch_calenviroscreen
python -m src.acquire.fetch_hpi
python -m src.acquire.fetch_tiger_tracts
python -m src.acquire.fetch_gtfs
python -m src.acquire.fetch_acs
python -m src.acquire.build_investment_points

echo "== Analyze =="
python -m src.analyze.build_disadvantage_index
python -m src.analyze.run_network_accessibility
python -m src.analyze.run_spatial_analysis

echo "== Visualize / brief =="
python -m src.viz.make_maps_and_charts
python -m src.viz.build_brief
cp METHODOLOGY.md site/METHODOLOGY.md
mkdir -p site/docs
cp docs/FULBRIGHT_PREDECESSOR_CHECKLIST.md \
   docs/RESEARCH_AGENDA_LA28_TO_BRISBANE.md \
   docs/BENEFITS_BURDENS_AND_COMMUNITY.md \
   site/docs/

echo "Done. Open site/index.html"
