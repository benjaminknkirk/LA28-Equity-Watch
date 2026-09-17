# Benefits, Burdens, and Community Input — LA28 Equity Watch

This document separates **what the quantitative model measures** from **what communities may experience**, and records a community-facing design that does **not** make the spatial model dependent on interviews.

## Benefits recognized in the quantitative model

| Benefit domain | How measured in this prototype | Investment types tagged |
| --- | --- | --- |
| Transit access | Walk / rail-network minutes to venues; 15/30/45-minute thresholds; scenario Δ accessibility from 28×28 points | rail, bus_brt, mobility_hub |
| Recreation / venue access | Network-adjusted walk minutes to competition venues | venues (competition) |
| Neighborhood connectivity | Proximity to active-transport and access projects | active_transport, access |
| Public capital investment (proxied) | Presence of geocoded Games-linked project points | all 28×28 categories |

## Burdens recognized (framework — not all modeled)

| Burden domain | Status in this prototype | Why it matters |
| --- | --- | --- |
| Displacement / affordability pressure | **Not modeled** numerically; flagged as limitation | Games-era investment can raise rents near corridors |
| Construction disruption | **Not modeled** | Temporary access loss during build |
| Congestion / security footprint | **Not modeled** | Games operations may reduce local accessibility |
| Policing / exclusion | **Not modeled** | Affects who can actually use “access” |
| Opportunity cost | Discussed in policy section | Dollars spent here vs community priorities elsewhere |

The Equity Watch **names both sides** so that “benefit maps” are not mistaken for net welfare. Brisbane / Hickman work should add at least one burden pathway (e.g., rent trajectory near opened stations) where data allow.

## Investment typology (geocoded inventory)

Each curated point carries a `category` / zone field:

- **Competition venues** — LA28 sports venues  
- **Training / village** — UCLA Olympic Village (and related housing)  
- **Transit projects** — rail extensions, BRT, bus-only lanes, grade separations  
- **Mobility hubs / access** — SFV hubs, Gateway Cities MCP, Eastside access  
- **Active transport / public realm** — Rail-to-Rail, LA River bike path  
- **Highway / corridor management** — I-5, I-105, I-405, SR 57/60 (Games-linked mobility, not “community benefit” by default)

Highway projects are retained for completeness of the announced program but interpreted cautiously in equity narrative (capacity expansion ≠ neighborhood accessibility).

## Community-facing component (design for author execution)

The quantitative pipeline runs without interviews. Parallel community input strengthens interpretation:

1. **Listening sessions** (2–3) in high-disadvantage / high-investment and high-disadvantage / low-access tracts (selected from quartile maps).  
2. **Stakeholder interviews** with community-based organizations near Exposition Park, Inglewood, Long Beach, and Eastside corridors.  
3. **Community review workshop** of draft maps: “Does this match how you experience access to venues and transit?”  
4. **Benefit definition check**: ask residents what “Olympic benefit” would mean locally (jobs, parks, safety, fares, housing)—feed into Brisbane survey design.

Outputs of community work: annotated map notes and a short appendix memo in `docs/community/` (to be added by the author; no fabricated quotes).

## Policy interpretation hooks

Use quartile comparison tables to flag:

- **Underserved:** high disadvantage + outside 30-minute walk/transit venue access + low S2 delta  
- **High investment, uncertain community benefit:** highway-classified 28×28 near vulnerable tracts  
- **High equity leverage:** projects that raise S2 access most for Q4 tracts in sensitivity runs  
