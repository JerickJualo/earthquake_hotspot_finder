import json

import pandas as pd

from app.data_pipeline.cleaning import clean_usgs_data
from app.data_pipeline.geographic_processing import assign_adm2_provinces
from app.data_pipeline.schema import transform_usgs_to_canonical
from app.data_pipeline.validation import validate_usgs_frame


def _source_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": ["2025-01-01T00:00:00.000Z", "2025-01-02T00:00:00.000Z"],
            "latitude": [10.0, 20.0],
            "longitude": [120.0, 130.0],
            "depth": [10.0, 20.0],
            "mag": [4.0, 5.0],
            "magType": ["mb", "mb"],
            "id": ["event-a", "event-b"],
            "updated": ["2025-01-01T01:00:00.000Z", "2025-01-02T01:00:00.000Z"],
            "place": ["10 km east of Test, Philippines", "100 km west of Test"],
            "type": ["earthquake", "earthquake"],
            "status": ["reviewed", "reviewed"],
            "net": ["us", "us"],
            "locationSource": ["us", "us"],
            "magSource": ["us", "us"],
        }
    )


def test_validation_and_canonical_mapping():
    source = _source_frame()
    report = validate_usgs_frame(source)
    assert report["row_count"] == 2
    assert report["validation_errors"] == []

    canonical = transform_usgs_to_canonical(
        source, source_name="USGS", import_id="test-import"
    )
    assert canonical.loc[0, "source_event_id"] == "event-a"
    assert canonical.loc[0, "depth_km"] == 10.0
    assert bool(canonical.loc[0, "source_place_is_philippines_label"])
    assert "source__place" in canonical.columns


def test_streaming_adm2_assignment(tmp_path):
    boundary = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "shapeName": "Test Province",
                    "shapeID": "PHL.1_1",
                    "shapeType": "ADM2",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[119.0, 9.0], [121.0, 9.0], [121.0, 11.0], [119.0, 11.0], [119.0, 9.0]]
                    ],
                },
            }
        ],
    }
    boundary_path = tmp_path / "test-adm2.geojson"
    boundary_path.write_text(json.dumps(boundary), encoding="utf-8")

    cleaned, _ = clean_usgs_data(
        _source_frame(), source_name="USGS", import_id="test-import"
    )
    processed, report = assign_adm2_provinces(cleaned, boundary_path)

    assert processed.loc[0, "province_name"] == "Test Province"
    assert processed.loc[0, "province_id"] == "PHL.1_1"
    assert processed.loc[0, "geographic_assignment_status"] == "assigned"
    assert processed.loc[1, "geographic_assignment_status"] == "outside_study_scope_candidate"
    assert report["assigned_rows"] == 1

