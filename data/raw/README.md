# Raw data

Files in this directory are downloaded by scripts under `src/acquire/`.
They are gitignored (reproducible via scripts). Do not edit by hand.

| Subfolder / file pattern | Source script | Notes |
| --- | --- | --- |
| `calenviroscreen/` | `src/acquire/fetch_calenviroscreen.py` | OEHHA CES 4.0 |
| `hpi/` | `src/acquire/fetch_hpi.py` | Requires `HPI_API_KEY` |
| `gtfs/` | `src/acquire/fetch_gtfs.py` | LA Metro bus + rail |
| `acs/` | `src/acquire/fetch_acs.py` | Requires `CENSUS_API_KEY` |
| `tiger/` | `src/acquire/fetch_tiger_tracts.py` | 2010 TIGER tracts (LA County) |

Curated Olympic / 28×28 CSVs live in `../curated/` (version-controlled).