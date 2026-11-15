# Phase 6 Database Documentation

## Database design

The PostgreSQL schema keeps source imports, canonical earthquake events, and machine-learning runs logically separated:

| Table | Purpose |
|---|---|
| `dataset_imports` | One controlled source import, including source name, file hash, version, status, and row count. |
| `earthquake_events` | Canonical earthquake records, geographic assignment fields, validation flags, and namespaced raw-source payload. |
| `cluster_runs` | Reproducibility metadata for a K-Means run, including K, random seed, CRS, and evaluation score. |
| `earthquake_cluster_assignments` | Cluster labels per event and per clustering run. This prevents a future run from overwriting an earlier result. |

The event uniqueness rule is `(import_id, source_event_id)`. This prevents duplicates inside one import while allowing USGS and PHIVOLCS records to remain separate until a documented cross-source reconciliation is approved.

## Indexes

The schema indexes import status/source, event time, latitude/longitude, magnitude, depth, province, geographic assignment status, import ownership, clustering runs, and cluster labels. These support the planned time filters, geographic queries, province summaries, and cluster retrievals.

## Configure PostgreSQL

PostgreSQL must be running locally. The project confirmed that the local service is listening on port 5432, but credentials are intentionally not stored in the repository.

1. Copy `.env.example` to `.env`.
2. Replace `CHANGE_ME` in `DATABASE_URL` with the local PostgreSQL password.
3. Create the database if it does not exist:

   ```powershell
   createdb -h localhost -U postgres earthquake_hotspot_finder
   ```

Do not commit `.env` or place the password in source code, command history, or documentation.

## Apply the migration

From `backend/`:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

The migration is `backend/alembic/versions/0001_initial_schema.py`. Offline SQL can be inspected safely with:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head --sql
```

## Import processed data

The controlled importer defaults to the Phase 5 clustered development dataset:

```powershell
.\.venv\Scripts\python.exe -m app.database.import_processed
```

The importer:

- hashes the input file;
- creates one `dataset_imports` record;
- imports canonical fields and preserves original namespaced source values in `source_payload`;
- imports cluster-run metadata and event assignments when cluster columns are present;
- skips an identical successful import safely;
- refuses to replace an existing import unless `--replace-existing` is explicitly supplied;
- replaces only rows owned by the specified import ID inside one transaction.

For an intentional controlled replacement:

```powershell
.\.venv\Scripts\python.exe -m app.database.import_processed --replace-existing
```

## Verify stored data

```powershell
.\.venv\Scripts\python.exe -m app.database.verify_database
```

Verification checks all four tables, import status and row count, event count, cluster-run count, cluster-assignment count, and the expected indexes.

## Testing without PostgreSQL

The importer has an SQLite integration test covering schema creation, event import, cluster assignment import, provenance payloads, idempotent re-import, and duplicate protection. This does not replace the final PostgreSQL migration/import check; it allows safe development without embedding credentials.
