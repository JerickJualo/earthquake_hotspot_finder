# Earthquake Hotspot Finder

A web-based geospatial analytics system for exploring Philippine earthquake records. The project uses a Python/FastAPI backend and a React/Vite frontend. It is an analytical application, not an earthquake prediction system.

## Current status

Phase 1 dataset auditing is complete. The active datasets are documented in:

- `docs/DATA_INSPECTION_REPORT_CURRENT.md`
- `docs/DATA_DICTIONARY_CURRENT.md`

Phase 2 now provides a minimal backend, frontend, local environment configuration, and development verification commands.

## Technology foundation

- Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL
- Pandas, NumPy, GeoPandas, Shapely, PyProj, scikit-learn
- React, Vite, JavaScript

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

The database engine configuration is present, but schema creation and data import belong to later phases. The current health endpoint verifies only that the API process is running.
