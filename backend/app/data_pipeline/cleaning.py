"""Cleaning and canonical transformation orchestration."""

from __future__ import annotations

import pandas as pd

from app.data_pipeline.schema import transform_usgs_to_canonical
from app.data_pipeline.validation import invalid_row_mask


def clean_usgs_data(
    source_frame: pd.DataFrame,
    *,
    source_name: str,
    import_id: str,
) -> tuple[pd.DataFrame, dict]:
    """Transform USGS rows while retaining valid and reviewable records.

    Non-Philippine and offshore records are not silently removed. They receive
    geographic status flags and remain available for review.
    """

    cleaned = transform_usgs_to_canonical(
        source_frame, source_name=source_name, import_id=import_id
    )
    invalid = invalid_row_mask(source_frame)
    cleaned["record_validation_status"] = invalid.map(
        {True: "invalid_required_fields", False: "valid_required_fields"}
    )
    cleaned["record_validation_reason"] = ""
    cleaned.loc[invalid, "record_validation_reason"] = (
        "Missing/invalid source ID, timestamp, or coordinate"
    )
    cleaned["geographic_assignment_status"] = cleaned[
        "source_place_is_philippines_label"
    ].map(
        {
            True: "candidate_philippines_unassigned",
            False: "outside_study_scope_candidate",
        }
    )
    cleaned["analysis_inclusion_status"] = "retained_for_review"
    return cleaned, {
        "input_rows": int(len(source_frame)),
        "invalid_required_field_rows": int(invalid.sum()),
        "retained_rows": int(len(cleaned)),
        "dropped_rows": 0,
        "non_philippines_label_rows": int(
            (~cleaned["source_place_is_philippines_label"]).sum()
        ),
        "decision": "Retain all source rows; use explicit status flags instead of silent deletion.",
    }
