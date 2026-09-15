# Mapping Access to Olympic Investment Across Los Angeles

**LA28 Equity Watch — Research Brief (draft)**  
**Author:** Benjamin Kirk  

> Draft findings language is generated from pipeline outputs for structure only. Rewrite before citation or Fulbright submission.

---

## 1. Motivation

Los Angeles will host the 2028 Olympic and Paralympic Games amid a large portfolio of transit and venue-adjacent investments, including Metro’s Twenty-Eight by ’28 program. A recurring equity question in Olympic planning is whether legacy infrastructure improves access for historically disadvantaged communities or concentrates benefits near already well-connected places.

This prototype builds a **reproducible, tract-level proximity analysis** for Los Angeles County as a methodological pilot for a Fulbright research design comparing LA28 with Brisbane 2032.

---

## 2. Data & Methods

See the full documentation in [`METHODOLOGY.md`](METHODOLOGY.md). In brief:

- **Unit:** 2010 census tracts in Los Angeles County (n=2346; CES-complete n=2297).
- **Disadvantage:** CalEnviroScreen 4.0 (primary) and Healthy Places Index 3.0 (validation; inverted).
- **Investments:** Curated LA28 venue points (n=34) and Metro 28×28 representative points (n=28).
- **Baseline transit:** Nearest Metro rail stop (n=463).
- **Accessibility change:** ΔA = A(min(d_stop, d_28)) − A(d_stop) where A(d)=1/(1+d) and distances are kilometers (EPSG:3310).

Manual curation was required for venues and 28×28 coordinates; automated sources were used for CES, HPI (LA County open data), ACS 2019, TIGER tracts, and GTFS.

---

## 3. Findings

### Primary map

![CalEnviroScreen choropleth with LA28 venues and 28×28 points](outputs/figures/choropleth_ces_investments.png)

### Accessibility change vs disadvantage

Spearman correlation between **CES county disadvantage decile** and **accessibility change** is **ρ = -0.093** (p = 7.56e-06). The association is **weak and negative**: more burdened deciles do not show systematically larger proximity gains under the 28×28 point-proxy model.

An OLS regression of accessibility change on statewide CES percentile yields **R² = 0.0000** (p = 0.936) — effectively a **null linear relationship**.

![Mean accessibility change by CES decile](outputs/figures/access_change_by_decile.png)

![Scatter: accessibility change vs CES percentile](outputs/figures/scatter_access_vs_ces.png)

About **36.8%** of tracts have a 28×28 representative point closer than their nearest rail stop (mean ΔA = 0.033).

### Venue proximity

Spearman correlation between CES disadvantage decile and **venue access** is **ρ = 0.196** (p = 2.92e-21): higher-burden tracts tend to be **closer** to curated LA28 venues on average. That pattern is visible in median venue distance by decile.

![Median venue distance by CES decile](outputs/figures/venue_distance_by_decile.png)

### HPI validation

Using inverted HPI disadvantage deciles, Spearman ρ with accessibility change is **-0.067** (p = 0.001), directionally consistent with the weak CES result.

**Interpretation (placeholder for author rewrite):** Under this proximity specification, planned 28×28 points do **not** show a strong progressive targeting pattern toward the most CalEnviroScreen-burdened tracts. Venue geography, however, overlaps more with higher-burden areas. Neither result should be over-read as a welfare or ridership conclusion.

---

## 4. Limitations

- Point proxies for corridor projects; Euclidean distance ≠ travel time.
- No Games Enhanced Transit System (GETS) / shuttle network modeled.
- Manual geocoding of venues and 28×28 points.
- CES/HPI measure baseline community conditions, not Olympic impacts.
- Rail-only baseline; bus proximity excluded by design.
- Full limitations list: [`METHODOLOGY.md`](METHODOLOGY.md).

---

## 5. Implications for Olympic legacy measurement (toward Brisbane 2032)

A defensible comparative framework needs (1) a consistent disadvantage index or carefully documented crosswalk, (2) investment inventories with transparent geometry (lines vs points), and (3) pre-registered accessibility metrics that can return **null or adverse** results. This LA County prototype shows that a transparent proximity pipeline is buildable with public data, and that honest null/weak associations are informative for equity claims about Olympic-era investment.

Next methodological steps for a Brisbane comparison include travel-time matrices, dollar-weighted investment surfaces, and difference-in-differences designs around project opening dates.

---

## Attribution

CalEnviroScreen 4.0 © California OEHHA. Healthy Places Index © Public Health Alliance of Southern California / PHI (via LA County Open Data). ACS and TIGER © U.S. Census Bureau. GTFS © LA Metro. Venue list compiled from public Wikipedia/LA28 materials; 28×28 list from Metro Board Report 2023-0756. Analysis code: LA28 Equity Watch repository.
