"""Validation checks for source earthquake records."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd


REQUIRED_USGS_COLUMNS = {
    "time",
    "latitude",
    "longitude",
    "depth",
    "mag",
    "id",
    "place",
}


def _numeric_invalid_count(frame: pd.DataFrame, column: str) -> int:
    converted = pd.to_numeric(frame[column], errors="coerce")
    nonmissing = frame[column].notna()
    return int((nonmissing & converted.isna()).sum()) + int(
        np.isinf(converted.dropna().to_numpy()).sum()
    )


def validate_usgs_frame(frame: pd.DataFrame) -> dict:
    """Return a serializable quality report without mutating ``frame``."""

    missing_columns = sorted(REQUIRED_USGS_COLUMNS.difference(frame.columns))
    report = {
        "row_count": int(len(frame)),
        "column_count": int(len(frame.columns)),
        "columns": list(frame.columns),
        "missing_required_columns": missing_columns,
        "missing_value_counts": {
            column: int(count)
            for column, count in frame.isna().sum().items()
            if int(count) > 0
        },
        "duplicate_full_rows": int(frame.duplicated().sum()),
        "duplicate_source_event_ids": 0,
        "invalid_timestamp_counts": {},
        "event_date_min": None,
        "event_date_max": None,
        "invalid_numeric_counts": {},
        "invalid_coordinate_counts": {},
        "negative_depth_count": 0,
        "validation_errors": [],
    }

    if "id" in frame.columns:
        report["duplicate_source_event_ids"] = int(
            frame.loc[frame["id"].notna(), "id"].duplicated().sum()
        )

    for column in ["time", "updated"]:
        if column in frame.columns:
            parsed = pd.to_datetime(frame[column], errors="coerce", utc=True)
            report["invalid_timestamp_counts"][column] = int(parsed.isna().sum())
            if column == "time" and parsed.notna().any():
                report["event_date_min"] = parsed.min().isoformat()
                report["event_date_max"] = parsed.max().isoformat()

    for column in [
        "latitude",
        "longitude",
        "depth",
        "mag",
        "nst",
        "gap",
        "dmin",
        "rms",
        "horizontalError",
        "depthError",
        "magError",
        "magNst",
    ]:
        if column in frame.columns:
            report["invalid_numeric_counts"][column] = _numeric_invalid_count(
                frame, column
            )

    if "latitude" in frame.columns:
        latitude = pd.to_numeric(frame["latitude"], errors="coerce")
        report["invalid_coordinate_counts"]["latitude_out_of_range"] = int(
            (latitude.notna() & ~latitude.between(-90, 90)).sum()
        )
    if "longitude" in frame.columns:
        longitude = pd.to_numeric(frame["longitude"], errors="coerce")
        report["invalid_coordinate_counts"]["longitude_out_of_range"] = int(
            (longitude.notna() & ~longitude.between(-180, 180)).sum()
        )
    if "latitude" in frame.columns and "longitude" in frame.columns:
        latitude = pd.to_numeric(frame["latitude"], errors="coerce")
        longitude = pd.to_numeric(frame["longitude"], errors="coerce")
        report["invalid_coordinate_counts"]["missing_coordinate_pair"] = int(
            (latitude.isna() | longitude.isna()).sum()
        )
    if "depth" in frame.columns:
        depth = pd.to_numeric(frame["depth"], errors="coerce")
        report["negative_depth_count"] = int((depth.notna() & (depth < 0)).sum())

    if missing_columns:
        report["validation_errors"].append("Missing required source columns")
    if report["duplicate_source_event_ids"]:
        report["validation_errors"].append("Duplicate source event identifiers")
    if report["duplicate_full_rows"]:
        report["validation_errors"].append("Duplicate complete rows")
    if any(report["invalid_timestamp_counts"].values()):
        report["validation_errors"].append("Invalid timestamps")
    if any(report["invalid_numeric_counts"].values()):
        report["validation_errors"].append("Invalid numeric values")
    if any(report["invalid_coordinate_counts"].values()):
        report["validation_errors"].append("Invalid coordinate values")
    if report["negative_depth_count"]:
        report["validation_errors"].append("Negative depth values")

    return report


def invalid_row_mask(frame: pd.DataFrame) -> pd.Series:
    """Return rows that cannot be safely represented as canonical points."""

    latitude = pd.to_numeric(frame["latitude"], errors="coerce")
    longitude = pd.to_numeric(frame["longitude"], errors="coerce")
    occurred_at = pd.to_datetime(frame["time"], errors="coerce", utc=True)
    source_id_missing = frame["id"].isna() | frame["id"].astype("string").eq("")

    return (
        latitude.isna()
        | longitude.isna()
        | ~latitude.between(-90, 90)
        | ~longitude.between(-180, 180)
        | occurred_at.isna()
        | source_id_missing
    )
