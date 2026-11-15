"""FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.analytics import router as analytics_router
from app.api.routes.earthquakes import router as earthquakes_router
from app.api.routes.system import router as system_router
from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API for exploring provisional Philippine earthquake analytics.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(earthquakes_router)
app.include_router(analytics_router)
app.include_router(system_router)


@app.exception_handler(SQLAlchemyError)
def database_error_handler(_request: Request, _exc: SQLAlchemyError) -> JSONResponse:
    """Return a safe database error without exposing connection details."""

    return JSONResponse(
        status_code=503,
        content={"detail": "Database operation failed or the database is unavailable"},
    )


@app.get("/", tags=["system"])
def read_root() -> dict[str, str]:
    """Return a small service-identification response."""

    return {"service": settings.app_name, "status": "ready"}


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Confirm that the API process is running.

    Database connectivity will be checked by a dedicated readiness endpoint
    after the PostgreSQL schema is created in a later phase.
    """

    return {"service": settings.app_name, "status": "ok"}
