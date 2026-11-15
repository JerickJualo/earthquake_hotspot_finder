import pandas as pd
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.database.connection import Base
from app.database.import_service import import_processed_dataset
from app.database.models import (
    ClusterRun,
    DatasetImport,
    EarthquakeClusterAssignment,
    EarthquakeEvent,
)


def test_controlled_processed_import_and_idempotency(tmp_path):
    csv_path = tmp_path / "clustered.csv"
    metadata_path = tmp_path / "cluster_metadata.json"
    pd.DataFrame(
        {
            "source_event_id": ["event-a", "event-b", "event-c"],
            "occurred_at": [
                "2025-01-01T00:00:00Z",
                "2025-01-02T00:00:00Z",
                "2025-01-03T00:00:00Z",
            ],
            "source_updated_at": [None, None, None],
            "latitude": [10.0, 10.2, 20.0],
            "longitude": [120.0, 120.2, 125.0],
            "depth_km": [10.0, 20.0, 30.0],
            "magnitude": [4.0, 4.1, 4.2],
            "magnitude_type": ["mb", "mb", "mb"],
            "province_name": ["A", "A", None],
            "geographic_assignment_status": [
                "assigned",
                "assigned",
                "offshore_or_unassigned",
            ],
            "cluster_label": [0, 0, None],
            "cluster_assignment_status": ["assigned", "assigned", "excluded"],
            "projected_x_m": [1.0, 2.0, None],
            "projected_y_m": [3.0, 4.0, None],
            "source__id": ["event-a", "event-b", "event-c"],
        }
    ).to_csv(csv_path, index=False)
    metadata_path.write_text(
        '{"selected_k": 1, "projected_crs": "test", "fit": {"random_state": 42, "silhouette_score": 0.5}}',
        encoding="utf-8",
    )

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        result = import_processed_dataset(
            session,
            csv_path,
            import_id="test-import",
            cluster_metadata_path=metadata_path,
        )
        assert result["status"] == "imported"
        assert result["row_count"] == 3
        assert result["cluster_assignment_count"] == 2
        assert session.scalar(select(func.count()).select_from(EarthquakeEvent)) == 3
        assert session.scalar(select(func.count()).select_from(ClusterRun)) == 1
        assert (
            session.scalar(select(func.count()).select_from(EarthquakeClusterAssignment))
            == 2
        )

        second = import_processed_dataset(
            session,
            csv_path,
            import_id="test-import",
            cluster_metadata_path=metadata_path,
        )
        assert second["status"] == "skipped_existing_identical_import"

        imported = session.get(DatasetImport, "test-import")
        assert imported is not None
        assert imported.status == "success"
