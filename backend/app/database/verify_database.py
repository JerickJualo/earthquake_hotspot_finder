"""Verify the current imported dataset and key database indexes."""

from __future__ import annotations

import argparse

from sqlalchemy import func, inspect, select

from app.core.config import settings
from app.database.connection import SessionLocal, engine
from app.database.models import (
    ClusterRun,
    DatasetImport,
    EarthquakeClusterAssignment,
    EarthquakeEvent,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--import-id", default="usgs-2025-development-v1")
    args = parser.parse_args()
    settings.require_configured_database_url()
    inspector = inspect(engine)
    required_tables = {
        "dataset_imports",
        "earthquake_events",
        "cluster_runs",
        "earthquake_cluster_assignments",
    }
    actual_tables = set(inspector.get_table_names())
    missing_tables = sorted(required_tables.difference(actual_tables))
    if missing_tables:
        raise RuntimeError(f"Missing database tables: {', '.join(missing_tables)}")

    with SessionLocal() as session:
        dataset_import = session.get(DatasetImport, args.import_id)
        if dataset_import is None:
            raise RuntimeError(f"Import ID not found: {args.import_id}")
        event_count = session.scalar(
            select(func.count()).select_from(EarthquakeEvent).where(
                EarthquakeEvent.import_id == args.import_id
            )
        )
        cluster_runs = session.scalar(
            select(func.count()).select_from(ClusterRun).where(
                ClusterRun.import_id == args.import_id
            )
        )
        assignment_count = session.scalar(
            select(func.count())
            .select_from(EarthquakeClusterAssignment)
            .join(ClusterRun)
            .where(ClusterRun.import_id == args.import_id)
        )
        print(
            {
                "tables_verified": sorted(required_tables),
                "import_status": dataset_import.status,
                "import_row_count": dataset_import.row_count,
                "event_count": int(event_count or 0),
                "cluster_run_count": int(cluster_runs or 0),
                "cluster_assignment_count": int(assignment_count or 0),
                "indexes": {
                    table: [index["name"] for index in inspector.get_indexes(table)]
                    for table in sorted(required_tables)
                },
            }
        )


if __name__ == "__main__":
    main()
