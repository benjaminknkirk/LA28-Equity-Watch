# Mapping Access to Olympic Investment Across Los Angeles

**LA28 Equity Watch — Research Brief (draft)**  
**Author:** Benjamin Kirk  

> Draft findings language is generated from pipeline outputs for structure. Rewrite before Fulbright citation.

---

## 1. Motivation

**Research question:** How are LA28-related infrastructure investments and accessibility gains distributed across communities with different levels of socioeconomic disadvantage?

Los Angeles will host the 2028 Olympic and Paralympic Games amid Metro’s Twenty-Eight by ’28 program and a fixed venue map. Olympic legacy debates often claim equity benefits without measuring **how accessibility gains are distributed** across disadvantaged communities. This prototype builds a reproducible, tract-level equity analysis for Los Angeles County as the first stage of a research agenda culminating in Brisbane 2032 (with Hickman / UQ transport-accessibility methods).

**Unit of analysis:** 2010 census tracts, Los Angeles County (n=2346; complete-case n=2319).

---

## 2. Data & Methods

Full documentation: [`METHODOLOGY.md`](METHODOLOGY.md). Checklist: [`docs/FULBRIGHT_PREDECESSOR_CHECKLIST.md`](docs/FULBRIGHT_PREDECESSOR_CHECKLIST.md).

- **Disadvantage:** Equal-weight z-score composite of poverty, inverted income, no-vehicle share, rent burden ≥30%, overcrowding, and CalEnviroScreen percentile (race/ethnicity as covariates; HPI validation).  
- **Investments:** Geocoded LA28 venues (competition + village) and Metro 28×28 points (transit, hubs, active transport, highway), each with documented sources.  
- **Baseline access:** Network-adjusted walking minutes (detour factor 1.35) and GTFS **rail network** multimodal minutes.  
- **Prospective scenarios:** S0 rail baseline; S1 opened+under construction; S2 full announced; S3 operational-only (delay).  
- **Sensitivity:** Detour factors, 15/30/45-minute thresholds, facility definitions, CES vs composite.  
- **Benefits vs burdens:** Access benefits modeled; displacement/construction/security burdens named in [`docs/BENEFITS_BURDENS_AND_COMMUNITY.md`](docs/BENEFITS_BURDENS_AND_COMMUNITY.md).

---

## 3. Findings

### Disadvantage and investment geography

![Composite disadvantage with venues and 28×28 points](outputs/figures/choropleth_disadvantage_investments.png)

### Baseline accessibility

Median network-adjusted walk time to the nearest LA28 venue is **122.7 minutes** in the least-disadvantaged quartile (Q1) versus **78.0 minutes** in the most-disadvantaged quartile (Q4) (Q4−Q1 = -44.6 min). Spearman ρ(disadvantage decile, walk minutes) = **-0.238** (p = 3.43e-31).

Share of tracts with ≤30-minute **walk+rail** access to a venue-serving stop: **3.5%** (Q1) vs **12.4%** (Q4). Spearman ρ with disadvantage = **0.141** (p = 7.70e-12).

![Walk minutes by quartile](outputs/figures/chart_walk_min_by_quartile.png)

![30-minute transit access by quartile](outputs/figures/chart_30min_transit_by_quartile.png)

![Baseline walk-time map](outputs/figures/map_walk_min_venue.png)

### Prospective scenarios

Under **S2 (full announced 28×28)**, mean accessibility change is **0.0292** in Q1 vs **0.0283** in Q4 (Q4−Q1 = **-0.0009**). Spearman ρ(disadvantage, S2 Δ) = **-0.113** (p = 0.000). OLS of S2 Δ on the composite index: R² = **0.0000** (p = 0.889).

![S2 change map](outputs/figures/map_scenario_S2_delta.png)

![S2 delta by quartile](outputs/figures/chart_S2_delta_by_quartile.png)

![Scenario equity gaps](outputs/figures/chart_scenario_equity_gaps.png)

### Persistent deficits

![Q4 tracts outside 30-minute walk of venues](outputs/figures/map_access_deficit_Q4.png)

**Interpretation (placeholder):** Venue geography and existing rail already place many higher-disadvantage tracts nearer to Games destinations than affluent periphery tracts. Announced 28×28 **point-proxied** gains do not show a strong progressive tilt toward the most disadvantaged quartile—an honest null/weak prospective result that motivates earlier, multimodal scenario design in Brisbane.

---

## 4. Policy interpretation

1. **Underserved:** Q4 tracts outside 30-minute walk access (deficit map) warrant community investment and first/last-mile attention, not only venue-adjacent spectacle.  
2. **Equity leverage:** Prioritize 28×28 elements that raise access for Q4 in sensitivity runs (BRT/hubs over highway capacity where the metric is neighborhood access).  
3. **Do not equate proximity with benefit:** Highway projects and security footprints may impose burdens; see benefits/burdens memo.  
4. **Use before 2032:** Brisbane planners can run analogous scenarios **before** locking capital programs.

---

## 5. Limitations

Planned infrastructure may change; accessibility ≠ utilization; announcements incomplete; point proxies for corridors; walk detour factors pending OSM; displacement not modeled; community listening protocol not yet executed. Full list: `METHODOLOGY.md`.

---

## 6. Implications for Brisbane 2032 and Hickman

LA28 Equity Watch **identifies the pattern and proves the workflow**. It also exposes the gap: near-Games descriptive analysis is too late, and rail+detour methods are only a bridge to full multimodal routers and co-designed scenarios. Brisbane’s planning-stage window + Hickman expertise supply the second phase — see [`docs/RESEARCH_AGENDA_LA28_TO_BRISBANE.md`](docs/RESEARCH_AGENDA_LA28_TO_BRISBANE.md).

**Progression:** LA28 identified the problem → spatial analysis demonstrated the pattern → limitations exposed the need for prospective multimodal modeling → Brisbane provides the planning-stage environment → Hickman provides transport-accessibility depth → improved framework returns comparatively to LA28.

---

## Attribution

CalEnviroScreen 4.0 (OEHHA); HPI (Public Health Alliance / PHI via LA County Open Data); ACS & TIGER (U.S. Census Bureau); GTFS (LA Metro). Venues and 28×28 curated from public sources. Analysis: LA28 Equity Watch repository.
