"""Geographical K-Means clustering service.

The service clusters earthquake coordinates only. Magnitude, depth, and time
are summarized after clustering but are not used as clustering features.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

_MPL_CONFIG_DIR = Path(__file__).resolve().parents[3] / ".matplotlib"
_MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPL_CONFIG_DIR))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyproj import CRS, Transformer
from sklearn.cluster import KMeans
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score


GEOGRAPHIC_CRS = "EPSG:4326"
LOCAL_METRIC_CRS = CRS.from_proj4(
    "+proj=aeqd +lat_0=12.8797 +lon_0=121.7740 +datum=WGS84 +units=m +no_defs"
)
LOCAL_METRIC_CRS_NAME = (
    "WGS84 local azimuthal equidistant projection centered on the Philippines"
)
DEFAULT_INCLUDED_STATUSES = ("assigned", "offshore_or_unassigned")


@dataclass(frozen=True)
class ClusteringConfig:
    """Configuration for reproducible geographical clustering."""

    random_state: int = 42
    n_init: int = 20
    min_k: int = 2
    max_k: int = 8
    included_statuses: tuple[str, ...] = DEFAULT_INCLUDED_STATUSES


def _transformers() -> tuple[Transformer, Transformer]:
    forward = Transformer.from_crs(GEOGRAPHIC_CRS, LOCAL_METRIC_CRS, always_xy=True)
    inverse = Transformer.from_crs(LOCAL_METRIC_CRS, GEOGRAPHIC_CRS, always_xy=True)
    return forward, inverse


def prepare_geographical_coordinates(
    frame: pd.DataFrame,
    *,
    included_statuses: Iterable[str] = DEFAULT_INCLUDED_STATUSES,
) -> pd.DataFrame:
    """Prepare valid, in-scope coordinates in a metric projected CRS.

    Rows remain in the returned frame. Rows outside the configured scope or
    with invalid coordinates receive explicit statuses and null projected
    coordinates rather than being silently removed.
    """

    required = {"latitude", "longitude", "geographic_assignment_status"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Missing clustering input columns: {', '.join(missing)}")

    result = frame.copy()
    latitude = pd.to_numeric(result["latitude"], errors="coerce")
    longitude = pd.to_numeric(result["longitude"], errors="coerce")
    valid_coordinates = (
        latitude.notna()
        & longitude.notna()
        & np.isfinite(latitude.to_numpy())
        & np.isfinite(longitude.to_numpy())
        & latitude.between(-90, 90)
        & longitude.between(-180, 180)
    )
    statuses = result["geographic_assignment_status"].astype("string")
    included = set(included_statuses)
    eligible = valid_coordinates & statuses.isin(included)

    result["projected_x_m"] = pd.Series(np.nan, index=result.index, dtype="float64")
    result["projected_y_m"] = pd.Series(np.nan, index=result.index, dtype="float64")
    result["cluster_label"] = pd.Series(pd.NA, index=result.index, dtype="Int64")
    result["cluster_assignment_status"] = pd.Series(
        "excluded_outside_study_scope", index=result.index, dtype="string"
    )
    result.loc[~valid_coordinates, "cluster_assignment_status"] = "excluded_invalid_coordinates"
    result.loc[eligible, "cluster_assignment_status"] = "eligible"

    if eligible.any():
        forward, _ = _transformers()
        x_values, y_values = forward.transform(
            longitude.loc[eligible].to_numpy(float),
            latitude.loc[eligible].to_numpy(float),
        )
        result.loc[eligible, "projected_x_m"] = x_values
        result.loc[eligible, "projected_y_m"] = y_values

    result.attrs["clustering_crs"] = LOCAL_METRIC_CRS.to_string()
    result.attrs["clustering_crs_name"] = LOCAL_METRIC_CRS_NAME
    result.attrs["included_statuses"] = sorted(included)
    return result


def _eligible_matrix(frame: pd.DataFrame) -> tuple[pd.Index, np.ndarray]:
    eligible = frame["cluster_assignment_status"].eq("eligible")
    indices = frame.index[eligible]
    matrix = frame.loc[indices, ["projected_x_m", "projected_y_m"]].to_numpy(float)
    if matrix.size == 0:
        raise ValueError("No valid in-scope coordinates are available for clustering")
    if not np.isfinite(matrix).all():
        raise ValueError("Projected clustering coordinates contain non-finite values")
    return indices, matrix


def _validate_k(k: int, sample_count: int, unique_point_count: int) -> None:
    if k < 1:
        raise ValueError("n_clusters must be at least 1")
    if k > sample_count:
        raise ValueError(f"n_clusters={k} exceeds the {sample_count} eligible records")
    if k > unique_point_count:
        raise ValueError(
            f"n_clusters={k} exceeds the {unique_point_count} unique coordinate points"
        )


def evaluate_candidate_k(
    frame: pd.DataFrame,
    *,
    k_values: Iterable[int],
    random_state: int = 42,
    n_init: int = 20,
) -> pd.DataFrame:
    """Evaluate candidate K values with standard internal clustering metrics."""

    _, matrix = _eligible_matrix(frame)
    unique_points = np.unique(matrix, axis=0).shape[0]
    rows: list[dict[str, Any]] = []
    for k in k_values:
        row: dict[str, Any] = {
            "k": int(k),
            "eligible_records": int(len(matrix)),
            "unique_coordinate_points": int(unique_points),
            "inertia_m2": None,
            "silhouette_score": None,
            "calinski_harabasz_score": None,
            "davies_bouldin_score": None,
            "status": "evaluated",
        }
        try:
            _validate_k(int(k), len(matrix), unique_points)
            model = KMeans(n_clusters=int(k), random_state=random_state, n_init=n_init)
            labels = model.fit_predict(matrix)
            row["inertia_m2"] = float(model.inertia_)
            if len(np.unique(labels)) < 2:
                row["status"] = "not_evaluable_single_label"
            else:
                row["silhouette_score"] = float(silhouette_score(matrix, labels))
                row["calinski_harabasz_score"] = float(
                    calinski_harabasz_score(matrix, labels)
                )
                row["davies_bouldin_score"] = float(davies_bouldin_score(matrix, labels))
        except ValueError as exc:
            row["status"] = f"skipped: {exc}"
        rows.append(row)
    return pd.DataFrame(rows)


def select_k(evaluation: pd.DataFrame) -> int:
    """Select the highest-silhouette candidate, breaking ties toward lower K."""

    valid = evaluation.loc[
        evaluation["silhouette_score"].notna() & (evaluation["status"] == "evaluated")
    ]
    if valid.empty:
        raise ValueError("No candidate K has a valid silhouette score")
    selected = valid.sort_values(["silhouette_score", "k"], ascending=[False, True]).iloc[0]
    return int(selected["k"])


def _canonical_label_mapping(centers: np.ndarray) -> dict[int, int]:
    order = np.lexsort((centers[:, 1], centers[:, 0]))
    return {int(raw_label): int(canonical_label) for canonical_label, raw_label in enumerate(order)}


def fit_kmeans(
    frame: pd.DataFrame,
    *,
    n_clusters: int,
    random_state: int = 42,
    n_init: int = 20,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fit K-Means and assign deterministic labels to eligible records."""

    result = frame.copy()
    indices, matrix = _eligible_matrix(result)
    unique_points = np.unique(matrix, axis=0).shape[0]
    _validate_k(n_clusters, len(matrix), unique_points)

    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=n_init)
    raw_labels = model.fit_predict(matrix)
    mapping = _canonical_label_mapping(model.cluster_centers_)
    labels = np.array([mapping[int(label)] for label in raw_labels], dtype=int)
    result.loc[indices, "cluster_label"] = labels
    result.loc[indices, "cluster_assignment_status"] = "assigned"

    _, inverse = _transformers()
    canonical_centers = np.empty_like(model.cluster_centers_)
    for raw_label, canonical_label in mapping.items():
        canonical_centers[canonical_label] = model.cluster_centers_[raw_label]
    centroid_lons, centroid_lats = inverse.transform(
        canonical_centers[:, 0], canonical_centers[:, 1]
    )
    metadata = {
        "n_clusters": int(n_clusters),
        "random_state": int(random_state),
        "n_init": int(n_init),
        "inertia_m2": float(model.inertia_),
        "silhouette_score": float(silhouette_score(matrix, raw_labels))
        if n_clusters > 1
        else None,
        "cluster_centroids": [
            {
                "cluster_label": int(label),
                "centroid_longitude": float(centroid_lons[label]),
                "centroid_latitude": float(centroid_lats[label]),
                "centroid_x_m": float(canonical_centers[label, 0]),
                "centroid_y_m": float(canonical_centers[label, 1]),
            }
            for label in range(n_clusters)
        ],
    }
    result.attrs.update(frame.attrs)
    result.attrs["cluster_metadata"] = metadata
    return result, metadata


