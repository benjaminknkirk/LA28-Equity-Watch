# Methodology — LA28 Equity Watch

**Author:** Benjamin Kirk  
**Study area:** Los Angeles County census tracts (2010 boundaries)  
**Role:** Reproducible prototype and Fulbright predecessor (LA28 → Brisbane 2032 / Hickman)

---

## 1. Research question

> How are LA28-related infrastructure investments and accessibility gains distributed across communities with different levels of socioeconomic disadvantage?

This is an **equity-of-distribution** question (not a generic “who benefits?” slogan). Continuity with Brisbane: the same question can be asked earlier in the planning cycle with stronger transport models.

---

## 2. Unit of analysis

| Choice | Decision | Why |
| --- | --- | --- |
| Geography | **2010 census tracts**, Los Angeles County | Matches CalEnviroScreen 4.0 & HPI 3.0; defensible small-area unit |
| Boundaries | Census TIGER/Line 2010 | Official polygons |
| Outside-county venues | Included as distance/network targets only | No multi-county SES reconciliation |

---

## 3. Socioeconomic disadvantage framework

### Indicators (ACS 2019 5-year + CES)

1. Poverty rate  
2. Median household income (**inverted**)  
3. % households with no vehicle  
4. % renter households with rent ≥30% of income  
5. % overcrowded units (>1 occupant/room) — housing vulnerability proxy  
6. CalEnviroScreen 4.0 percentile  

Each indicator is converted to a county z-score; the **composite disadvantage index** is the equal-weight mean of available z-scores. Quartiles/deciles are county-relative.

**Race/ethnicity** (Hispanic, NH Black, NH Asian, NH White shares) are retained as **covariates** for stratified description but are **not** in the default index (to avoid collapsing structural racism into a single SES score without explicit theory). HPI 3.0 validates orientation.

Script: `src/analyze/build_disadvantage_index.py` → `data/processed/disadvantage_index.csv`

---

## 4. Investment inventory (geocoded, sourced)

| Type | Source | Notes |
| --- | --- | --- |
| Competition venues | Wikipedia LA28 venues list + Nominatim | Manual curation; QA recommended |
| Olympic Village / training-related | UCLA | Tagged in venue inventory |
| Transit (rail/BRT/bus lanes) | Metro Board 2023-0756 Attachment A | Representative points for corridors |
| Mobility hubs / access | Same | Point proxies |
| Active transport / public realm | Rail-to-Rail; LA River bike path | Point proxies |
| Highway / ICM | I-5, I-105, I-405, SR 57/60 | Included for program completeness; interpreted cautiously |

**Not available as official GeoJSON:** LA28 venue coordinates and full 28×28 geometries — curated CSVs document every source and geocode method.

---

## 5. Accessibility methods

### 5.1 Baseline (pre–Games-related change)

- Network-adjusted **walking minutes** to nearest venue and nearest Metro rail stop  
- Default: Euclidean km × **1.35 detour factor** / 4.5 km/h walk speed  
- Threshold counts: destinations within **15 / 30 / 45** minutes  
- **GTFS rail network graph**: edges from consecutive `stop_times`; multimodal minutes = walk-to-rail + in-vehicle rail to venue-serving stop  

### 5.2 Prospective change

Accessibility index \(A(d) = 1/(1 + d_{\mathrm{network}})\) where \(d_{\mathrm{network}}\) is detour-adjusted km.  
\(\Delta A = A(\min(d_{\mathrm{rail}}, d_{28\times28})) - A(d_{\mathrm{rail}})\).

### 5.3 Scenarios

| ID | Definition |
| --- | --- |
| S0 | Current rail walk access only |
| S1 | Rail + 28×28 Operational & Under construction |
| S2 | Rail + all announced 28×28 (full prospective) |
| S3 | Rail + Operational only (selected projects delayed/excluded) |

### 5.4 Sensitivity

- Detour factors 1.20 / 1.35 / 1.50  
- Thresholds 15 / 30 / 45  
- Facility sets: venues / projects / both  
- SES: composite vs CES quartiles  

**OSM note:** Full Overpass download failed in this environment (SSL). Code prefers `data/raw/osm/la_walk.graphml` when present; otherwise uses documented detour factors. Brisbane/Hickman should replace this with OSM shortest paths + OTP/R5.

---

## 6. Equity comparison & statistics

- Cross-tabs by disadvantage quartile/decile  
- Spearman correlations; OLS of S2 Δ on disadvantage index  
- Q4 − Q1 gaps for walk time, transit threshold share, and scenario Δ  

---

## 7. Benefits and burdens

See `docs/BENEFITS_BURDENS_AND_COMMUNITY.md`. The model measures access benefits; burdens (displacement, construction, security) are **named but not fully quantified**.

---

## 8. Limitations

1. Corridor projects as **points** understate linear coverage.  
2. Walk network uses **detour factors** unless OSM GraphML is supplied.  
3. Rail-only GTFS graph (bus not in multimodal router).  
4. Accessibility ≠ utilization or fare affordability.  
5. Announced projects may change; statuses become stale.  
6. Manual geocoding error risk.  
7. Displacement / rent effects require separate analysis.  
8. Community listening not yet executed (protocol only).  

---

## 9. Reproducibility

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash scripts/run_all.sh
```

Stepwise equivalents are listed in `README.md`. Optional: `CENSUS_API_KEY`, `HPI_API_KEY` in `.env`; optional OSM GraphML at `data/raw/osm/la_walk.graphml`.

---

## 10. Brisbane / Hickman bridge

See `docs/RESEARCH_AGENDA_LA28_TO_BRISBANE.md` and `docs/FULBRIGHT_PREDECESSOR_CHECKLIST.md`.
