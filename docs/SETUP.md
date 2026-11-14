# Development Environment Setup

## Installed system tools

The workspace uses the following already-installed tools:

- Python 3.14.5
- Node.js 24.16.0
- npm 11.13.0
- PostgreSQL 18.4
- Git

## Python environment

The project-local virtual environment is:

```text
backend/.venv/
```

Its dependencies are listed in `backend/requirements.txt`. The environment contains the data-analysis, geospatial, machine-learning, FastAPI, SQLAlchemy, PostgreSQL, migration, and testing packages required by the approved architecture.

Activate it in PowerShell with:

```powershell
.\backend\.venv\Scripts\Activate.ps1
```

## Environment variables

Copy `.env.example` to `.env` at the project root. The file contains a placeholder PostgreSQL URL and local CORS configuration. `.env` is ignored by Git and must not contain credentials that are committed to the repository.

The backend reads:

- `APP_NAME`
- `APP_ENV`
- `BACKEND_HOST`
- `BACKEND_PORT`
- `DATABASE_URL`
- `ALLOWED_ORIGINS`

## Backend skeleton

The FastAPI entry point is `backend/app/main.py`. It exposes:

- `GET /` — service identification
- `GET /health` — process health check

The SQLAlchemy engine and session factory are configured in `backend/app/database/connection.py`. Creating the engine does not connect to PostgreSQL; actual database readiness will be added with the schema in a later phase.

Run the backend from the project root:

```powershell
uvicorn app.main:app --app-dir backend --reload
```

## Frontend skeleton

The Vite project is under `frontend/`. It contains a small React page that calls the backend health endpoint. React Leaflet, Recharts, and dashboard components will be installed and created only when those features are implemented.

Install frontend dependencies and start Vite with:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Create a production build with:

```powershell
npm.cmd run build
```

## Verification commands

Run backend tests:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests -q
```

Verify the frontend build:

```powershell
cd frontend
npm.cmd run build
```