def summarize_clusters(frame: pd.DataFrame) -> pd.DataFrame:
    """Create descriptive summaries for each assigned spatial cluster."""

    if "cluster_label" not in frame.columns:
        raise ValueError("The frame must contain cluster_label before summarization")
    assigned = frame.loc[frame["cluster_label"].notna()].copy()
    if assigned.empty:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    total = len(assigned)
    for cluster_label, group in assigned.groupby("cluster_label", sort=True):
        provinces = group["province_name"].dropna().astype(str)
        province_counts = provinces.value_counts()
        rows.append(
            {
                "cluster_label": int(cluster_label),
                "record_count": int(len(group)),
                "percentage_of_clustered_records": float(len(group) / total * 100),
                "centroid_latitude": float(group["latitude"].mean()),
                "centroid_longitude": float(group["longitude"].mean()),
                "min_latitude": float(group["latitude"].min()),
                "max_latitude": float(group["latitude"].max()),
                "min_longitude": float(group["longitude"].min()),
                "max_longitude": float(group["longitude"].max()),
                "mean_magnitude": float(group["magnitude"].mean()),
                "max_magnitude": float(group["magnitude"].max()),
                "mean_depth_km": float(group["depth_km"].mean()),
                "assigned_province_count": int(provinces.nunique()),
                "top_assigned_province": str(province_counts.index[0])
                if not province_counts.empty
                else None,
                "top_assigned_province_records": int(province_counts.iloc[0])
                if not province_counts.empty
                else 0,
            }
        )
    return pd.DataFrame(rows)


