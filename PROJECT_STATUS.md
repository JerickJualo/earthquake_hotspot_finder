# Project Status

**Last updated:** 2026-11-15  
**Current phase:** Phase 2 — Environment and Project Setup complete  
**Frontend development:** Not started

## Current active datasets

- USGS: `backend/data/raw/usgs/accurate_2025_usgs_dataset.csv`
- Boundaries: `backend/data/boundaries/geoBoundaries-PHL-ADM2.geojson`
- Current audit reports: `docs/DATA_INSPECTION_REPORT_CURRENT.md` and `docs/DATA_DICTIONARY_CURRENT.md`

## Completed

- Created the initial backend, frontend, data, and documentation directories.
- Preserved the original USGS and geoBoundaries files in the workspace.
- Created a project-local Python virtual environment at `backend/.venv/`.
- Installed and verified the data-science, geospatial, backend, database, and testing dependencies.
- Inspected the USGS CSV structure and quality.
- Inspected the geoBoundaries file metadata, attributes, administrative level, geometry types, and extent.
- Created `docs/DATA_INSPECTION_REPORT.md`.
- Created `docs/DATA_DICTIONARY.md`.
- Created the FastAPI backend skeleton with `/` and `/health` endpoints.
- Created environment-driven PostgreSQL and CORS configuration.
- Created the React/Vite frontend skeleton and frontend API helper.
- Created `.env.example`, `README.md`, and `docs/SETUP.md`.
- Installed frontend dependencies and generated `frontend/package-lock.json`.
- Verified the backend test suite: 1 test passed.
- Verified the running backend health endpoint: HTTP 200.
- Verified the frontend production build: successful Vite build.

## Previous baseline audit findings

- The USGS dataset contains 612 records covering 2025.
- The USGS file has no missing values, duplicate complete rows, duplicate event IDs, invalid timestamps, or basic coordinate-range violations.
- All USGS location descriptions contain “Philippines,” but 227 coordinates lie east of the downloaded boundary layer's overall eastern extent. These should be treated as potential offshore events, not automatically discarded.
- The geoBoundaries file contains 17 `ADM1` features representing Philippine regions, not provinces.
- Provincial assignment and province ranking require an inspected ADM2/province boundary dataset.

## Current replacement-dataset findings

- The active USGS file contains 794 records covering 2025-01-01 through 2025-12-31 UTC.
- The active USGS file has no missing values, duplicate event IDs, invalid timestamps, or basic coordinate-range violations.
- 772 records mention the Philippines in the location description; 22 are labelled as Taiwan, Indonesia, or Malaysia.
- The active geoBoundaries file contains 86 ADM2 province features and is appropriate for province-level point-in-polygon assignment.
- Offshore events and nearby-country events must be handled through explicit, documented spatial-scope rules.

## Phase 2 result

The development environments are ready for the next implementation phase. PostgreSQL connection configuration exists, but the database schema, migrations, and data import are intentionally deferred until the data-processing rules are finalized.

## Jupyter Notebook decision

Jupyter Notebook is approved for effective and appropriate use in this project, especially for:

- Dataset inspection and exploratory data analysis
- Tables, charts, and geographic visual checks
- Testing analytical ideas on small, documented steps
- Beginner-friendly explanations of calculations and clustering
- Reproducible demonstrations using the cleaned development dataset

Reusable production logic should remain in Python modules or services. Notebooks should call those reusable functions rather than becoming the only location of data-cleaning or backend logic. Store notebooks in `backend/notebooks/`, keep raw files read-only, and clearly label generated figures and exploratory results.

## Current limitations and next actions

1. Complete a memory-conscious geometry validation/processing plan for the 444 MB ADM2 GeoJSON.
2. Define the configurable Philippine spatial scope and offshore-event policy.
3. Implement canonical schema mapping and data-quality flags.
4. Use a Jupyter Notebook for the first EDA once the spatial rules are documented.
5. Create the cleaned development dataset and proceed to database schema design.

