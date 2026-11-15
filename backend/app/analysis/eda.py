"""Reproducible exploratory analysis for the cleaned earthquake dataset."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_MPL_CONFIG_DIR = Path(__file__).resolve().parents[3] / ".matplotlib"
_MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPL_CONFIG_DIR))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


MAGNITUDE_BINS = [-np.inf, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, np.inf]
MAGNITUDE_LABELS = [
    "<4.5",
    "4.5–<5.0",
    "5.0–<5.5",
    "5.5–<6.0",
    "6.0–<6.5",
    "6.5–<7.0",
    "≥7.0",
]
DEPTH_BINS = [-np.inf, 70.0, 300.0, np.inf]
DEPTH_LABELS = ["Shallow (<70 km)", "Intermediate (70–<300 km)", "Deep (≥300 km)"]


def load_cleaned_dataset(path: Path) -> pd.DataFrame:
    """Load the Phase 3 output and normalize analysis dtypes."""

    if not path.exists():
        raise FileNotFoundError(f"Cleaned dataset not found: {path}")
    frame = pd.read_csv(path)
    frame["occurred_at"] = pd.to_datetime(frame["occurred_at"], errors="coerce", utc=True)
    for column in ["latitude", "longitude", "depth_km", "magnitude"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def _numeric_summary(series: pd.Series) -> dict[str, float | int | None]:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return {"count": 0, "min": None, "q1": None, "median": None, "mean": None, "q3": None, "max": None, "std": None}
    return {
        "count": int(values.count()),
        "min": float(values.min()),
        "q1": float(values.quantile(0.25)),
        "median": float(values.median()),
        "mean": float(values.mean()),
        "q3": float(values.quantile(0.75)),
        "max": float(values.max()),
        "std": float(values.std(ddof=1)) if len(values) > 1 else 0.0,
    }


def calculate_statistics(frame: pd.DataFrame) -> dict[str, Any]:
    """Calculate the statistics used by the notebook and reports."""

    occurred = frame["occurred_at"].dropna()
    assignment = frame["geographic_assignment_status"].value_counts(dropna=False)
    province_counts = (
        frame.loc[frame["province_name"].notna(), "province_name"]
        .value_counts()
        .rename_axis("province_name")
        .reset_index(name="earthquake_count")
    )

    monthly = (
        frame.assign(month=frame["occurred_at"].dt.strftime("%Y-%m"))
        .groupby("month", dropna=False)
        .size()
        .rename("earthquake_count")
        .reindex(
            pd.date_range(
                occurred.min().floor("D").replace(month=1, day=1),
                occurred.max().floor("D").replace(month=12, day=31),
                freq="MS",
            ).strftime("%Y-%m"),
            fill_value=0,
        )
        .rename_axis("month")
        .reset_index()
    )

    magnitude_bins = pd.cut(
        frame["magnitude"], bins=MAGNITUDE_BINS, labels=MAGNITUDE_LABELS, right=False
    )
    magnitude_distribution = (
        magnitude_bins.value_counts(sort=False)
        .rename_axis("magnitude_bin")
        .reset_index(name="earthquake_count")
    )

    depth_bins = pd.cut(frame["depth_km"], bins=DEPTH_BINS, labels=DEPTH_LABELS, right=False)
    depth_distribution = (
        depth_bins.value_counts(sort=False)
        .rename_axis("depth_bin")
        .reset_index(name="earthquake_count")
    )

    return {
        "record_count": int(len(frame)),
        "date_min_utc": occurred.min().isoformat() if not occurred.empty else None,
        "date_max_utc": occurred.max().isoformat() if not occurred.empty else None,
        "numeric_summary": {
            "magnitude": _numeric_summary(frame["magnitude"]),
            "depth_km": _numeric_summary(frame["depth_km"]),
            "latitude": _numeric_summary(frame["latitude"]),
            "longitude": _numeric_summary(frame["longitude"]),
        },
        "magnitude_type_counts": {
            str(key): int(value)
            for key, value in frame["magnitude_type"].value_counts(dropna=False).items()
        },
        "geographic_assignment_counts": {
            str(key): int(value) for key, value in assignment.items()
        },
        "assigned_province_count": int(frame["province_name"].dropna().nunique()),
        "province_activity": province_counts.to_dict(orient="records"),
        "monthly_activity": monthly.to_dict(orient="records"),
        "magnitude_distribution": magnitude_distribution.to_dict(orient="records"),
        "depth_distribution": depth_distribution.to_dict(orient="records"),
    }


def export_statistical_results(frame: pd.DataFrame, output_dir: Path) -> dict[str, Path]:
    """Write machine-readable and beginner-readable EDA results."""

    output_dir.mkdir(parents=True, exist_ok=True)
    statistics = calculate_statistics(frame)
    output_paths = {
        "json": output_dir / "statistical_results.json",
        "monthly": output_dir / "monthly_activity.csv",
        "magnitude": output_dir / "magnitude_distribution.csv",
        "depth": output_dir / "depth_distribution.csv",
        "province": output_dir / "province_activity.csv",
        "geography": output_dir / "geographic_assignment.csv",
    }
    output_paths["json"].write_text(
        json.dumps(statistics, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    pd.DataFrame(statistics["monthly_activity"]).to_csv(output_paths["monthly"], index=False)
    pd.DataFrame(statistics["magnitude_distribution"]).to_csv(
        output_paths["magnitude"], index=False
    )
    pd.DataFrame(statistics["depth_distribution"]).to_csv(output_paths["depth"], index=False)
    pd.DataFrame(statistics["province_activity"]).to_csv(output_paths["province"], index=False)
    pd.DataFrame(
        statistics["geographic_assignment_counts"].items(),
        columns=["geographic_assignment_status", "earthquake_count"],
    ).to_csv(output_paths["geography"], index=False)
    return output_paths


def _save_figure(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def create_visualizations(frame: pd.DataFrame, figure_dir: Path) -> dict[str, Path]:
    """Create static exploratory figures and return their paths."""

    figure_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].hist(frame["magnitude"].dropna(), bins=np.arange(3.75, 7.76, 0.25), color="#2563eb", edgecolor="white")
    axes[0].set(title="Earthquake magnitude distribution", xlabel="Magnitude", ylabel="Records")
    axes[0].grid(axis="y", alpha=0.25)
    axes[1].boxplot(frame["magnitude"].dropna(), vert=True, patch_artist=True, boxprops={"facecolor": "#93c5fd"})
    axes[1].set(title="Magnitude summary", ylabel="Magnitude")
    axes[1].set_xticks([])
    axes[1].grid(axis="y", alpha=0.25)
    paths["magnitude_distribution"] = figure_dir / "magnitude_distribution.png"
    _save_figure(fig, paths["magnitude_distribution"])

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].hist(frame["depth_km"].dropna(), bins=30, color="#0f766e", edgecolor="white")
    axes[0].set(title="Earthquake depth distribution", xlabel="Depth (km)", ylabel="Records")
    axes[0].grid(axis="y", alpha=0.25)
    axes[1].hist(frame["depth_km"].dropna(), bins=30, color="#14b8a6", edgecolor="white", log=True)
    axes[1].set(title="Depth distribution (log count scale)", xlabel="Depth (km)", ylabel="Records (log scale)")
    axes[1].grid(axis="y", alpha=0.25)
    paths["depth_distribution"] = figure_dir / "depth_distribution.png"
    _save_figure(fig, paths["depth_distribution"])

    monthly = (
        frame.assign(month=frame["occurred_at"].dt.strftime("%Y-%m"))
        .groupby("month")
        .size()
    )
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(monthly.index, monthly.values, color="#7c3aed")
    ax.set(title="Earthquake records by month (UTC)", xlabel="Month", ylabel="Records")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.25)
    paths["monthly_activity"] = figure_dir / "monthly_activity.png"
    _save_figure(fig, paths["monthly_activity"])

    status_colors = {
        "assigned": "#16a34a",
        "offshore_or_unassigned": "#f59e0b",
        "outside_study_scope_candidate": "#dc2626",
    }
    fig, ax = plt.subplots(figsize=(8, 7))
    for status, group in frame.groupby("geographic_assignment_status", dropna=False):
        ax.scatter(
            group["longitude"],
            group["latitude"],
            s=20,
            alpha=0.7,
            label=str(status),
            color=status_colors.get(str(status), "#64748b"),
        )
    ax.set(title="Earthquake locations and geographic assignment status", xlabel="Longitude (°E)", ylabel="Latitude (°N)")
    ax.legend(title="Status", loc="best")
    ax.grid(alpha=0.2)
    paths["geographical_distribution"] = figure_dir / "geographical_distribution.png"
    _save_figure(fig, paths["geographical_distribution"])

    province_counts = (
        frame.loc[frame["province_name"].notna(), "province_name"]
        .value_counts()
        .sort_values()
        .tail(15)
    )
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(province_counts.index, province_counts.values, color="#0891b2")
    ax.set(title="Top 15 provinces by assigned earthquake records", xlabel="Records", ylabel="Province")
    ax.grid(axis="x", alpha=0.25)
    paths["province_activity"] = figure_dir / "province_activity.png"
    _save_figure(fig, paths["province_activity"])

    fig, ax = plt.subplots(figsize=(8, 5.5))
    scatter = ax.scatter(
        frame["depth_km"],
        frame["magnitude"],
        c=frame["latitude"],
        cmap="viridis",
        alpha=0.7,
        s=24,
    )
    ax.set(title="Magnitude versus depth", xlabel="Depth (km)", ylabel="Magnitude")
    fig.colorbar(scatter, ax=ax, label="Latitude (°N)")
    ax.grid(alpha=0.2)
    paths["magnitude_vs_depth"] = figure_dir / "magnitude_vs_depth.png"
    _save_figure(fig, paths["magnitude_vs_depth"])

    return paths


def write_findings_document(
    frame: pd.DataFrame,
    statistics: dict[str, Any],
    output_path: Path,
    figure_paths: dict[str, Path],
) -> None:
    """Write a concise, reproducible interpretation of the EDA results."""

    magnitude = statistics["numeric_summary"]["magnitude"]
    depth = statistics["numeric_summary"]["depth_km"]
    assignments = statistics["geographic_assignment_counts"]
    top_provinces = statistics["province_activity"][:5]
    top_month = max(statistics["monthly_activity"], key=lambda item: item["earthquake_count"])
    lines = [
        "# Phase 4 Exploratory Data Analysis",
        "",
        "This analysis uses the cleaned USGS 2025 development dataset. The results are provisional and descriptive; they are not earthquake predictions or final PHIVOLCS research conclusions.",
        "",
        "## Dataset and scope",
        "",
        f"- Records analyzed: **{statistics['record_count']}**",
        f"- Event coverage: **{statistics['date_min_utc']}** to **{statistics['date_max_utc']}** (UTC)",
        f"- Province-assigned records: **{assignments.get('assigned', 0)}**",
        f"- Philippine-labelled offshore/unassigned records: **{assignments.get('offshore_or_unassigned', 0)}**",
        f"- Nearby-country candidates retained for review: **{assignments.get('outside_study_scope_candidate', 0)}**",
        "",
        "## Descriptive findings",
        "",
        f"- Magnitude: mean **{magnitude['mean']:.3f}**, median **{magnitude['median']:.3f}**, range **{magnitude['min']:.1f}–{magnitude['max']:.1f}**.",
        f"- Depth: mean **{depth['mean']:.3f} km**, median **{depth['median']:.3f} km**, range **{depth['min']:.3f}–{depth['max']:.3f} km**.",
        f"- The month with the most records was **{top_month['month']}** with **{top_month['earthquake_count']}** records.",
        f"- The ADM2 assignment covers **{statistics['assigned_province_count']}** provinces in this dataset.",
        "",
        "### Provinces with the most assigned records",
        "",
        "| Province | Assigned records |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {item['province_name']} | {item['earthquake_count']} |" for item in top_provinces
    )
    lines.extend(
        [
            "",
            "## Interpretation cautions",
            "",
            "- Province counts describe only records whose coordinates intersected an ADM2 polygon. No nearest-province fallback was used.",
            "- Offshore records are retained and visibly separated; excluding or including them in later research statistics requires an explicit study rule.",
            "- The dataset covers one historical year. Time-based observations should not be described as current activity.",
            "- These descriptive results do not establish causation, recurrence probability, risk, or prediction.",
            "",
            "## Visualizations",
            "",
        ]
    )
    for title, path in figure_paths.items():
        lines.append(f"- [{title.replace('_', ' ').title()}](figures/{path.name})")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_eda(input_path: Path, output_dir: Path) -> dict[str, Any]:
    """Run all Phase 4 calculations, exports, figures, and documentation."""

    frame = load_cleaned_dataset(input_path)
    statistics = calculate_statistics(frame)
    statistical_paths = export_statistical_results(frame, output_dir / "statistics")
    figure_paths = create_visualizations(frame, output_dir / "figures")
    findings_path = output_dir / "EDA_FINDINGS.md"
    write_findings_document(frame, statistics, findings_path, figure_paths)
    return {
        "statistics": statistics,
        "statistical_paths": statistical_paths,
        "figure_paths": figure_paths,
        "findings_path": findings_path,
    }
