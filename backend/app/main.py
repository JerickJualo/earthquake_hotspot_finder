"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Backend skeleton for the Philippine earthquake analytics system.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
