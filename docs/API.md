# FastAPI API

Phase 7 provides a database-backed API for the provisional USGS development data. The API is source-independent: records are returned using the canonical database fields, while the original source name, source event ID, and import ID remain available for provenance.

## Start the backend

From the project root, with `.env` configured and the PostgreSQL schema/import available:

```powershell
uvicorn app.main:app --app-dir backend --reload
```

Interactive documentation is available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

The API can be imported and its OpenAPI document inspected before PostgreSQL is configured. Database-backed requests return HTTP 503 until the database connection and schema are ready.

## Endpoints

### `GET /api/v1/earthquakes`

Returns a paginated list of earthquake events.

Supported filters:

- `source_name`
- `import_id`
- `start_date` and `end_date` (`YYYY-MM-DD`; the end date is inclusive)
- `min_magnitude` and `max_magnitude`
- `min_depth_km` and `max_depth_km`
- `province_name`
- `geographic_assignment_status`
- `cluster_label` and optional `cluster_run_id`
- `page` (default `1`)
- `page_size` (default `50`, maximum `500`)

Example:

```text
GET /api/v1/earthquakes?start_date=2025-01-01&end_date=2025-12-31&min_magnitude=4&page_size=25
```

The response contains `data`, `page`, `page_size`, `total`, and `total_pages`.

### `GET /api/v1/earthquakes/{event_id}`

Returns one stored event by its internal database ID. A missing ID returns HTTP 404.

### `GET /api/v1/analytics/summary`

Applies the shared event filters and calculates descriptive statistics using the existing Python EDA service. The response includes record count, date range, numeric summaries, magnitude-type counts, geographic-assignment counts, assigned-province count, and monthly activity.

### `GET /api/v1/analytics/provinces`

Applies the shared event filters and returns earthquake counts for records with an assigned province. Events without a province are not fabricated into a province result.

### `GET /api/v1/analytics/clusters`

Applies the shared event filters, prepares valid geographic coordinates, and runs the reusable projected-coordinate K-Means service. It evaluates the requested K range and selects a supported K using the Phase 5 selection rules.

Additional query parameters:

- `min_k` (default `2`, range `2`–`12`)
- `max_k` (default `8`, range `2`–`12`)
- `include_assignments` (default `false`)

This endpoint performs an analysis request and does not write a cluster run or assignments to the database. Results are descriptive spatial groupings, not predictions or final hazard conclusions. Records excluded by the existing clustering eligibility rules are reported separately.

### `GET /api/v1/system/ready`

Executes a database connectivity check. It returns HTTP 200 when the database is reachable and HTTP 503 when it is unavailable or not yet configured.

The existing `GET /` and `GET /health` endpoints continue to report service-process status only; they do not replace the database readiness check.

## Error handling

- HTTP 404: requested event or filtered result does not exist.
- HTTP 422: invalid query values, reversed ranges, or an invalid clustering K range.
- HTTP 503: database operation failed or the database is unavailable.

Database errors intentionally return a generic message and do not expose passwords, connection strings, or driver details.

## Testing

Run the backend tests from the `backend` directory:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

The API tests use an isolated in-memory SQLite database. They do not modify the PostgreSQL database or the original downloaded datasets.

## Dataset status

The active USGS 2025 data remains provisional development data. When PHIVOLCS data becomes available, it must be independently inspected, mapped into the canonical schema, validated, and imported through the controlled replacement workflow described in [the dataset transition policy](DATASET_TRANSITION_POLICY.md). The API routes should continue to operate without source-specific assumptions.
