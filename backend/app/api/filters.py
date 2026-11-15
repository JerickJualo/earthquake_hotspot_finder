"""Shared API filter parsing and SQLAlchemy condition construction."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException, Query
from sqlalchemy import Select, and_, select
from sqlalchemy.sql.elements import ColumnElement

from app.database.models import EarthquakeClusterAssignment, EarthquakeEvent


class EarthquakeFilterParams:
    """Validated filters shared by event and analytics endpoints."""

    def __init__(
        self,
        *,
        source_name: str | None = None,
        import_id: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        min_magnitude: float | None = None,
        max_magnitude: float | None = None,
        min_depth_km: float | None = None,
        max_depth_km: float | None = None,
        province_name: str | None = None,
        geographic_assignment_status: str | None = None,
        cluster_label: int | None = None,
        cluster_run_id: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> None:
        if start_date and end_date and start_date > end_date:
            raise HTTPException(status_code=422, detail="start_date must not be after end_date")
        if min_magnitude is not None and max_magnitude is not None and min_magnitude > max_magnitude:
            raise HTTPException(status_code=422, detail="min_magnitude must not exceed max_magnitude")
        if min_depth_km is not None and max_depth_km is not None and min_depth_km > max_depth_km:
            raise HTTPException(status_code=422, detail="min_depth_km must not exceed max_depth_km")
        self.source_name = source_name
        self.import_id = import_id
        self.start_date = start_date
        self.end_date = end_date
        self.min_magnitude = min_magnitude
        self.max_magnitude = max_magnitude
        self.min_depth_km = min_depth_km
        self.max_depth_km = max_depth_km
        self.province_name = province_name
        self.geographic_assignment_status = geographic_assignment_status
        self.cluster_label = cluster_label
        self.cluster_run_id = cluster_run_id
        self.page = page
        self.page_size = page_size


def earthquake_filters(
    source_name: str | None = Query(None),
    import_id: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    min_magnitude: float | None = Query(None, ge=-10, le=20),
    max_magnitude: float | None = Query(None, ge=-10, le=20),
    min_depth_km: float | None = Query(None, ge=0),
    max_depth_km: float | None = Query(None, ge=0, le=10000),
    province_name: str | None = Query(None),
    geographic_assignment_status: str | None = Query(None),
    cluster_label: int | None = Query(None, ge=0),
    cluster_run_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> EarthquakeFilterParams:
    return EarthquakeFilterParams(
        source_name=source_name,
        import_id=import_id,
        start_date=start_date,
        end_date=end_date,
        min_magnitude=min_magnitude,
        max_magnitude=max_magnitude,
        min_depth_km=min_depth_km,
        max_depth_km=max_depth_km,
        province_name=province_name,
        geographic_assignment_status=geographic_assignment_status,
        cluster_label=cluster_label,
        cluster_run_id=cluster_run_id,
        page=page,
        page_size=page_size,
    )


def filter_conditions(params: EarthquakeFilterParams) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = []
    if params.source_name:
        conditions.append(EarthquakeEvent.source_name == params.source_name)
    if params.import_id:
        conditions.append(EarthquakeEvent.import_id == params.import_id)
    if params.start_date:
        start = datetime.combine(params.start_date, time.min, tzinfo=timezone.utc)
        conditions.append(EarthquakeEvent.occurred_at >= start)
    if params.end_date:
        end_exclusive = datetime.combine(
            params.end_date + timedelta(days=1), time.min, tzinfo=timezone.utc
        )
        conditions.append(EarthquakeEvent.occurred_at < end_exclusive)
    if params.min_magnitude is not None:
        conditions.append(EarthquakeEvent.magnitude >= params.min_magnitude)
    if params.max_magnitude is not None:
        conditions.append(EarthquakeEvent.magnitude <= params.max_magnitude)
    if params.min_depth_km is not None:
        conditions.append(EarthquakeEvent.depth_km >= params.min_depth_km)
    if params.max_depth_km is not None:
        conditions.append(EarthquakeEvent.depth_km <= params.max_depth_km)
    if params.province_name:
        conditions.append(EarthquakeEvent.province_name == params.province_name)
    if params.geographic_assignment_status:
        conditions.append(
            EarthquakeEvent.geographic_assignment_status
            == params.geographic_assignment_status
        )
    if params.cluster_label is not None:
        assignment_query = select(EarthquakeClusterAssignment.event_id).where(
            EarthquakeClusterAssignment.event_id == EarthquakeEvent.event_id,
            EarthquakeClusterAssignment.cluster_label == params.cluster_label,
        )
        if params.cluster_run_id:
            assignment_query = assignment_query.where(
                EarthquakeClusterAssignment.cluster_run_id == params.cluster_run_id
            )
        conditions.append(assignment_query.exists())
    return conditions


def filtered_event_query(params: EarthquakeFilterParams) -> Select:
    conditions = filter_conditions(params)
    query = select(EarthquakeEvent)
    return query.where(and_(*conditions)) if conditions else query
