# Phase 1 Data Dictionary

## Source file

`backend/data/raw/usgs/usgs_earthquake_dataset.csv`

Provider identifier observed in the file: `us` (USGS). The source event identifier is the `id` column. All 612 observed event IDs are unique.

## Original USGS columns

| Original column | Observed type | Canonical field candidate | Meaning / handling |
|---|---|---|---|
| `time` | string | `occurred_at` | Event time; parse as UTC-aware timestamp |
| `latitude` | float64 | `latitude` | Event latitude in decimal degrees |
| `longitude` | float64 | `longitude` | Event longitude in decimal degrees |
| `depth` | float64 | `depth_km` | Reported earthquake depth; preserve numeric value and document units as km |
| `mag` | float64 | `magnitude` | Reported magnitude value |
| `magType` | string | `magnitude_type` | Magnitude scale/type; observed values are `mb` and `mww` |
| `nst` | int64 | `station_count` | Number of stations used where supplied |
| `gap` | int64 | `azimuthal_gap` | Network azimuthal gap where supplied |
| `dmin` | float64 | `distance_to_nearest_station` | Preserve source value and verify exact source units before presenting it to users |
| `rms` | float64 | `rms_residual` | Preserve source measurement |
| `net` | string | `source_network` | Network/provider code; all observed values are `us` |
| `id` | string | `source_event_id` | Original source event identifier |
| `updated` | string | `source_updated_at` | Last source update time; parse as UTC-aware timestamp |
| `place` | string | `location_description` | Original USGS location description |
| `type` | string | `event_type` | Event type; all observed values are `earthquake` |
| `horizontalError` | float64 | `horizontal_error` | Preserve source uncertainty value; verify display units from USGS metadata |
| `depthError` | float64 | `depth_error` | Preserve source uncertainty value; verify display units from USGS metadata |
| `magError` | float64 | `magnitude_error` | Preserve source uncertainty value |
| `magNst` | int64 | `magnitude_station_count` | Number of stations used for magnitude where supplied |
| `status` | string | `review_status` | Source review status; all observed values are `reviewed` |
| `locationSource` | string | `location_source` | Location source code; all observed values are `us` |
| `magSource` | string | `magnitude_source` | Magnitude source code; all observed values are `us` |

## Canonical application fields

The application should use a canonical internal schema while retaining the original source columns for provenance.

| Canonical field | Source mapping | Initial handling |
|---|---|---|
| `source_event_id` | `id` | Required for source-level identity; enforce uniqueness within a source/import |
| `source_name` | Constant derived from source metadata | Set to `USGS` for this import; do not confuse with `net` |
| `occurred_at` | `time` | Parse to UTC-aware timestamp |
| `latitude` | `latitude` | Validate range -90 to 90 |
| `longitude` | `longitude` | Validate range -180 to 180 |
| `depth_km` | `depth` | Preserve missing values if future files contain them; do not replace with zero |
| `magnitude` | `mag` | Exclude only from magnitude-specific calculations when missing or invalid |
| `magnitude_type` | `magType` | Preserve the scale/type; do not compare scales without documenting the method |
| `location_description` | `place` | Preserve the original text |
| `province_id` | Not available | Leave null until a verified ADM2 layer is available |
| `region` | Derived from ADM1 `shapeName` | Populate only after a successful documented spatial operation |
| `island_group` | Not present | Derive only through a documented mapping and approved offshore policy |

## Observed quality state

- Every original column had 0 missing values in the inspected file.
- All 612 event IDs were unique.
- All timestamps parsed successfully.
- All inspected numeric fields were numeric and finite.
- No latitude/longitude values violated their basic coordinate ranges.
- No negative depth values were observed.

These findings describe this specific downloaded file and must be rechecked whenever a new source file is imported.

## Boundary dataset dictionary

File: `backend/data/boundaries/geoBoundaries-PHL-ADM1.geojson`

| Field | Observed type | Meaning / handling |
|---|---|---|
| `shapeISO` | string/object | Boundary feature ISO-style identifier; preserve |
| `shapeName` | string/object | Administrative region name; use as the region label after normalization is documented |
| `shapeID` | string/object | geoBoundaries feature identifier; preserve |
| `shapeGroup` | string/object | Dataset grouping field; preserve |
| `shapeType` | string/object | Administrative level; all observed values are `ADM1` |
| `geometry` | Polygon/MultiPolygon | Region geometry; CRS reported as EPSG:4326 |

The file contains 17 region features and does not contain provincial (`ADM2`) attributes.

