"""Pydantic response schemas for the public API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class EarthquakeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: int
    import_id: str
    source_name: str
    source_event_id: str
    occurred_at: datetime
    source_updated_at: datetime | None = None
    latitude: float
    longitude: float
    depth_km: float | None = None
    magnitude: float | None = None
    magnitude_type: str | None = None
    location_description: str | None = None
    province_name: str | None = None
    province_id: str | None = None
    geographic_assignment_status: str | None = None
    record_validation_status: str | None = None


class EarthquakePage(BaseModel):
    data: list[EarthquakeResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class ProvinceActivityResponse(BaseModel):
    province_name: str
    earthquake_count: int


class SummaryResponse(BaseModel):
    record_count: int
    date_min_utc: str | None
    date_max_utc: str | None
    numeric_summary: dict[str, dict[str, Any]]
    magnitude_type_counts: dict[str, int]
    geographic_assignment_counts: dict[str, int]
    assigned_province_count: int
    monthly_activity: list[dict[str, Any]]
    province_activity: list[dict[str, Any]]
    magnitude_distribution: list[dict[str, Any]]
    depth_distribution: list[dict[str, Any]]


class ClusterAnalysisResponse(BaseModel):
    selected_k: int
    eligible_record_count: int
    excluded_record_count: int
    silhouette_score: float | None
    evaluation: list[dict[str, Any]]
    summaries: list[dict[str, Any]]
    assignments: list[dict[str, Any]] | None = None
