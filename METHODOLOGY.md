# Methodology — LA28 Equity Watch

**Author:** Benjamin Kirk  
**Study area:** Los Angeles County census tracts (2010 boundaries)  
**Prototype scope:** Reproducible pipeline and static research brief supporting a Fulbright proposal comparing Olympic legacy measurement (LA28 → Brisbane 2032).

This document records every methodological choice, data source, and limitation for the Phase 1–5 analysis. Findings language in the brief is generated from pipeline outputs and should be rewritten by the author before formal publication.

---

## 1. Research question

Do planned LA28-related investments (Olympic venues and Metro’s Twenty-Eight by ’28 projects) disproportionately improve proximity for historically disadvantaged census tracts in Los Angeles County, relative to less burdened tracts?

“Disadvantage” is measured primarily with CalEnviroScreen 4.0 and validated with Healthy Places Index 3.0. “Access” is measured with a transparent proximity formula (not travel time or ridership).

---

## 2. Geographic unit and vintage

| Choice | Decision | Rationale |
| --- | --- | --- |
| Study area | Los Angeles County only | Aligns CES, HPI (LA County open data), ACS, and TIGER tracts without multi-county index reconciliation |
| Tract vintage | **2010** census tracts | CalEnviroScreen 4.0 and HPI 3.0 (API / county publish) use 2010 geography |
| Boundary source | Census TIGER/Line 2010 (`tl_2010_06037_tract10`) | Official tract polygons matching index vintages |
| Venues outside county | Included as distance targets | Honda Center, Trestles, etc. can still affect LA County tract distances without requiring Orange County sociodemographic joins |

---

## 3. Data sources

### 3.1 CalEnviroScreen 4.0 (primary disadvantage index)

- **Publisher:** California OEHHA  
- **Access:** Public ArcGIS Feature Service (no key)  
- **Filter:** Tract IDs `6037*` (LA County without leading zero)  
- **Orientation:** Higher score / percentile = greater cumulative burden  
- **Script:** `src/acquire/fetch_calenviroscreen.py`  
- **Output:** `data/processed/calenviroscreen_la.csv`

### 3.2 Healthy Places Index 3.0 (validation index)

- **Publisher:** Public Health Alliance of Southern California / Public Health Institute  
- **Access used:** LA County Open Data Feature Service layer “HPI Score (3.0)” (public; no personal API key required for LA County)  
- **Provenance note on service:** HPI 3.0 file acquired 2022-04-25 from PHI  
- **Orientation:** Higher HPI = healthier; we invert percentile → `disadvantage_pctile = 1 - hpi_percentile`  
- **Official API alternative:** Requires Google SSO account at map.healthyplacesindex.org (see `docs/hpi_registration_status.md`) — **not completed in this environment**  
- **Script:** `src/acquire/fetch_hpi.py`

### 3.3 American Community Survey 2019 5-year

- **Why 2019:** Last ACS 5-year release on **2010** tract boundaries  
- **Variables:** population (B01003), median household income (B19013), households / no-vehicle (B08201)  
- **Access:** Census Summary File sequences for California tracts (no API key). Census Data API path available if `CENSUS_API_KEY` is set.  
- **Script:** `src/acquire/fetch_acs.py`

### 3.4 LA Metro GTFS (baseline transit)

- **Feeds:** Bus + rail evergreen zips from LACMTA GitLab  
- **Role:** Existing high-capacity baseline = **rail stops** (n≈463) for nearest-stop distance  
- **Script:** `src/acquire/fetch_gtfs.py`

### 3.5 LA28 venues (manually curated)

- **Not available** as an official machine-readable coordinate file from LA28  
- **Compiled from:** Wikipedia “Venues of the 2028 Summer Olympics and Paralympics” (public list)  
- **Coordinates:** Nominatim/OpenStreetMap geocoding with documented queries (`data/curated/la28_venues_seed.csv`)  
- **Exclusions from distance set:** Oklahoma City venues and non-California football prelim sites (not regional LA investments)  
- **Script:** `src/acquire/build_investment_points.py`  
- **Flag for author QA:** Spot-check geocodes against official venue maps before publication

### 3.6 Metro Twenty-Eight by ’28 (manually curated)

- **Not available** as a public GeoJSON of all 28 projects  
- **Compiled from:** Metro Board Report 2023-0756 Attachment A (approved March 2024) and Wikipedia summary of the revised list  
- **Coordinates:** Curated representative points (station / corridor midpoints / interchange proxies) in `data/curated/metro_28x28_seed.csv`  
- **Limitation:** Linear corridor projects are represented as **points**, which understates coverage along the full alignment and can mis-rank tracts near a corridor but far from the chosen proxy

---

## 4. Accessibility change formula

For each tract, take a representative point inside the polygon. Project to **EPSG:3310** (California Albers). Compute Euclidean distances (km):

- \(d_{stop}\): nearest existing Metro **rail** stop  
- \(d_{28}\): nearest Twenty-Eight by ’28 project point  
- \(d_{venue}\): nearest LA28 venue point  

Inverse-distance accessibility:

\[
A(d) = \frac{1}{1 + d}
\]

- Baseline: \(A_{base} = A(d_{stop})\)  
- Planned: \(A_{plan} = A(\min(d_{stop}, d_{28}))\)  
- **Accessibility change:** \(\Delta A = A_{plan} - A_{base}\)  

\(\Delta A > 0\) only when a 28×28 point is closer than the nearest rail stop. This is a **conservative proximity proxy**, not a network travel-time, frequency, or ridership model.

Venue proximity is analyzed separately as \(A(d_{venue})\).

County-relative disadvantage deciles (1–10) are computed from CES percentile and inverted HPI percentile within LA County tracts with non-missing values.

---

## 5. Statistical tests

1. Spearman rank correlation: CES county decile vs \(\Delta A\)  
2. Spearman: CES county decile vs venue access  
3. OLS: \(\Delta A \sim\) CES statewide percentile  
4. Validation Spearman: HPI disadvantage decile vs \(\Delta A\)

No causal claim is made. Multiple comparisons are not adjusted (exploratory prototype).

---

## 6. Limitations (non-exhaustive)

1. Point proxies for corridor projects  
2. Euclidean distance ≠ travel time; no bus network, traffic, or Olympics shuttle (GETS) modeling  
3. CES/HPI vintages predate final Games operations; disadvantage is baseline community context, not Olympics impact  
4. Manual geocoding / curation error risk for venues and 28×28  
5. Using rail-only baseline ignores bus proximity (intentional high-capacity focus)  
6. HPI drawn from LA County republished layer rather than live HPI API pull in this run  
7. “Investment” here means spatial proximity to planned/opened project points, not dollars spent in a tract  
8. Football prelim venues in San Jose / San Diego inflate some long-distance venue minima for southern/northern county tracts relatively little, but are still included

---

## 7. Reproducibility

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash scripts/run_acquire.sh
python -m src.analyze.run_spatial_analysis
python -m src.viz.make_maps_and_charts
python -m src.viz.build_brief
```

Optional: set `CENSUS_API_KEY` and `HPI_API_KEY` in `.env` (see `.env.example`).
