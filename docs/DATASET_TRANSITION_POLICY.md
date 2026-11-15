# Temporary Development Dataset and Final Dataset Transition Policy

**Status:** Authoritative project policy  
**Adopted:** 2026-11-15

## Purpose

The project will use the downloaded USGS 2025 earthquake dataset for development while the requested official PHIVOLCS earthquake catalogue is pending. PHIVOLCS is the preferred final research dataset, subject to independent inspection and verification when it becomes available.

## Development and research-data rules

1. Complete all technically possible software phases using the USGS 2025 dataset.
2. Do not delay development while waiting for PHIVOLCS.
3. Keep the data pipeline independent of source-specific column names and file formats.
4. Map every source into a canonical earthquake schema.
5. Preserve source names, source event identifiers, import references, and provenance.
6. Keep raw files, processed files, and database-import records logically separate.
7. Do not spread USGS-specific assumptions through analytics, clustering, API, database, or frontend code.
8. Keep original downloaded datasets unchanged.
9. Treat all USGS 2025 statistics, rankings, and clusters as provisional development results.
10. Do not present provisional development results as final research conclusions.

## PHIVOLCS onboarding procedure

When PHIVOLCS data becomes available:

1. Store the original PHIVOLCS file separately from USGS files.
2. Inspect its actual format, fields, coverage, missing values, identifiers, and quality independently.
3. Map its fields to the canonical schema without modifying the original file.
4. Preserve PHIVOLCS source identity and source-specific identifiers.
5. Compare PHIVOLCS and USGS coverage and identify possible duplicate events.
6. Do not automatically merge the providers.
7. Require an explicit, documented reconciliation decision before any combined analysis.

## Controlled replacement and re-import

Dataset replacement must be an explicit, repeatable operation:

1. Register the dataset version and source metadata.
2. Run schema validation, quality checks, and geographic validation.
3. Produce a reviewable processed dataset without overwriting raw input.
4. Import the selected dataset version using a controlled import reference.
5. Prevent duplicate imports through dataset and source-event identity checks.
6. Replace or isolate the development database records safely; do not mix incompatible source records by accident.
7. Rerun all data-dependent statistics, rankings, clustering, charts, API checks, and relevant tests.
8. Update the data dictionary, inspection report, project status, and research-result labels.

## Date-filter policy

The USGS development dataset covers historical 2025 records. It must not be presented as current real-world earthquake activity when the dataset has no corresponding recent records.

- Historical filters may operate within the actual dataset date range.
- “Recent” or “last N days” filters must be based on an explicitly configured dataset-relative reference date during development.
- Dataset-relative periods must be visibly labelled as dataset-relative.
- The application must not imply that provisional historical results are live monitoring or current earthquake activity.

## Architecture consequence

The canonical schema, source adapter, import reference, database records, analytics services, clustering services, API responses, and frontend labels must allow a USGS-to-PHIVOLCS transition with minimal code changes. Dataset-derived findings must remain separate from software functionality and system-level documentation.
