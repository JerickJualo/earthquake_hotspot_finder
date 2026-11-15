"""Canonical schema and source-column mappings."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd


USGS_COLUMN_MAP: Mapping[str, str] = {
    "time": "occurred_at",
    "latitude": "latitude",
    "longitude": "longitude",
    "depth": "depth_km",
    "mag": "magnitude",
    "magType": "magnitude_type",
    "id": "source_event_id",
    "updated": "source_updated_at",
    "place": "location_description",
    "type": "event_type",
    "status": "review_status",
    "net": "source_network",
    "locationSource": "location_source",
    "magSource": "magnitude_source",
    "nst": "station_count",
    "gap": "azimuthal_gap",
    "dmin": "distance_to_nearest_station",
    "rms": "rms_residual",
    "horizontalError": "horizontal_error",
    "depthError": "depth_error",
    "magError": "magnitude_error",
    "magNst": "magnitude_station_count",
}

CANONICAL_COLUMNS = [
    "source_name",
    "source_event_id",
    "import_id",
    "occurred_at",
    "source_updated_at",
    "latitude",
    "longitude",
    "depth_km",
    "magnitude",
    "magnitude_type",
    "location_description",
    "event_type",
    "review_status",
    "source_network",
    "location_source",
    "magnitude_source",
    "station_count",
    "azimuthal_gap",
    "distance_to_nearest_station",
    "rms_residual",
    "horizontal_error",
    "depth_error",
    "magnitude_error",
    "magnitude_station_count",
    "province_name",
    "province_id",
    "region",
    "island_group",
    "geographic_assignment_status",
    "source_place_is_philippines_label",
]


def transform_usgs_to_canonical(
    source_frame: pd.DataFrame,
    *,
    source_name: str,
    import_id: str,
) -> pd.DataFrame:
    """Create canonical fields while retaining every original source column."""

    frame = source_frame.copy()
    canonical = pd.DataFrame(index=frame.index)

    for source_column, canonical_column in USGS_COLUMN_MAP.items():
        if source_column not in frame.columns:
            canonical[canonical_column] = pd.NA
        else:
            canonical[canonical_column] = frame[source_column]

    canonical["source_name"] = source_name
    canonical["import_id"] = import_id
    canonical["source_event_id"] = canonical["source_event_id"].astype("string")
    canonical["occurred_at"] = pd.to_datetime(
        canonical["occurred_at"], errors="coerce", utc=True
    )
    canonical["source_updated_at"] = pd.to_datetime(
        canonical["source_updated_at"], errors="coerce", utc=True
    )

    canonical["province_name"] = pd.Series(pd.NA, index=frame.index, dtype="string")
    canonical["province_id"] = pd.Series(pd.NA, index=frame.index, dtype="string")
    canonical["region"] = pd.Series(pd.NA, index=frame.index, dtype="string")
    canonical["island_group"] = pd.Series(pd.NA, index=frame.index, dtype="string")
    canonical["geographic_assignment_status"] = "unassigned"
    canonical["source_place_is_philippines_label"] = (
        canonical["location_description"]
        .fillna("")
        .astype("string")
        .str.contains("Philippines", case=False, regex=False)
    )

    for column in [
        "latitude",
        "longitude",
        "depth_km",
        "magnitude",
    ]:
        canonical[column] = pd.to_numeric(canonical[column], errors="coerce")

    # Keep canonical fields first, followed by namespaced raw source columns.
    # Namespacing prevents duplicate labels such as canonical ``latitude`` and
    # the original USGS ``latitude`` from becoming ambiguous in pandas.
    raw_frame = frame.rename(columns={column: f"source__{column}" for column in frame.columns})
    return pd.concat([canonical[CANONICAL_COLUMNS], raw_frame], axis=1)
