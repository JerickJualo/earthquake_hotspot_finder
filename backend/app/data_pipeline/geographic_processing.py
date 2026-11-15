"""Memory-conscious geographic processing for large GeoJSON boundaries."""

from __future__ import annotations

import math
from pathlib import Path

import ijson
import numpy as np
import pandas as pd


COORDINATE_PREFIX = "features.item.geometry.coordinates"


def _scan_boundary_metadata(path: Path) -> list[dict]:
    """Read feature metadata and coordinate bounds without building geometries."""

    features: list[dict] = []
    current: dict | None = None
    coordinate_number_index = 0

    with path.open("rb") as stream:
        for prefix, event, value in ijson.parse(stream, use_float=True):
            if prefix == "features.item" and event == "start_map":
                current = {
                    "name": None,
                    "shape_id": None,
                    "shape_type": None,
                    "geometry_type": None,
                    "minx": math.inf,
                    "miny": math.inf,
                    "maxx": -math.inf,
                    "maxy": -math.inf,
                    "coordinate_count": 0,
                }
                coordinate_number_index = 0
                continue

            if current is None:
                continue

            if prefix == "features.item.properties.shapeName" and event == "string":
                current["name"] = value
            elif prefix == "features.item.properties.shapeID" and event == "string":
                current["shape_id"] = value
            elif prefix == "features.item.properties.shapeType" and event == "string":
                current["shape_type"] = value
            elif prefix == "features.item.geometry.type" and event == "string":
                current["geometry_type"] = value
            elif prefix.startswith(COORDINATE_PREFIX) and event == "number":
                number = float(value)
                current["coordinate_count"] += 1
                if coordinate_number_index % 2 == 0:
                    current["minx"] = min(current["minx"], number)
                    current["maxx"] = max(current["maxx"], number)
                else:
                    current["miny"] = min(current["miny"], number)
                    current["maxy"] = max(current["maxy"], number)
                coordinate_number_index += 1
            elif prefix == "features.item" and event == "end_map":
                features.append(current)
                current = None

    return features


def _segment_crossings(
    ring_inside: np.ndarray | None,
    active_lons: np.ndarray,
    active_lats: np.ndarray,
    previous: tuple[float, float],
    current: tuple[float, float],
) -> None:
    """Apply one ray-casting segment to active points."""

    if ring_inside is None or not len(active_lons):
        return

    x1, y1 = previous
    x2, y2 = current
    candidate = (active_lats > min(y1, y2)) & (active_lats <= max(y1, y2))
    if not candidate.any() or y1 == y2:
        return

    x_intersections = x1 + (active_lats[candidate] - y1) * (x2 - x1) / (y2 - y1)
    crosses = active_lons[candidate] < x_intersections
    ring_inside[candidate] ^= crosses


def _finish_ring(
    ring_inside: np.ndarray | None,
    first_point: tuple[float, float] | None,
    previous_point: tuple[float, float] | None,
    point_count: int,
    ring_index: int,
    polygon_inside: np.ndarray | None,
    active_lons: np.ndarray,
    active_lats: np.ndarray,
) -> tuple[np.ndarray | None, int, bool]:
    """Close a ring and combine it with the current polygon, including holes."""

    structurally_valid = point_count >= 4 and first_point == previous_point
    if ring_inside is not None and first_point is not None and previous_point is not None:
        _segment_crossings(
            ring_inside, active_lons, active_lats, previous_point, first_point
        )
        if ring_index == 0:
            polygon_inside = ring_inside.copy()
        elif polygon_inside is not None:
            polygon_inside &= ~ring_inside

    return polygon_inside, ring_index + 1, structurally_valid


