import pandas as pd

from app.analysis.eda import calculate_statistics


def test_calculate_statistics_returns_reproducible_summary():
    frame = pd.DataFrame(
        {
            "occurred_at": pd.to_datetime(
                ["2025-01-01T00:00:00Z", "2025-01-15T00:00:00Z", "2025-02-01T00:00:00Z"],
                utc=True,
            ),
            "latitude": [10.0, 11.0, 12.0],
            "longitude": [120.0, 121.0, 122.0],
            "depth_km": [10.0, 100.0, 350.0],
            "magnitude": [4.0, 5.0, 6.0],
            "magnitude_type": ["mb", "mb", "mww"],
            "province_name": ["A", "A", pd.NA],
            "geographic_assignment_status": [
                "assigned",
                "assigned",
                "offshore_or_unassigned",
            ],
        }
    )

    result = calculate_statistics(frame)

    assert result["record_count"] == 3
    assert result["numeric_summary"]["magnitude"]["mean"] == 5.0
    assert result["assigned_province_count"] == 1
    assert result["geographic_assignment_counts"]["assigned"] == 2
    assert len(result["monthly_activity"]) == 12
    assert result["monthly_activity"][:2] == [
        {"month": "2025-01", "earthquake_count": 2},
        {"month": "2025-02", "earthquake_count": 1},
    ]
