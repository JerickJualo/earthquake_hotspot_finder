"""Controlled import of processed earthquake data into PostgreSQL."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    ClusterRun,
    DatasetImport,
    EarthquakeClusterAssignment,
    EarthquakeEvent,
)


CANONICAL_EVENT_FIELDS = {
    "source_name",
    "source_event_id",
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
    "record_validation_status",
    "record_validation_reason",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _value(row: pd.Series, column: str) -> Any:
    value = row.get(column)
    if value is None or pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if hasattr(value, "item"):
        return value.item()
    return value


def _payload(row: pd.Series) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for column in row.index:
        if not str(column).startswith("source__"):
            continue
        value = _value(row, column)
        if isinstance(value, datetime):
            value = value.isoformat()
        payload[str(column)[len("source__") :]] = value
    return payload


def _load_frame(input_path: Path) -> pd.DataFrame:
    if not input_path.exists():
        raise FileNotFoundError(f"Processed dataset not found: {input_path}")
    frame = pd.read_csv(input_path)
    required = {"source_event_id", "occurred_at", "latitude", "longitude"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Processed dataset is missing required columns: {', '.join(missing)}")
    frame["occurred_at"] = pd.to_datetime(frame["occurred_at"], errors="coerce", utc=True)
    frame["source_updated_at"] = pd.to_datetime(
        frame.get("source_updated_at"), errors="coerce", utc=True
    )
    if frame["source_event_id"].isna().any() or frame["source_event_id"].duplicated().any():
        raise ValueError("Processed dataset contains missing or duplicate source_event_id values")
    if frame["occurred_at"].isna().any():
        raise ValueError("Processed dataset contains invalid occurred_at values")
    return frame


def import_processed_dataset(
    session: Session,
    input_path: Path,
    *,
    import_id: str,
    source_name: str = "USGS",
    dataset_version: str = "2025-development",
    replace_existing: bool = False,
    cluster_metadata_path: Path | None = None,
) -> dict[str, Any]:
    """Import one processed dataset in a transaction.

    Existing successful imports are skipped when replacement is not explicitly
    requested. Replacement deletes only records owned by the same import ID.
    """

    frame = _load_frame(input_path)
    source_hash = sha256_file(input_path)
    existing = session.get(DatasetImport, import_id)
    if existing is not None:
        if not replace_existing and existing.source_sha256 == source_hash and existing.status == "success":
            return {
                "status": "skipped_existing_identical_import",
                "import_id": import_id,
                "row_count": int(existing.row_count or 0),
            }
        if not replace_existing:
            raise ValueError(
                f"Import ID {import_id!r} already exists. Use replace_existing=True for a controlled replacement."
            )
        session.delete(existing)
        session.flush()

    now = datetime.now(timezone.utc)
    dataset_import = DatasetImport(
        import_id=import_id,
        source_name=source_name,
        source_filename=input_path.name,
        source_sha256=source_hash,
        dataset_version=dataset_version,
        status="running",
        row_count=None,
        started_at=now,
        created_at=now,
        notes="Controlled import of the Phase 3 processed development dataset.",
    )
    session.add(dataset_import)

    event_objects: list[EarthquakeEvent] = []
    for _, row in frame.iterrows():
        event_objects.append(
            EarthquakeEvent(
                import_id=import_id,
                source_name=source_name,
                source_event_id=str(_value(row, "source_event_id")),
                occurred_at=_value(row, "occurred_at"),
                source_updated_at=_value(row, "source_updated_at"),
                latitude=float(_value(row, "latitude")),
                longitude=float(_value(row, "longitude")),
                depth_km=_value(row, "depth_km"),
                magnitude=_value(row, "magnitude"),
                magnitude_type=_value(row, "magnitude_type"),
                location_description=_value(row, "location_description"),
                event_type=_value(row, "event_type"),
                review_status=_value(row, "review_status"),
                source_network=_value(row, "source_network"),
                location_source=_value(row, "location_source"),
                magnitude_source=_value(row, "magnitude_source"),
                station_count=_value(row, "station_count"),
                azimuthal_gap=_value(row, "azimuthal_gap"),
                distance_to_nearest_station=_value(row, "distance_to_nearest_station"),
                rms_residual=_value(row, "rms_residual"),
                horizontal_error=_value(row, "horizontal_error"),
                depth_error=_value(row, "depth_error"),
                magnitude_error=_value(row, "magnitude_error"),
                magnitude_station_count=_value(row, "magnitude_station_count"),
                province_name=_value(row, "province_name"),
                province_id=_value(row, "province_id"),
                region=_value(row, "region"),
                island_group=_value(row, "island_group"),
                geographic_assignment_status=_value(row, "geographic_assignment_status"),
                source_place_is_philippines_label=_value(
                    row, "source_place_is_philippines_label"
                ),
                record_validation_status=_value(row, "record_validation_status"),
                record_validation_reason=_value(row, "record_validation_reason"),
                source_payload=_payload(row),
                created_at=now,
            )
        )
    session.add_all(event_objects)
    session.flush()
    event_by_source_id = {event.source_event_id: event for event in event_objects}

    cluster_run = None
    assignment_count = 0
    if "cluster_label" in frame.columns:
        metadata = {}
        if cluster_metadata_path is not None and cluster_metadata_path.exists():
            metadata = json.loads(cluster_metadata_path.read_text(encoding="utf-8"))
        fit = metadata.get("fit", {})
        selected_k = metadata.get("selected_k")
        if selected_k is None:
            labels = pd.to_numeric(frame["cluster_label"], errors="coerce").dropna()
            selected_k = int(labels.nunique()) if not labels.empty else 0
        cluster_run_id = f"{import_id}-k{int(selected_k)}-rs{int(fit.get('random_state', 42))}"
        cluster_run = ClusterRun(
            cluster_run_id=cluster_run_id,
            import_id=import_id,
            algorithm="KMeans",
            n_clusters=int(selected_k),
            random_state=int(fit.get("random_state", 42)),
            silhouette_score=fit.get("silhouette_score"),
            projected_crs=metadata.get("projected_crs"),
            configuration=metadata,
            created_at=now,
        )
        session.add(cluster_run)
        session.flush()
        assignments: list[EarthquakeClusterAssignment] = []
        for _, row in frame.iterrows():
            label = _value(row, "cluster_label")
            if label is None or _value(row, "cluster_assignment_status") != "assigned":
                continue
            event = event_by_source_id[str(_value(row, "source_event_id"))]
            assignments.append(
                EarthquakeClusterAssignment(
                    cluster_run_id=cluster_run.cluster_run_id,
                    event_id=event.event_id,
                    cluster_label=int(label),
                    projected_x_m=_value(row, "projected_x_m"),
                    projected_y_m=_value(row, "projected_y_m"),
                    created_at=now,
                )
            )
        session.add_all(assignments)
        assignment_count = len(assignments)

    dataset_import.row_count = len(event_objects)
    dataset_import.status = "success"
    dataset_import.completed_at = datetime.now(timezone.utc)
    session.commit()
    return {
        "status": "imported",
        "import_id": import_id,
        "row_count": len(event_objects),
        "cluster_run_id": cluster_run.cluster_run_id if cluster_run else None,
        "cluster_assignment_count": assignment_count,
    }
