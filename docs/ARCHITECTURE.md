# Earthquake Hotspot Finder Architecture

## Purpose and scope

Earthquake Hotspot Finder is a local analytical application for exploring earthquake records. It is not an earthquake prediction, recurrence, risk, or live-alert system. The current development view uses the downloaded USGS 2025 catalogue and geoBoundaries Philippines ADM2 polygons. Those results are provisional until the preferred PHIVOLCS catalogue is independently inspected and imported.

## System flow

```text
Raw USGS CSV + raw geoBoundaries ADM2 GeoJSON
                 |
                 v
        Source-independent data pipeline
        load -> validate -> clean -> assign ADM2 status
                 |
                 v
     Canonical cleaned/clustered development CSV
                 |
                 v
   Controlled SQLAlchemy/Alembic database import
                 |
                 v
 PostgreSQL: imports -> earthquake events -> cluster runs/assignments
                 |
                 v
 FastAPI: filters -> database queries -> EDA/K-Means analytics
                 |
                 v
 React/Vite: shared filters -> Leaflet map + Recharts + tables/cards
```

The original downloaded files are read-only inputs. Raw, processed, and imported records are kept logically separate. A dataset import stores the source name, source filename, SHA-256 hash, version, status, and row count. Events retain their source event IDs and source payload fields.

## Backend structure

- `backend/app/data_pipeline/`: source loading, validation, canonical mapping, cleaning, and ADM2 point-in-polygon assignment.
- `backend/app/analysis/`: reusable descriptive statistics and EDA output generation.
- `backend/app/services/clustering_service.py`: projected-coordinate preparation, K-Means, evaluation, and summaries.
- `backend/app/database/`: SQLAlchemy models, database connection, Alembic migration, controlled import, and verification commands.
- `backend/app/api/`: shared filter parsing, response schemas, query helpers, earthquake routes, analytics routes, and readiness route.
- `backend/tests/`: pipeline, clustering, database, and FastAPI route tests. API tests use isolated SQLite and do not touch production PostgreSQL.

The API has these main routes:

- `GET /health`: process health only.
- `GET /api/v1/system/ready`: database readiness.
- `GET /api/v1/earthquakes` and `/api/v1/earthquakes/{event_id}`: filtered event records.
- `GET /api/v1/analytics/summary`: Python EDA statistics.
- `GET /api/v1/analytics/provinces`: province activity counts.
- `GET /api/v1/analytics/clusters`: on-demand scikit-learn K-Means analysis.

All analytics routes use the same validated filter dependency. K-Means requests do not write results to the database; persisted cluster-run tables are available for controlled database workflows.

## Frontend structure

- `frontend/src/App.jsx`: dashboard composition, shared filter state, loading/error states, Leaflet map, Recharts charts, rankings, source references, and disclaimers.
- `frontend/src/services/api.js`: one API client with shared query serialization and safe error propagation.
- `frontend/src/style.css`: responsive dashboard styling and Leaflet/Recharts integration styles.
- `frontend/src/App.test.jsx`: filter control interaction tests.
- `frontend/src/services/api.test.js`: query serialization, endpoint request, and database-error tests.

The React app uses one `appliedFilters` object for every dashboard request. Editing controls changes draft state; applying filters copies that state into `appliedFilters`; reset restores the dataset-relative 2025 default range. Empty optional values are omitted from query strings.

Leaflet uses OpenStreetMap tiles for geographic context and plots only coordinates returned by FastAPI. The map is not a political boundary or hazard map. Recharts renders distributions returned by the backend, avoiding client-side recomputation from a paginated sample.

## Data and scientific safeguards

- USGS 2025 statistics, rankings, and clusters are labelled provisional development results.
- The historical dataset is not presented as current real-world activity.
- ADM2 assignment is point-in-polygon only; no nearest-province fallback is silently applied.
- Offshore/unassigned and outside-scope candidates retain explicit statuses.
- Cluster labels are identifiers, not hazard rankings. K-Means uses geographic coordinates, not a prediction model.
- USGS and PHIVOLCS records are not automatically merged.
- PHIVOLCS onboarding requires independent inspection, canonical mapping, validation, controlled import, and rerunning data-dependent analyses.
- The UI includes source references for USGS, geoBoundaries, and PHIVOLCS, and a scientific disclaimer.

## Local configuration and execution

1. Copy the root `.env.example` to `.env` and configure PostgreSQL locally. Never commit `.env`.
2. From the project root, run `uvicorn app.main:app --app-dir backend --reload`.
3. From `frontend/`, run `npm.cmd run dev`.
4. If FastAPI is not on `http://localhost:8000`, copy `frontend/.env.example` to `frontend/.env` and set `VITE_API_BASE_URL`.
5. Run the controlled migration/import commands documented in [DATABASE.md](DATABASE.md).

The application can be built and its frontend/API tests can run without live PostgreSQL. Database-backed dashboard data requires a configured PostgreSQL schema and imported records.
