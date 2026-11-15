import pandas as pd
import pytest

from app.services.clustering_service import (
    evaluate_candidate_k,
    fit_kmeans,
    prepare_geographical_coordinates,
    select_k,
    summarize_clusters,
)


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "latitude": [10.0, 10.2, 20.0, 20.2, 30.0],
            "longitude": [120.0, 120.2, 125.0, 125.2, 130.0],
            "depth_km": [10, 20, 30, 40, 50],
            "magnitude": [4.0, 4.1, 4.2, 4.3, 4.4],
            "province_name": ["A", "A", "B", "B", pd.NA],
            "geographic_assignment_status": [
                "assigned",
                "assigned",
                "offshore_or_unassigned",
                "offshore_or_unassigned",
                "outside_study_scope_candidate",
            ],
        }
    )


def test_coordinates_evaluate_fit_and_summarize():
    prepared = prepare_geographical_coordinates(_frame())
    assert prepared["cluster_assignment_status"].tolist() == [
        "eligible",
        "eligible",
        "eligible",
        "eligible",
        "excluded_outside_study_scope",
    ]
    assert prepared[["projected_x_m", "projected_y_m"]].iloc[:4].notna().all().all()

    evaluation = evaluate_candidate_k(prepared, k_values=[2, 3])
    assert evaluation["status"].tolist() == ["evaluated", "evaluated"]
    selected_k = select_k(evaluation)
    assert selected_k in {2, 3}

    clustered, metadata = fit_kmeans(prepared, n_clusters=2)
    assert clustered["cluster_label"].iloc[:4].notna().all()
    assert pd.isna(clustered["cluster_label"].iloc[4])
    assert metadata["n_clusters"] == 2

    summary = summarize_clusters(clustered)
    assert len(summary) == 2
    assert int(summary["record_count"].sum()) == 4


def test_clustering_rejects_no_eligible_coordinates():
    frame = _frame().assign(geographic_assignment_status="outside_study_scope_candidate")
    prepared = prepare_geographical_coordinates(frame)
    with pytest.raises(ValueError, match="No valid in-scope coordinates"):
        evaluate_candidate_k(prepared, k_values=[2])


def test_clustering_rejects_more_clusters_than_unique_points():
    frame = _frame().iloc[[0]].copy()
    frame["geographic_assignment_status"] = "assigned"
    repeated = pd.concat([frame, frame], ignore_index=True)
    prepared = prepare_geographical_coordinates(repeated)
    with pytest.raises(ValueError, match="unique coordinate points"):
        fit_kmeans(prepared, n_clusters=2)
