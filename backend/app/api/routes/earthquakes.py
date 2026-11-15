"""Earthquake record endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.filters import EarthquakeFilterParams, earthquake_filters, filtered_event_query
from app.api.query_helpers import event_response, fetch_events, total_pages
from app.api.schemas import EarthquakePage, EarthquakeResponse
from app.database.connection import get_db
from app.database.models import EarthquakeEvent


router = APIRouter(prefix="/api/v1/earthquakes", tags=["earthquakes"])


@router.get("", response_model=EarthquakePage)
def list_earthquakes(
    params: EarthquakeFilterParams = Depends(earthquake_filters),
    session: Session = Depends(get_db),
) -> EarthquakePage:
    events, total = fetch_events(session, params)
    return EarthquakePage(
        data=[event_response(event) for event in events],
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=total_pages(total, params.page_size),
    )


@router.get("/{event_id}", response_model=EarthquakeResponse)
def get_earthquake(event_id: int, session: Session = Depends(get_db)) -> EarthquakeResponse:
    event = session.scalar(
        select(EarthquakeEvent).where(EarthquakeEvent.event_id == event_id)
    )
    if event is None:
        raise HTTPException(status_code=404, detail="Earthquake event not found")
    return event_response(event)
