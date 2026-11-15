"""Run the Phase 3 development data pipeline."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from app.data_pipeline.cleaning import clean_usgs_data
from app.data_pipeline.geographic_processing import assign_adm2_provinces
from app.data_pipeline.loader import load_usgs_csv
from app.data_pipeline.validation import validate_usgs_frame


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_USGS = PROJECT_ROOT / "backend/data/raw/usgs/accurate_2025_usgs_dataset.csv"
DEFAULT_ADM2 = PROJECT_ROOT / "backend/data/boundaries/geoBoundaries-PHL-ADM2.geojson"
DEFAULT_OUTPUT = PROJECT_ROOT / "backend/data/processed"


def _markdown_report(
    *,
    usgs_path: Path,
    boundary_path: Path,
    source_validation: dict,
    cleaning_report: dict,
    geographic_report: dict,
    output_path: Path,
    output_rows: int,
    output_columns: int,
) -> str:
    return f"""# Phase 3 Data Quality Report

**Generated:** {datetime.now(timezone.utc).isoformat()}  
**Source dataset:** `{usgs_path.name}`  
**Boundary dataset:** `{boundary_path.name}`  
**Output:** `{output_path.name}`

## Source validation

- Input rows: **{source_validation['row_count']}**
- Input columns: **{source_validation['column_count']}**
- Event coverage (UTC): **{source_validation['event_date_min']}** to **{source_validation['event_date_max']}**
- Duplicate full rows: **{source_validation['duplicate_full_rows']}**
- Duplicate source event IDs: **{source_validation['duplicate_source_event_ids']}**
- Missing values: **{sum(source_validation['missing_value_counts'].values())}**
- Validation errors: **{', '.join(source_validation['validation_errors']) if source_validation['validation_errors'] else 'None'}**

## Cleaning decisions

- Rows retained: **{cleaning_report['retained_rows']}**
- Rows dropped: **{cleaning_report['dropped_rows']}**
- Invalid required-field rows: **{cleaning_report['invalid_required_field_rows']}**
- Non-Philippine location-label candidates: **{cleaning_report['non_philippines_label_rows']}**
- Decision: {cleaning_report['decision']}

## Canonical output

- Output rows: **{output_rows}**
- Output columns: **{output_columns}**
- Original source values: retained as `source__<column>` fields

## ADM2 geographic processing

- Boundary features: **{geographic_report['boundary_feature_count']}**
- Boundary administrative types: `{', '.join(geographic_report['boundary_shape_types'])}`
- Geometry types: `{', '.join(geographic_report['boundary_geometry_types'])}`
- Province-assigned rows: **{geographic_report['assigned_rows']}**
- Offshore/unassigned rows: **{geographic_report['unassigned_rows']}**
- Outside-study-scope candidates: **{geographic_report['outside_study_scope_candidates']}**
- Multiple polygon matches requiring review: **{geographic_report['multiple_polygon_matches']}**
- Structurally invalid rings observed: **{geographic_report['invalid_ring_count']}**
- Empty boundary features observed: **{geographic_report['empty_feature_count']}**
- Geographic policy: {geographic_report['policy']}

## Interpretation

This is a development-quality report for the current USGS dataset. It does not establish final research conclusions. PHIVOLCS data, when received, must be inspected independently and processed through the same source-independent pipeline.
"""


def run_pipeline(
    *,
    usgs_path: Path = DEFAULT_USGS,
    boundary_path: Path = DEFAULT_ADM2,
    output_dir: Path = DEFAULT_OUTPUT,
) -> tuple[Path, Path]:
    """Run loading, validation, cleaning, geographic processing, and export."""

    output_dir.mkdir(parents=True, exist_ok=True)
    import_id = "usgs-2025-development-v1"
    source_frame = load_usgs_csv(usgs_path)
    validation_report = validate_usgs_frame(source_frame)
    cleaned, cleaning_report = clean_usgs_data(
        source_frame, source_name="USGS", import_id=import_id
    )
    processed, geographic_report = assign_adm2_provinces(cleaned, boundary_path)

    output_csv = output_dir / "cleaned_usgs_2025.csv"
    output_report = output_dir / "DATA_QUALITY_REPORT.md"
    processed.to_csv(output_csv, index=False)
    output_report.write_text(
        _markdown_report(
            usgs_path=usgs_path,
            boundary_path=boundary_path,
            source_validation=validation_report,
            cleaning_report=cleaning_report,
            geographic_report=geographic_report,
            output_path=output_csv,
            output_rows=len(processed),
            output_columns=len(processed.columns),
        ),
        encoding="utf-8",
    )
    return output_csv, output_report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usgs", type=Path, default=DEFAULT_USGS)
    parser.add_argument("--boundaries", type=Path, default=DEFAULT_ADM2)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output_csv, output_report = run_pipeline(
        usgs_path=args.usgs,
        boundary_path=args.boundaries,
        output_dir=args.output_dir,
    )
    print(f"Created: {output_csv}")
    print(f"Created: {output_report}")


if __name__ == "__main__":
    main()
