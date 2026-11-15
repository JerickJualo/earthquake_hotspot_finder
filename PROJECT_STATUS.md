# Project Status

**Last updated:** 2026-11-15  
**Current phase:** Phase 5 — Machine Learning complete  
**Frontend development:** Not started

## Authoritative dataset policy

The USGS 2025 dataset is the provisional development dataset. Development should continue using it while the PHIVOLCS catalogue request is pending. PHIVOLCS is the preferred final research dataset, subject to independent inspection and validation when received.

The project must preserve raw files, processed datasets, database imports, source names, source event IDs, and dataset provenance. It must use a canonical source-independent earthquake schema, avoid automatic USGS/PHIVOLCS merging, and provide a controlled replacement and re-import procedure. USGS-derived statistics, rankings, and K-Means clusters must be labelled provisional development results rather than final research conclusions.

See [DATASET_TRANSITION_POLICY.md](docs/DATASET_TRANSITION_POLICY.md) for the complete policy.

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
- Implemented source-independent canonical schema mapping with preserved `source__...` raw fields.
- Implemented USGS loading, validation, cleaning, provenance, and explicit quality flags.
- Implemented memory-conscious streaming ADM2 Polygon/MultiPolygon province assignment for the 444 MB boundary file.
- Generated the cleaned development dataset and Phase 3 quality report.
- Added data-pipeline unit tests; all 3 tests pass.
- Added JupyterLab and Matplotlib to the project environment for reproducible EDA.
- Created and executed the Phase 4 EDA notebook with descriptive statistics and six figures.
- Documented EDA methods, findings, and interpretation limitations.
- Implemented reusable projected-coordinate geographical K-Means service.
- Evaluated K=2 through K=8 with inertia, silhouette, Calinski-Harabasz, and Davies-Bouldin metrics.
- Generated cluster labels, summaries, metadata, visualizations, and clustering documentation.
- Added clustering edge-case tests.

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

## Phase 3 result

The Phase 3 pipeline is operational. Run it from `backend/` with:

```powershell
.\.venv\Scripts\python.exe -m app.data_pipeline.run_pipeline
```

The generated development artifacts are:

- `backend/data/processed/cleaned_usgs_2025.csv`
- `backend/data/processed/DATA_QUALITY_REPORT.md`

The current run retained all 794 source records, found no required-field validation failures, assigned 120 records to 37 ADM2 provinces, marked 652 Philippine-labelled records as offshore/unassigned, and retained 22 nearby-country candidates for explicit review. These are provisional development-data results, not final research conclusions.

## Phase 4 result

The EDA is complete for the current USGS development dataset. It reports basic numeric summaries, magnitude and depth distributions, monthly activity, coordinate distribution, geographic assignment status, and province-level activity. The October 2025 count is the highest monthly count at 234 records; this descriptive result must not be interpreted as a forecast or a final hazard conclusion.

Artifacts:

- `backend/notebooks/phase4_eda_usgs_2025.ipynb`
- `docs/EDA_METHODS.md`
- `docs/eda/EDA_FINDINGS.md`
- `docs/eda/statistics/`
- `docs/eda/figures/`

## Phase 5 result

The clustering service is operational. The default run uses 772 in-scope records, excludes 22 nearby-country candidates by explicit status, selects K=2 using the highest silhouette score (0.6716), and writes the clustered development output and evaluation artifacts. Cluster labels describe geographic partitions only; they are not hotspot rankings or predictions.

Artifacts:

- `backend/app/services/clustering_service.py`
- `backend/data/processed/clustered_usgs_2025.csv`
- `docs/CLUSTERING_METHODS.md`
- `docs/clustering/CLUSTERING_FINDINGS.md`
- `docs/clustering/cluster_evaluation.csv`
- `docs/clustering/cluster_summaries.csv`
- `docs/clustering/figures/`

## Phase 2 result

The development environments are ready for the next implementation phase. PostgreSQL connection configuration exists, but the database schema, migrations, and data import are intentionally deferred until the data-processing rules are finalized.

## Dataset transition requirements to carry into later phases

- Build source adapters and canonical schema mapping rather than hardcoding USGS columns.
- Add dataset version/import references and duplicate-protection checks.
- Keep a controlled dataset replacement path for PHIVOLCS.
- Support historical dataset-relative date filters during development and label them clearly.
- Rerun analyses, clustering, API checks, frontend data checks, and relevant tests after final-data import.

## Jupyter Notebook decision

Jupyter Notebook is approved for effective and appropriate use in this project, especially for:

- Dataset inspection and exploratory data analysis
- Tables, charts, and geographic visual checks
- Testing analytical ideas on small, documented steps
- Beginner-friendly explanations of calculations and clustering
- Reproducible demonstrations using the cleaned development dataset

Reusable production logic should remain in Python modules or services. Notebooks should call those reusable functions rather than becoming the only location of data-cleaning or backend logic. Store notebooks in `backend/notebooks/`, keep raw files read-only, and clearly label generated figures and exploratory results.

## Current limitations and next actions

1. Finalize the configurable Philippine spatial scope and offshore-event inclusion policy with the research requirements.
2. Create the PostgreSQL schema and controlled import process using the canonical fields and provenance identifiers.
3. Add PHIVOLCS as a separately inspected source adapter when the catalogue becomes available.

