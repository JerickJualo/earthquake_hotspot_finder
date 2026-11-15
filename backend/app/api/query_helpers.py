"""Database query and serialization helpers for API routes."""

from __future__ import annotations

import math

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.filters import EarthquakeFilterParams, filter_conditions, filtered_event_query
from app.api.schemas import EarthquakeResponse
from app.database.models import EarthquakeEvent


def fetch_events(
    session: Session, params: EarthquakeFilterParams
) -> tuple[list[EarthquakeEvent], int]:
    conditions = filter_conditions(params)
    total = int(
        session.scalar(
            select(func.count(EarthquakeEvent.event_id)).where(*conditions)
        )
        or 0
    )
    query = (
        filtered_event_query(params)
        .order_by(EarthquakeEvent.occurred_at.desc(), EarthquakeEvent.event_id.desc())
        .offset((params.page - 1) * params.page_size)
        .limit(params.page_size)
    )
    return list(session.scalars(query)), total


def event_response(event: EarthquakeEvent) -> EarthquakeResponse:
    return EarthquakeResponse.model_validate(event)


def events_to_frame(events: list[EarthquakeEvent]) -> pd.DataFrame:
    rows = [
        {
            "event_id": event.event_id,
            "source_event_id": event.source_event_id,
            "occurred_at": event.occurred_at,
            "latitude": event.latitude,
            "longitude": event.longitude,
            "depth_km": event.depth_km,
            "magnitude": event.magnitude,
            "magnitude_type": event.magnitude_type,
            "province_name": event.province_name,
            "province_id": event.province_id,
            "geographic_assignment_status": event.geographic_assignment_status,
        }
        for event in events
    ]
    return pd.DataFrame(rows)


def dataframe_records(frame: pd.DataFrame) -> list[dict]:
    """Convert pandas/numpy values to JSON-safe Python values."""

    records = frame.astype(object).where(pd.notna(frame), None).to_dict(orient="records")
    safe_records: list[dict] = []
    for record in records:
        safe_record = {}
        for key, value in record.items():
            if hasattr(value, "item"):
                value = value.item()
            safe_record[key] = value
        safe_records.append(safe_record)
    return safe_records


def total_pages(total: int, page_size: int) -> int:
    return math.ceil(total / page_size) if total else 0
