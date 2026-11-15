"""System and database readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.connection import get_db


router = APIRouter(prefix="/api/v1/system", tags=["system"])


@router.get("/ready")
def readiness(session: Session = Depends(get_db)) -> dict[str, str]:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database is not ready") from exc
    return {"service": "Earthquake Hotspot Finder API", "status": "ready", "database": "ok"}
