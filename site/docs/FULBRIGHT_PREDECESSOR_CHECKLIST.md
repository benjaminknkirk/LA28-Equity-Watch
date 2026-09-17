# Fulbright Predecessor Checklist — Coverage Status

Status key: **Done** = implemented in repo · **Partial** = present with documented limits · **Design** = framework/docs ready for author fieldwork

| # | Requirement | Status | Where |
| --- | --- | --- | --- |
| 1 | Precise equity question | **Done** | `docs/RESEARCH_AGENDA_LA28_TO_BRISBANE.md`, stats JSON |
| 2 | Defined unit of analysis | **Done** | 2010 LA County census tracts (`METHODOLOGY.md`) |
| 3 | Socioeconomic disadvantage data + transparent framework | **Done** | ACS poverty, income, rent burden, vehicle, overcrowding + CES; `disadvantage_index.csv`; race/ethnicity as covariates |
| 4 | Geospatial mapping of LA28-related investments | **Done** | Venues, village/training (UCLA), transit, hubs, active transport, highway; curated + sourced |
| 5 | Baseline accessibility analysis | **Done** | Walk minutes + rail access before prospective adds |
| 6 | Network-based spatial analysis | **Partial→strong** | GTFS rail network graph (true network); walk via network detour factor (OSM GraphML hook when available); 15/30/45-min thresholds; multimodal minutes |
| 7 | Equity comparison | **Done** | Quartile / decile tables; Q4 vs Q1 gaps |
| 8 | Prospective component | **Done** | Current vs announced 2028 (S0 vs S2) |
| 9 | Scenario analysis | **Done** | S0 baseline · S1 opened+construction · S2 full announced · S3 delayed |
| 10 | Sensitivity testing | **Done** | Detour 1.2/1.35/1.5; thresholds; facility defs; CES vs composite |
| 11 | Benefits vs burdens distinction | **Done** | `docs/BENEFITS_BURDENS_AND_COMMUNITY.md` |
| 12 | Reproducible data pipeline | **Done** | `src/acquire`, `src/analyze`, `scripts/` |
| 13 | Technically credible toolkit | **Done** | Python, GeoPandas, GTFS, ACS, networkx; QGIS-compatible GeoJSON exports |
| 14 | Maps that answer analytical questions | **Done** | Disadvantage, venue access, accessibility change, scenario delta, gap map |
| 15 | At least one quantitative result | **Done** | Quartile gaps + Spearman/OLS in `stats_summary.json` |
| 16 | Policy interpretation | **Done** | Brief + site policy section; underserved/leverage flags |
| 17 | Documented limitations | **Done** | `METHODOLOGY.md` |
| 18 | Community-facing component | **Design** | Listening/interview/review protocol (no fabricated data) |
| 19 | Public-facing output | **Done** | `site/` + PDF brief + Pages workflow |
| 20 | Research gap Brisbane solves | **Done** | Research agenda doc |
| 21 | Methodological bridge to Hickman | **Done** | Research agenda table |
| 22 | Clean research progression narrative | **Done** | Research agenda + brief §5 |

## Most valuable additions (now present)

1. Network-oriented accessibility (GTFS rail + walk thresholds)  
2. Multi-indicator socioeconomic comparison  
3. Scenario modeling (S0–S3)  
4. Explicit Brisbane/Hickman gap narrative  
