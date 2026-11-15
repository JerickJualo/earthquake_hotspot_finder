# Current Data Dictionary

**Active USGS file:** `backend/data/raw/usgs/accurate_2025_usgs_dataset.csv`  
**Active boundary file:** `backend/data/boundaries/geoBoundaries-PHL-ADM2.geojson`

## USGS source columns

The active CSV contains 794 records and the same 22 source columns as the previous download.

| Original column | Observed type | Canonical field candidate | Handling |
|---|---|---|---|
| `time` | string | `occurred_at` | Parse as UTC-aware timestamp |
| `latitude` | float64 | `latitude` | Validate -90 to 90 degrees |
| `longitude` | float64 | `longitude` | Validate -180 to 180 degrees |
| `depth` | float64 | `depth_km` | Preserve numeric value and source units |
| `mag` | float64 | `magnitude` | Preserve value; document magnitude scale |
| `magType` | string | `magnitude_type` | Preserve `mb`, `mww`, or `mwr` |
| `nst` | int64 | `station_count` | Preserve source attribute |
| `gap` | int64 | `azimuthal_gap` | Preserve source attribute |
| `dmin` | float64 | `distance_to_nearest_station` | Preserve; verify display units before user-facing use |
| `rms` | float64 | `rms_residual` | Preserve source attribute |
| `net` | string | `source_network` | All observed values are `us` |
| `id` | string | `source_event_id` | Preserve and enforce source-level uniqueness |
| `updated` | string | `source_updated_at` | Parse as UTC-aware timestamp |
| `place` | string | `location_description` | Preserve original text |
| `type` | string | `event_type` | All observed values are `earthquake` |
| `horizontalError` | float64 | `horizontal_error` | Preserve source uncertainty |
| `depthError` | float64 | `depth_error` | Preserve source uncertainty |
| `magError` | float64 | `magnitude_error` | Preserve source uncertainty |
| `magNst` | int64 | `magnitude_station_count` | Preserve source attribute |
| `status` | string | `review_status` | All observed values are `reviewed` |
| `locationSource` | string | `location_source` | Preserve source code |
| `magSource` | string | `magnitude_source` | Preserve source code |

## Application fields

The processed file places canonical fields first. Every original USGS value is also retained as a namespaced field such as `source__time` or `source__latitude`; this preserves provenance without creating duplicate column names.

The current canonical output also includes `station_count`, `azimuthal_gap`, `distance_to_nearest_station`, `rms_residual`, `horizontal_error`, `depth_error`, `magnitude_error`, and `magnitude_station_count`, mapped from the corresponding USGS quality and uncertainty fields.

| Canonical field | Source or derivation | Initial rule |
|---|---|---|
| `source_event_id` | `id` | Required for provenance and deduplication |
| `source_name` | Import metadata | Set to `USGS` |
| `occurred_at` | `time` | UTC-aware timestamp |
| `latitude` | `latitude` | Required for spatial processing |
| `longitude` | `longitude` | Required for spatial processing |
| `depth_km` | `depth` | Do not replace missing values with zero in future imports |
| `magnitude` | `mag` | Exclude only from analyses requiring a valid magnitude |
| `magnitude_type` | `magType` | Preserve scale/type |
| `location_description` | `place` | Preserve original description |
| `province_id` | ADM2 spatial join | Null when offshore or unassigned |
| `region` | Optional ADM1 spatial join | Derive only through documented processing |
| `island_group` | Province reference mapping | Derive through a reviewed reference table |
| `geographic_assignment_status` | Processing result | Suggested values: `assigned`, `offshore_or_unassigned`, `outside_study_scope` |

## Current data-quality state

- All 22 columns have zero missing values in the active file.
- All 794 source event IDs are unique.
- All timestamps parse successfully.
- All inspected numeric values are finite and numeric.
- No basic coordinate-range violations were found.
- No negative depth values were found.
- 772 location descriptions mention the Philippines.
- 22 location descriptions identify nearby non-Philippine areas.

## ADM2 boundary fields

| Field | Observed type | Meaning |
|---|---|---|
| `shapeName` | string/object | Province name |
| `shapeISO` | string/object | geoBoundaries identifier |
| `shapeID` | string/object | geoBoundaries feature identifier |
| `shapeGroup` | string/object | Dataset grouping field |
| `shapeType` | string/object | Administrative level; all values are `ADM2` |
| `geometry` | Polygon/MultiPolygon | Province boundary geometry in EPSG:4326 |

The active boundary file contains 86 province features: 62 MultiPolygon and 24 Polygon geometries.

