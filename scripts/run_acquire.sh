#!/usr/bin/env bash
# Run the full data acquisition pipeline (Phases 1–2 dependencies).
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck disable=SC1091
source .venv/bin/activate

python -m src.acquire.fetch_calenviroscreen
python -m src.acquire.fetch_hpi
python -m src.acquire.fetch_tiger_tracts
python -m src.acquire.fetch_gtfs
python -m src.acquire.fetch_acs
python -m src.acquire.build_investment_points

echo "Phase 2 complete. Processed outputs in data/processed/"
