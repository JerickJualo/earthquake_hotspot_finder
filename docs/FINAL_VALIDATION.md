# Phase 10 Final Validation

**Validation date:** 2026-11-15  
**Development dataset:** USGS 2025 cleaned dataset  
**Status:** Application code validated; live PostgreSQL execution remains a local setup step

## Test matrix

| Area | Command/check | Result |
|---|---|---|
| Backend unit/integration suite | `backend/.venv/Scripts/python.exe -m pytest backend/tests -q` | 9 passed |
| Frontend tests | `cd frontend; npm.cmd test` | 5 passed in 2 files |
| Frontend production build | `cd frontend; npm.cmd run build` | Passed |
| Python compilation | `backend/.venv/Scripts/python.exe -m compileall -q backend/app` | Passed during Phase 7 validation |
| OpenAPI generation | FastAPI `GET /openapi.json` smoke check | HTTP 200; 8 paths |
| API integration | SQLite-seeded TestClient routes | Filters, event detail, summary, provinces, clusters, readiness, and 404 behavior passed |
| Formatting check | `git diff --check` | Passed |

The frontend browser-level smoke check was attempted, but native browser automation approval timed out before a window could be opened. No visual interaction result is claimed from that attempt. The executable frontend tests cover filter editing, submit/reset callbacks, loading-state controls, query serialization, successful API requests, and safe 503 propagation.

## Verified provisional earthquake statistics

The values below were recalculated from `backend/data/processed/cleaned_usgs_2025.csv` using the reusable `calculate_statistics` function. They are not copied from a report by assumption.

- Records: **794**
- UTC coverage: **2025-01-01T18:39:33.615000+00:00** through **2025-12-31T17:30:42.385000+00:00**
- Magnitude mean: **4.568**; median: **4.5**
- Depth mean: **61.742 km**
- Unique assigned provinces: **37**
- Geographic assignment counts: **120 assigned**, **652 offshore/unassigned**, **22 outside-study-scope candidates**
- Peak month: **2025-10**, with **234 records**
- Source names: **USGS** only
- Source network: **`us`** only
- Unique source event IDs: **794**

These are historical, provisional development statistics. They must be recalculated after PHIVOLCS is inspected and imported.

## Attribution and disclaimer review

- The source dataset is identified in the UI and documentation as the downloaded USGS 2025 development dataset.
- The geographic layer is identified as `geoBoundaries-PHL-ADM2.geojson` and described as ADM2/province-level input.
- The UI links to the USGS Earthquake Catalog, geoBoundaries, and PHIVOLCS websites.
- The UI states that the results do not predict earthquakes or measure hazard.
- The UI states that clusters are descriptive groupings, not rankings or final hazard conclusions.
- The dataset transition policy states that PHIVOLCS must be independently inspected and that USGS/PHIVOLCS records must not be automatically merged.

## Known release limitations

1. PostgreSQL credentials were not guessed or stored. Configure `.env`, run the migration, import the processed dataset, and call `/api/v1/system/ready` before claiming live database readiness.
2. The dashboard uses historical dataset-relative filters. It must not be described as current monitoring.
3. The map uses OpenStreetMap tiles for context and API-returned points; it is not a legal boundary or hazard map.
4. The USGS catalogue's original query parameters are not present in the downloaded CSV, so the observed magnitude/date coverage is documented as observed file coverage.
5. A final PHIVOLCS catalogue has not yet been imported; all current findings remain provisional.

## Release decision

The project is locally runnable and documented for development. The software workflow is ready for final-data replacement, but the research dataset and live PostgreSQL deployment are not yet finalised.
