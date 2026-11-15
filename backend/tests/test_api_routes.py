from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base, get_db
from app.database.models import DatasetImport, EarthquakeEvent
from app.main import app


def _seed_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    now = datetime.now(timezone.utc)
    with factory() as session:
        session.add(
            DatasetImport(
                import_id="test-import",
                source_name="USGS",
                source_filename="test.csv",
                source_sha256="a" * 64,
                dataset_version="test",
                status="success",
                row_count=6,
                started_at=now,
                completed_at=now,
                created_at=now,
            )
        )
        for index, (latitude, longitude, province, status, magnitude) in enumerate(
            [
                (10.0, 120.0, "Test Province", "assigned", 4.0),
                (10.2, 120.2, "Test Province", "assigned", 4.5),
                (20.0, 125.0, "North Province", "assigned", 5.0),
                (20.2, 125.2, "North Province", "assigned", 5.2),
                (11.0, 126.0, None, "offshore_or_unassigned", 4.2),
                (21.0, 127.0, None, "outside_study_scope_candidate", 4.1),
            ],
            start=1,
        ):
            session.add(
                EarthquakeEvent(
                    import_id="test-import",
                    source_name="USGS",
                    source_event_id=f"event-{index}",
                    occurred_at=datetime(2025, 1, index, tzinfo=timezone.utc),
                    latitude=latitude,
                    longitude=longitude,
                    depth_km=10.0 + index,
                    magnitude=magnitude,
                    magnitude_type="mb",
                    province_name=province,
                    geographic_assignment_status=status,
                    source_place_is_philippines_label=status != "outside_study_scope_candidate",
                    record_validation_status="valid_required_fields",
                    source_payload={"id": f"event-{index}"},
                    created_at=now,
                )
            )
        session.commit()
    return engine, factory


def test_api_filters_and_analytics():
    engine, factory = _seed_session()

    def override_get_db():
        with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    try:
        response = client.get(
            "/api/v1/earthquakes",
            params={"min_magnitude": 4.5, "page_size": 2},
        )
        assert response.status_code == 200
        assert response.json()["total"] == 3
        assert len(response.json()["data"]) == 2

        detail = client.get("/api/v1/earthquakes/1")
        assert detail.status_code == 200
        assert detail.json()["source_event_id"] == "event-1"

        summary = client.get("/api/v1/analytics/summary", params={"import_id": "test-import"})
        assert summary.status_code == 200
        assert summary.json()["record_count"] == 6

        provinces = client.get("/api/v1/analytics/provinces")
        assert provinces.status_code == 200
        assert provinces.json()[0]["province_name"] == "Test Province"

        clusters = client.get(
            "/api/v1/analytics/clusters",
            params={"min_k": 2, "max_k": 3, "include_assignments": True},
        )
        assert clusters.status_code == 200
        assert clusters.json()["eligible_record_count"] == 5
        assert clusters.json()["excluded_record_count"] == 1
        assert clusters.json()["assignments"]

        ready = client.get("/api/v1/system/ready")
        assert ready.status_code == 200
        assert ready.json()["database"] == "ok"

        missing = client.get("/api/v1/earthquakes/9999")
        assert missing.status_code == 404
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
