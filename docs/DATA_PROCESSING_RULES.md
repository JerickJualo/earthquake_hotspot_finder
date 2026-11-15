# Phase 3 Data Processing Rules

## Active development source

The active development import is `accurate_2025_usgs_dataset.csv`, identified by import reference `usgs-2025-development-v1`. The original CSV is read-only input and is never overwritten.

## Canonical schema

Source-specific fields are mapped into canonical fields in `backend/app/data_pipeline/schema.py`. Original USGS values are retained in the cleaned output as `source__<original_column>` fields for provenance. Namespacing avoids ambiguous duplicate column labels when an original column name is also a canonical field name. Future PHIVOLCS data must use a separate adapter and the same canonical fields.

## Validation

The pipeline checks required columns, missing values, timestamp parsing, numeric conversion, finite values, coordinate ranges, negative depths, duplicate complete rows, and duplicate source event IDs.

Invalid required fields are flagged. The pipeline does not silently replace missing values with zero.

## Geographic processing

- The ADM2 GeoJSON is processed as province-level data.
- Province assignment uses point-in-polygon ray casting against the original Polygon/MultiPolygon coordinates.
- No nearest-province fallback is used.
- Points that do not intersect a province remain `offshore_or_unassigned` when their source description identifies the Philippines.
- Records whose source location description does not identify the Philippines remain retained as `outside_study_scope_candidate` until the final geographic inclusion rule is approved.
- The raw boundary file is not simplified or overwritten.

## Output separation

- Raw inputs: `backend/data/raw/` and `backend/data/boundaries/`
- Processed development output: `backend/data/processed/cleaned_usgs_2025.csv`
- Data-quality report: `backend/data/processed/DATA_QUALITY_REPORT.md`

The processed output is a development artifact. It is not a final research dataset and must be regenerated when the source dataset, boundary dataset, or processing rules change.
