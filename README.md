# Earthquake Hotspot Finder

A web-based geospatial analytics system for exploring Philippine earthquake records. The project uses a Python/FastAPI backend and a React/Vite frontend. It is an analytical application, not an earthquake prediction system.

## Current status

Phase 1 dataset auditing is complete. The active datasets are documented in:

- `docs/DATA_INSPECTION_REPORT_CURRENT.md`
- `docs/DATA_DICTIONARY_CURRENT.md`

Phase 2 now provides a minimal backend, frontend, local environment configuration, and development verification commands.

Phase 3 now provides the source-independent data pipeline, canonical mapping, validation, cleaning, streaming ADM2 province assignment, cleaned development output, and a data-quality report.

Phase 4 now provides a reproducible Jupyter EDA notebook, descriptive statistics, six exploratory figures, and documented interpretation limits. The results are provisional USGS development findings.

Phase 5 now provides a reusable geographical K-Means service, projected-coordinate preparation, candidate-K evaluation, cluster summaries, edge-case tests, and cluster visualizations. The clusters are descriptive spatial groupings, not predictions or final hazard conclusions.

Phase 6 now provides the PostgreSQL schema, Alembic migration, SQLAlchemy models, controlled processed-data importer, indexes, and verification command. PostgreSQL credentials remain local-only in `.env`.

Phase 7 now provides database-backed FastAPI endpoints for earthquake records, shared filtering, descriptive summaries, province activity, on-demand K-Means analysis, readiness checks, safe error handling, and backend tests. See [the API documentation](docs/API.md).

Phase 8 now provides the responsive React dashboard: shared filters, summary cards, server-derived charts, coordinate map, cluster summaries, provincial rankings, source references, and scientific disclaimers.

Phase 9 now connects the dashboard to FastAPI through one shared filter state, uses Leaflet for the geographic view and Recharts for analytical charts, and verifies the frontend production integration. Copy `frontend/.env.example` to `frontend/.env` only when the API is running at a non-default URL.

The current USGS 2025 data is provisional development data. The planned transition to the preferred PHIVOLCS research dataset is governed by [the dataset transition policy](docs/DATASET_TRANSITION_POLICY.md). The application must keep source provenance, canonical schema mapping, raw/processed/imported data separation, and controlled dataset replacement independent of any one provider.

## Technology foundation

- Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL
- Pandas, NumPy, GeoPandas, Shapely, PyProj, scikit-learn
- React, Vite, JavaScript, Leaflet, React-Leaflet, Recharts

## Local setup

1. Copy `.env.example` to `.env`.
2. Replace `CHANGE_ME` in `DATABASE_URL` with the local PostgreSQL password. Do not commit `.env`.
3. Activate the backend environment:

   ```powershell
   .\backend\.venv\Scripts\Activate.ps1
   ```

4. Start the backend from the project root:

   ```powershell
   uvicorn app.main:app --app-dir backend --reload
   ```

5. In a second terminal, start the frontend:

   ```powershell
   cd frontend
   npm.cmd run dev
   ```

   The frontend defaults to `http://localhost:8000` for FastAPI. Copy `frontend/.env.example` to `frontend/.env` and change `VITE_API_BASE_URL` only when using another backend URL.

6. Open the Vite URL shown in the terminal. The starter page checks `http://localhost:8000/health`.

## Verification

Backend tests:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests -q
```

Backend health endpoint:

```text
http://localhost:8000/health
```

Frontend production build:

```powershell
cd frontend
npm.cmd run build
```

Run the Phase 3 data pipeline from the backend directory:

```powershell
cd backend
.\\.venv\\Scripts\\python.exe -m app.data_pipeline.run_pipeline
```

The pipeline reads the active raw USGS and ADM2 files without modifying them and writes the cleaned development dataset and quality report under `backend/data/processed/`. See [the processing rules](docs/DATA_PROCESSING_RULES.md) for the decisions and replacement-data expectations.

Run Phase 4 EDA from the backend directory:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.analysis.run_eda
```

See [EDA methods](docs/EDA_METHODS.md), [EDA findings](docs/eda/EDA_FINDINGS.md), and the [Jupyter notebook](backend/notebooks/phase4_eda_usgs_2025.ipynb).

Run Phase 5 clustering from the backend directory:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.services.run_clustering
```

See [clustering methods](docs/CLUSTERING_METHODS.md) and [clustering findings](docs/clustering/CLUSTERING_FINDINGS.md).

See [database documentation](docs/DATABASE.md) for migration, import, replacement, and verification commands.

See [API documentation](docs/API.md) for endpoint parameters, response behavior, error handling, and API test commands.

The database schema, migration, and import commands are implemented. Live PostgreSQL execution remains a local setup step until `.env` contains the user's PostgreSQL password. `/health` verifies that the API process is running; `/api/v1/system/ready` verifies database readiness.
