# Research Agenda Continuity: LA28 → Brisbane 2032 → Hickman / UQ

## Precise equity question (LA28 Equity Watch)

> **How are LA28-related infrastructure investments and accessibility gains distributed across Los Angeles County census tracts with different levels of socioeconomic disadvantage?**

Disadvantage is measured with a transparent multi-indicator composite (poverty, income, vehicle access, rent burden, overcrowding, CalEnviroScreen) validated against HPI. Accessibility uses network-adjusted walking time and a GTFS rail network, with prospective scenarios for announced Twenty-Eight by ’28 projects.

## Unit of analysis

**2010 census tracts** in Los Angeles County — chosen to match CalEnviroScreen 4.0 and HPI 3.0 geography and to support small-area equity comparison without multi-county index reconciliation.

## Clean research progression

```text
LA28 Equity Watch (this project)
  → identifies spatial inequality patterns in Games-linked investment & access
  → demonstrates GIS + ACS + GTFS + scenario literacy
  → limitations expose need for earlier, multimodal prospective modeling
Brisbane 2032 planning window
  → infrastructure decisions still malleable (unlike late-stage LA28)
Hickman / UQ transport-accessibility expertise
  → rigorous network routing, scenario design, methodological validation
Improved framework returns as comparative Olympic legacy method (LA ↔ Brisbane)
```

## What LA28 already proves (competence)

| Capability | Evidence in this repository |
| --- | --- |
| GIS / spatial joins | Tract joins, KD-tree distances, choropleths |
| Spatial-equity framing | Composite disadvantage × accessibility cross-tabs |
| Basic–intermediate accessibility | Walk thresholds; GTFS rail graph; multimodal minutes |
| Prospective scenarios | S0–S3 baseline / announced / delayed |
| Sensitivity | Detour factors, thresholds, facility defs, SES measures |
| Reproducible Python pipeline | `src/acquire`, `src/analyze`, `src/viz` |
| Public research output | Static site + PDF brief |

## Research gap that Brisbane is uniquely positioned to solve

1. **Timing:** Near-Games LA analysis arrives **too late** to reshape the capital program; Brisbane’s planning-stage window allows prospective access modeling to inform decisions.  
2. **Multimodal rigor:** This prototype uses network-adjusted walking + a rail-only GTFS graph. Brisbane/Hickman should deploy full **schedule-based transit routers** (e.g., R5 / OpenTripPlanner) with bus + rail + walking.  
3. **Scenario policy design:** LA scenarios are illustrative (point proxies). Brisbane can co-design scenarios with agencies (build / delay / equity-priority packages) before final investment.  
4. **Burden pathways:** LA framework names displacement and construction burdens but does not model them; Brisbane can link accessibility change to housing-market indicators earlier.  
5. **Comparative method:** A paired LA–Brisbane design converts a US case study into a **general Olympic legacy measurement protocol**.

## Methodological bridge to Hickman

| LA28 Equity Watch establishes | Hickman / UQ should add |
| --- | --- |
| GIS competence & tract equity framing | Peer-reviewed transport accessibility methods |
| GTFS ingestion & simple rail graph | Full multimodal network assignment |
| Detour-factor walk times | OSM shortest paths / sidewalk networks |
| Four discrete scenarios | Structured scenario design & uncertainty |
| Spearman / OLS equity tests | Validation against observed ridership / travel surveys |
| Benefits/burdens taxonomy | Empirical burden indicators |

## Checklist coverage map

See [`docs/FULBRIGHT_PREDECESSOR_CHECKLIST.md`](FULBRIGHT_PREDECESSOR_CHECKLIST.md).
