"""Database-backed Python and scikit-learn analytics endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis.eda import calculate_statistics
from app.api.filters import EarthquakeFilterParams, earthquake_filters, filtered_event_query
from app.api.query_helpers import dataframe_records, events_to_frame
from app.api.schemas import (
    ClusterAnalysisResponse,
    ProvinceActivityResponse,
    SummaryResponse,
)
from app.database.connection import get_db
from app.database.models import EarthquakeEvent
from app.services.clustering_service import (
    evaluate_candidate_k,
    fit_kmeans,
    prepare_geographical_coordinates,
    select_k,
    summarize_clusters,
)


router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


def _all_filtered_events(session: Session, params: EarthquakeFilterParams) -> list[EarthquakeEvent]:
    return list(session.scalars(filtered_event_query(params)))


@router.get("/summary", response_model=SummaryResponse)
def summary(
    params: EarthquakeFilterParams = Depends(earthquake_filters),
    session: Session = Depends(get_db),
) -> SummaryResponse:
    events = _all_filtered_events(session, params)
    if not events:
        raise HTTPException(status_code=404, detail="No earthquake records match the filters")
    statistics = calculate_statistics(events_to_frame(events))
    return SummaryResponse.model_validate(statistics)


@router.get("/provinces", response_model=list[ProvinceActivityResponse])
def province_activity(
    params: EarthquakeFilterParams = Depends(earthquake_filters),
    session: Session = Depends(get_db),
) -> list[ProvinceActivityResponse]:
    events = _all_filtered_events(session, params)
    if not events:
        raise HTTPException(status_code=404, detail="No earthquake records match the filters")
    frame = events_to_frame(events)
    counts = (
        frame.loc[frame["province_name"].notna(), "province_name"]
        .value_counts()
        .rename_axis("province_name")
        .reset_index(name="earthquake_count")
    )
    return [ProvinceActivityResponse.model_validate(row) for row in dataframe_records(counts)]


@router.get("/clusters", response_model=ClusterAnalysisResponse)
def geographic_clusters(
    params: EarthquakeFilterParams = Depends(earthquake_filters),
    min_k: int = Query(2, ge=2, le=12),
    max_k: int = Query(8, ge=2, le=12),
    include_assignments: bool = Query(False),
    session: Session = Depends(get_db),
) -> ClusterAnalysisResponse:
    if min_k > max_k:
        raise HTTPException(status_code=422, detail="min_k must not exceed max_k")
    events = _all_filtered_events(session, params)
    if not events:
        raise HTTPException(status_code=404, detail="No earthquake records match the filters")
    frame = events_to_frame(events)
    try:
        prepared = prepare_geographical_coordinates(frame)
        evaluation = evaluate_candidate_k(prepared, k_values=range(min_k, max_k + 1))
        selected_k = select_k(evaluation)
        clustered, metadata = fit_kmeans(prepared, n_clusters=selected_k)
        summaries = summarize_clusters(clustered)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    assignments = None
    if include_assignments:
        assignments = dataframe_records(
            clustered.loc[
                clustered["cluster_label"].notna(),
                [
                    "event_id",
                    "source_event_id",
                    "cluster_label",
                    "latitude",
                    "longitude",
                    "occurred_at",
                    "magnitude",
                    "depth_km",
                    "province_name",
                    "geographic_assignment_status",
                ],
            ]
        )
    return ClusterAnalysisResponse(
        selected_k=selected_k,
        eligible_record_count=int(clustered["cluster_label"].notna().sum()),
        excluded_record_count=int(clustered["cluster_label"].isna().sum()),
        silhouette_score=metadata.get("silhouette_score"),
        evaluation=dataframe_records(evaluation),
        summaries=dataframe_records(summaries),
        assignments=assignments,
    )