def assign_adm2_provinces(
    frame: pd.DataFrame,
    boundary_path: Path,
) -> tuple[pd.DataFrame, dict]:
    """Assign province names using a streaming Polygon/MultiPolygon parser.

    The parser avoids loading the 444 MB GeoJSON into one GeoDataFrame. It uses
    boundary polygons as-is and does not assign an artificial nearest province.
    """

    if not boundary_path.exists():
        raise FileNotFoundError(f"ADM2 boundary file not found: {boundary_path}")

    longitudes = pd.to_numeric(frame["longitude"], errors="coerce").to_numpy(float)
    latitudes = pd.to_numeric(frame["latitude"], errors="coerce").to_numpy(float)
    point_count = len(frame)
    matches: list[list[tuple[str, str | None]]] = [[] for _ in range(point_count)]
    metadata = _scan_boundary_metadata(boundary_path)
    invalid_ring_count = 0
    empty_feature_count = 0

    with boundary_path.open("rb") as stream:
        feature_index = -1
        current_info: dict | None = None
        geometry_type: str | None = None
        feature_inside: np.ndarray | None = None
        polygon_inside: np.ndarray | None = None
        ring_inside: np.ndarray | None = None
        active_indices = np.array([], dtype=int)
        active_lons = np.array([], dtype=float)
        active_lats = np.array([], dtype=float)
        ring_index = 0
        first_point: tuple[float, float] | None = None
        previous_point: tuple[float, float] | None = None
        point_values: list[float] = []
        point_count_in_ring = 0

        for prefix, event, value in ijson.parse(stream, use_float=True):
            if prefix == "features.item" and event == "start_map":
                feature_index += 1
                current_info = metadata[feature_index]
                geometry_type = current_info["geometry_type"]
                minx, miny = current_info["minx"], current_info["miny"]
                maxx, maxy = current_info["maxx"], current_info["maxy"]
                active_indices = np.flatnonzero(
                    np.isfinite(longitudes)
                    & np.isfinite(latitudes)
                    & (longitudes >= minx)
                    & (longitudes <= maxx)
                    & (latitudes >= miny)
                    & (latitudes <= maxy)
                )
                active_lons = longitudes[active_indices]
                active_lats = latitudes[active_indices]
                feature_inside = np.zeros(len(active_indices), dtype=bool)
                polygon_inside = None
                ring_inside = None
                ring_index = 0
                first_point = None
                previous_point = None
                point_values = []
                point_count_in_ring = 0
                continue

            if current_info is None:
                continue

            ring_prefix = (
                f"{COORDINATE_PREFIX}.item"
                if geometry_type == "Polygon"
                else f"{COORDINATE_PREFIX}.item.item"
            )
            point_prefix = f"{ring_prefix}.item"
            number_prefix = f"{point_prefix}.item"

            if prefix == ring_prefix and event == "start_array":
                ring_inside = np.zeros(len(active_indices), dtype=bool)
                first_point = None
                previous_point = None
                point_values = []
                point_count_in_ring = 0
            elif prefix == number_prefix and event == "number":
                point_values.append(float(value))
                if len(point_values) == 2:
                    point = (point_values[0], point_values[1])
                    if first_point is None:
                        first_point = point
                    if previous_point is not None:
                        _segment_crossings(
                            ring_inside,
                            active_lons,
                            active_lats,
                            previous_point,
                            point,
                        )
                    previous_point = point
                    point_count_in_ring += 1
                    point_values = []
            elif prefix == ring_prefix and event == "end_array":
                polygon_inside, ring_index, ring_valid = _finish_ring(
                    ring_inside,
                    first_point,
                    previous_point,
                    point_count_in_ring,
                    ring_index,
                    polygon_inside,
                    active_lons,
                    active_lats,
                )
                if not ring_valid:
                    invalid_ring_count += 1
                ring_inside = None
            elif (
                geometry_type == "MultiPolygon"
                and prefix == f"{COORDINATE_PREFIX}.item"
                and event == "end_array"
            ):
                if polygon_inside is not None and feature_inside is not None:
                    feature_inside |= polygon_inside
                polygon_inside = None
                ring_index = 0
            elif prefix == COORDINATE_PREFIX and event == "end_array":
                if geometry_type == "Polygon" and polygon_inside is not None and feature_inside is not None:
                    feature_inside |= polygon_inside
                if feature_inside is not None and current_info["coordinate_count"] == 0:
                    empty_feature_count += 1
            elif prefix == "features.item" and event == "end_map":
                if feature_inside is not None:
                    for local_index, global_index in enumerate(active_indices):
                        if feature_inside[local_index]:
                            matches[global_index].append(
                                (str(current_info["name"]), current_info["shape_id"])
                            )
                current_info = None

    result = frame.copy()
    result["province_name"] = pd.Series(pd.NA, index=result.index, dtype="string")
    result["province_id"] = pd.Series(pd.NA, index=result.index, dtype="string")
    result["geographic_assignment_status"] = result[
        "geographic_assignment_status"
    ].astype("string")

    for row_index, row_matches in enumerate(matches):
        if len(row_matches) == 1:
            province_name, province_id = row_matches[0]
            result.at[result.index[row_index], "province_name"] = province_name
            if province_id is not None:
                result.at[result.index[row_index], "province_id"] = str(province_id)
            result.at[result.index[row_index], "geographic_assignment_status"] = "assigned"
        elif len(row_matches) > 1:
            result.at[result.index[row_index], "province_name"] = "; ".join(
                match[0] for match in row_matches
            )
            result.at[result.index[row_index], "province_id"] = "; ".join(
                match[1] for match in row_matches if match[1] is not None
            ) or pd.NA
            result.at[result.index[row_index], "geographic_assignment_status"] = "multiple_polygon_matches_review"
        elif result.iloc[row_index]["source_place_is_philippines_label"]:
            result.at[result.index[row_index], "geographic_assignment_status"] = "offshore_or_unassigned"
        else:
            result.at[result.index[row_index], "geographic_assignment_status"] = "outside_study_scope_candidate"

    report = {
        "boundary_file": boundary_path.name,
        "boundary_feature_count": len(metadata),
        "boundary_shape_types": sorted({item["shape_type"] for item in metadata}),
        "boundary_geometry_types": sorted({item["geometry_type"] for item in metadata}),
        "assigned_rows": int((result["geographic_assignment_status"] == "assigned").sum()),
        "unassigned_rows": int((result["geographic_assignment_status"] == "offshore_or_unassigned").sum()),
        "outside_study_scope_candidates": int((result["geographic_assignment_status"] == "outside_study_scope_candidate").sum()),
        "multiple_polygon_matches": int((result["geographic_assignment_status"] == "multiple_polygon_matches_review").sum()),
        "invalid_ring_count": invalid_ring_count,
        "empty_feature_count": empty_feature_count,
        "policy": "No nearest-province assignment was performed; unmatched points remain unassigned.",
    }
    return result, report