def create_cluster_visualizations(
    frame: pd.DataFrame,
    summary: pd.DataFrame,
    output_dir: Path,
) -> dict[str, Path]:
    """Create geographic cluster and cluster-size figures."""

    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    fig, ax = plt.subplots(figsize=(9, 7))
    excluded = frame.loc[frame["cluster_label"].isna()]
    if not excluded.empty:
        ax.scatter(
            excluded["longitude"],
            excluded["latitude"],
            color="#9ca3af",
            s=20,
            alpha=0.45,
            label="Excluded from clustering",
        )
    clustered = frame.loc[frame["cluster_label"].notna()]
    colors = plt.get_cmap("tab10")
    for label, group in clustered.groupby("cluster_label", sort=True):
        ax.scatter(
            group["longitude"],
            group["latitude"],
            s=24,
            alpha=0.75,
            color=colors(int(label) % 10),
            label=f"Cluster {int(label)} ({len(group)})",
        )
    if not summary.empty:
        ax.scatter(
            summary["centroid_longitude"],
            summary["centroid_latitude"],
            marker="x",
            s=90,
            linewidths=2,
            color="#111827",
            label="Cluster centroid",
        )
    ax.set(
        title="Geographical K-Means clusters",
        xlabel="Longitude (°E)",
        ylabel="Latitude (°N)",
    )
    ax.grid(alpha=0.2)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    paths["geographic_clusters"] = output_dir / "geographic_clusters.png"
    fig.savefig(paths["geographic_clusters"], dpi=160, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    if not summary.empty:
        ax.bar(summary["cluster_label"].astype(str), summary["record_count"], color="#7c3aed")
    ax.set(title="Records per geographical cluster", xlabel="Cluster label", ylabel="Records")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    paths["cluster_sizes"] = output_dir / "cluster_sizes.png"
    fig.savefig(paths["cluster_sizes"], dpi=160, bbox_inches="tight")
    plt.close(fig)
    return paths


def write_clustering_findings(
    metadata: dict[str, Any],
    evaluation: pd.DataFrame,
    summary: pd.DataFrame,
    output_path: Path,
) -> None:
    """Write a plain-language report of the selected clustering result."""

    def format_metric(value: Any, digits: int = 4) -> str:
        if value is None or pd.isna(value):
            return "n/a"
        return f"{float(value):.{digits}f}"

    selected_k = metadata["selected_k"]
    fit = metadata["fit"]
    lines = [
        "# Phase 5 Geographical Clustering Findings",
        "",
        "This report describes K-Means groupings in the provisional USGS 2025 development dataset. A cluster is a spatial grouping produced by the algorithm; it is not a confirmed earthquake hotspot, hazard ranking, recurrence estimate, or prediction.",
        "",
        "## Configuration",
        "",
        f"- Records included in clustering: **{metadata['eligible_record_count']}**",
        f"- Records excluded from clustering: **{sum(metadata['excluded_status_counts'].values())}**",
        f"- Selected number of clusters (K): **{selected_k}**",
        f"- Silhouette score for selected K: **{fit['silhouette_score']:.4f}**",
        f"- Coordinate transformation: **{metadata['projected_crs_name']}**",
        f"- Included assignment statuses: `{', '.join(metadata['included_statuses'])}`",
        "",
        "The 22 nearby-country candidates were excluded because their Phase 3 status was `outside_study_scope_candidate`. They remain in the cleaned dataset and clustered output with null cluster labels.",
        "",
        "## Candidate-K evaluation",
        "",
        "The selected K maximizes the silhouette score among K=2 through K=8, with lower K preferred only when scores tie. Higher silhouette values indicate better separation under this metric; they do not prove geological or hazard significance.",
        "",
        "| K | Inertia (m2) | Silhouette | Calinski-Harabasz | Davies-Bouldin |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in evaluation.itertuples(index=False):
        lines.append(
            f"| {row.k} | {format_metric(row.inertia_m2, 2)} | "
            f"{format_metric(row.silhouette_score)} | {format_metric(row.calinski_harabasz_score, 2)} | "
            f"{format_metric(row.davies_bouldin_score)} |"
        )
    lines.extend(
        [
            "",
            "## Cluster summaries",
            "",
            "| Cluster | Records | Share | Centroid latitude | Centroid longitude | Mean magnitude | Mean depth (km) | Top assigned province |",
            "|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.cluster_label} | {row.record_count} | {row.percentage_of_clustered_records:.2f}% | "
            f"{row.centroid_latitude:.4f} | {row.centroid_longitude:.4f} | "
            f"{row.mean_magnitude:.3f} | {row.mean_depth_km:.3f} | "
            f"{row.top_assigned_province or 'None'} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation limits",
            "",
            "- K-Means uses projected longitude/latitude only. Magnitude, depth, and time are summarized after clustering and do not influence the labels.",
            "- K-Means prefers roughly compact, distance-based groups and can be sensitive to the chosen K and study scope.",
            "- Offshore records labelled as Philippine events are included by default; this is a configurable development choice, not a final research decision.",
            "- Cluster labels are identifiers, not rankings. A larger cluster does not mean greater hazard.",
            "- The results use one historical year of USGS data and must be rerun after PHIVOLCS data is inspected and imported.",
            "",
            "## Figures",
            "",
            "- [Geographical clusters](figures/geographic_clusters.png)",
            "- [Cluster sizes](figures/cluster_sizes.png)",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_clustering(
    input_path: Path,
    output_dataset_path: Path,
    output_dir: Path,
    *,
    config: ClusteringConfig = ClusteringConfig(),
) -> dict[str, Any]:
    """Run preparation, K selection, fitting, summaries, and exports."""

    if not input_path.exists():
        raise FileNotFoundError(f"Cleaned dataset not found: {input_path}")
    frame = pd.read_csv(input_path)
    frame["occurred_at"] = pd.to_datetime(frame["occurred_at"], errors="coerce", utc=True)
    for column in ["latitude", "longitude", "depth_km", "magnitude"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    prepared = prepare_geographical_coordinates(
        frame, included_statuses=config.included_statuses
    )
    candidate_values = range(config.min_k, config.max_k + 1)
    evaluation = evaluate_candidate_k(
        prepared,
        k_values=candidate_values,
        random_state=config.random_state,
        n_init=config.n_init,
    )
    selected_k = select_k(evaluation)
    clustered, fit_metadata = fit_kmeans(
        prepared,
        n_clusters=selected_k,
        random_state=config.random_state,
        n_init=config.n_init,
    )
    summary = summarize_clusters(clustered)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_dataset_path.parent.mkdir(parents=True, exist_ok=True)
    clustered.to_csv(output_dataset_path, index=False)
    evaluation.to_csv(output_dir / "cluster_evaluation.csv", index=False)
    summary.to_csv(output_dir / "cluster_summaries.csv", index=False)
    figure_paths = create_cluster_visualizations(clustered, summary, output_dir / "figures")

    metadata = {
        "input_dataset": input_path.name,
        "output_dataset": output_dataset_path.name,
        "coordinate_source_crs": GEOGRAPHIC_CRS,
        "projected_crs": LOCAL_METRIC_CRS.to_string(),
        "projected_crs_name": LOCAL_METRIC_CRS_NAME,
        "included_statuses": list(config.included_statuses),
        "excluded_status_counts": {
            str(key): int(value)
            for key, value in clustered.loc[
                clustered["cluster_label"].isna(), "cluster_assignment_status"
            ].value_counts(dropna=False).items()
        },
        "eligible_record_count": int((clustered["cluster_label"].notna()).sum()),
        "selected_k": int(selected_k),
        "candidate_k_range": [config.min_k, config.max_k],
        "fit": fit_metadata,
    }
    (output_dir / "cluster_metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    findings_path = output_dir / "CLUSTERING_FINDINGS.md"
    write_clustering_findings(metadata, evaluation, summary, findings_path)
    return {
        "clustered": clustered,
        "evaluation": evaluation,
        "summary": summary,
        "metadata": metadata,
        "figure_paths": figure_paths,
        "findings_path": findings_path,
    }
