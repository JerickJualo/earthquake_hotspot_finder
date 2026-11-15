"""SQLAlchemy models for provenance-safe earthquake storage."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class DatasetImport(Base):
    """One controlled import of one source dataset version."""

    __tablename__ = "dataset_imports"

    import_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    source_name: Mapped[str] = mapped_column(String(80), nullable=False)
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    dataset_version: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="running")
    row_count: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    events: Mapped[list["EarthquakeEvent"]] = relationship(
        back_populates="dataset_import", cascade="all, delete-orphan"
    )
    cluster_runs: Mapped[list["ClusterRun"]] = relationship(
        back_populates="dataset_import", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_dataset_imports_source_name", "source_name"),
        Index("ix_dataset_imports_status", "status"),
    )


class EarthquakeEvent(Base):
    """Canonical earthquake record with source provenance and quality flags."""

    __tablename__ = "earthquake_events"

    event_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    import_id: Mapped[str] = mapped_column(
        String(120), ForeignKey("dataset_imports.import_id", ondelete="CASCADE"), nullable=False
    )
    source_name: Mapped[str] = mapped_column(String(80), nullable=False)
    source_event_id: Mapped[str] = mapped_column(String(160), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    depth_km: Mapped[float | None] = mapped_column(Float)
    magnitude: Mapped[float | None] = mapped_column(Float)
    magnitude_type: Mapped[str | None] = mapped_column(String(30))
    location_description: Mapped[str | None] = mapped_column(Text)
    event_type: Mapped[str | None] = mapped_column(String(60))
    review_status: Mapped[str | None] = mapped_column(String(40))
    source_network: Mapped[str | None] = mapped_column(String(40))
    location_source: Mapped[str | None] = mapped_column(String(40))
    magnitude_source: Mapped[str | None] = mapped_column(String(40))
    station_count: Mapped[float | None] = mapped_column(Float)
    azimuthal_gap: Mapped[float | None] = mapped_column(Float)
    distance_to_nearest_station: Mapped[float | None] = mapped_column(Float)
    rms_residual: Mapped[float | None] = mapped_column(Float)
    horizontal_error: Mapped[float | None] = mapped_column(Float)
    depth_error: Mapped[float | None] = mapped_column(Float)
    magnitude_error: Mapped[float | None] = mapped_column(Float)
    magnitude_station_count: Mapped[float | None] = mapped_column(Float)
    province_name: Mapped[str | None] = mapped_column(String(120))
    province_id: Mapped[str | None] = mapped_column(String(160))
    region: Mapped[str | None] = mapped_column(String(120))
    island_group: Mapped[str | None] = mapped_column(String(80))
    geographic_assignment_status: Mapped[str | None] = mapped_column(String(50))
    source_place_is_philippines_label: Mapped[bool | None] = mapped_column(Boolean)
    record_validation_status: Mapped[str | None] = mapped_column(String(50))
    record_validation_reason: Mapped[str | None] = mapped_column(Text)
    source_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    dataset_import: Mapped[DatasetImport] = relationship(back_populates="events")
    cluster_assignments: Mapped[list["EarthquakeClusterAssignment"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "import_id", "source_event_id", name="uq_earthquake_events_import_source_id"
        ),
        Index("ix_earthquake_events_occurred_at", "occurred_at"),
        Index("ix_earthquake_events_latitude_longitude", "latitude", "longitude"),
        Index("ix_earthquake_events_magnitude", "magnitude"),
        Index("ix_earthquake_events_depth_km", "depth_km"),
        Index("ix_earthquake_events_province_name", "province_name"),
        Index("ix_earthquake_events_geographic_status", "geographic_assignment_status"),
        Index("ix_earthquake_events_import_id", "import_id"),
    )


class ClusterRun(Base):
    """Metadata for one reproducible clustering execution."""

    __tablename__ = "cluster_runs"

    cluster_run_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    import_id: Mapped[str] = mapped_column(
        String(120), ForeignKey("dataset_imports.import_id", ondelete="CASCADE"), nullable=False
    )
    algorithm: Mapped[str] = mapped_column(String(60), nullable=False)
    n_clusters: Mapped[int] = mapped_column(Integer, nullable=False)
    random_state: Mapped[int | None] = mapped_column(Integer)
    silhouette_score: Mapped[float | None] = mapped_column(Float)
    projected_crs: Mapped[str | None] = mapped_column(Text)
    configuration: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    dataset_import: Mapped[DatasetImport] = relationship(back_populates="cluster_runs")
    assignments: Mapped[list["EarthquakeClusterAssignment"]] = relationship(
        back_populates="cluster_run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_cluster_runs_import_id", "import_id"),
        Index("ix_cluster_runs_algorithm", "algorithm"),
    )


class EarthquakeClusterAssignment(Base):
    """A cluster label attached to an event for one specific run."""

    __tablename__ = "earthquake_cluster_assignments"

    cluster_run_id: Mapped[str] = mapped_column(
        String(160), ForeignKey("cluster_runs.cluster_run_id", ondelete="CASCADE"), primary_key=True
    )
    event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("earthquake_events.event_id", ondelete="CASCADE"), primary_key=True
    )
    cluster_label: Mapped[int] = mapped_column(Integer, nullable=False)
    projected_x_m: Mapped[float | None] = mapped_column(Float)
    projected_y_m: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    cluster_run: Mapped[ClusterRun] = relationship(back_populates="assignments")
    event: Mapped[EarthquakeEvent] = relationship(back_populates="cluster_assignments")

    __table_args__ = (
        Index(
            "ix_cluster_assignments_run_label",
            "cluster_run_id",
            "cluster_label",
        ),
        Index("ix_cluster_assignments_event_id", "event_id"),
    )
