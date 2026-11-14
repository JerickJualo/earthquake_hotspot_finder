# Phase 1 Data Inspection Report

**Project:** Earthquake Hotspot Finder  
**Inspection date:** 2026-11-15  
**Original files:** Preserved and not modified

## 1. Executive summary

The workspace contains the two expected source datasets:

| Dataset | Result |
|---|---|
| `backend/data/raw/usgs/usgs_earthquake_dataset.csv` | 612 earthquake records, covering 2025-01-01 through 2025-12-31 UTC |
| `backend/data/boundaries/geoBoundaries-PHL-ADM1.geojson` | 17 first-level administrative features representing Philippine regions |

The USGS file is clean enough for initial exploratory analysis. All 612 rows have values in every column, all event IDs are unique, timestamps parse correctly, and no invalid latitude, longitude, or negative depth values were found under the initial validation rules.

The boundary file is not a province-level dataset. Its 17 `ADM1` features are regions such as CAR, NCR, Central Luzon, and Davao Region. Therefore, it can support regional and map-level analysis, but it cannot support reliable province assignments by itself. A Philippine `ADM2` boundary dataset will be required for provincial rankings.

The two datasets are broadly compatible for point-and-region analysis because both use longitude/latitude coordinates consistent with WGS84 / EPSG:4326. However, the USGS records include many offshore events, and the downloaded boundary file represents administrative areas rather than a complete offshore study-area mask.

## 2. Workspace and file audit

The project workspace contains the planned directory scaffold, the two original datasets, the project-local Python environment, and the dependency definition. No frontend application code has been created.

| File | Size | Format |
|---|---:|---|
| `usgs_earthquake_dataset.csv` | 117,694 bytes | CSV |
| `geoBoundaries-PHL-ADM1.geojson` | 440,897,026 bytes, approximately 440.9 MB | GeoJSON |

The original downloaded files were read-only inputs during this inspection. No rows, geometries, or source files were overwritten.

## 3. USGS dataset findings

### 3.1 Record count and coverage

- Records: **612**
- Columns: **22**
- Event time minimum: **2025-01-01 18:39:33.615 UTC**
- Event time maximum: **2025-12-31 17:30:42.385 UTC**
- Event-time coverage: **one calendar year, 2025**
- `updated` timestamps also parse successfully; their observed range is 2025-03-17 through 2026-09-06 UTC.

The file should not be described as a broad historical catalogue. The inspected file contains one year of records only. Its observed minimum magnitude is exactly 4.0, which suggests that the downloaded search may have used a magnitude filter, but the original search parameters are not present in the CSV and must not be assumed.

### 3.2 Columns and observed data types

Pandas observed the following types when reading the CSV:

| Column | Observed type | Missing values |
|---|---|---:|
| `time` | string | 0 |
| `latitude` | float64 | 0 |
| `longitude` | float64 | 0 |
| `depth` | float64 | 0 |
| `mag` | float64 | 0 |
| `magType` | string | 0 |
| `nst` | int64 | 0 |
| `gap` | int64 | 0 |
| `dmin` | float64 | 0 |
| `rms` | float64 | 0 |
| `net` | string | 0 |
| `id` | string | 0 |
| `updated` | string | 0 |
| `place` | string | 0 |
| `type` | string | 0 |
| `horizontalError` | float64 | 0 |
| `depthError` | float64 | 0 |
| `magError` | float64 | 0 |
| `magNst` | int64 | 0 |
| `status` | string | 0 |
| `locationSource` | string | 0 |
| `magSource` | string | 0 |

Observed categorical values include:

- `magType`: 566 `mb`, 46 `mww`
- `net`: all 612 are `us`
- `type`: all 612 are `earthquake`
- `status`: all 612 are `reviewed`
- `locationSource`: all 612 are `us`
- `magSource`: all 612 are `us`

### 3.3 Missing, duplicate, and invalid values

The inspection found:

- Missing values: **0 in every column**
- Duplicate complete rows: **0**
- Duplicate non-null event IDs: **0**
- Unique non-null event IDs: **612**
- Invalid timestamps: **0**
- Non-numeric values in numeric fields: **0**
- Non-finite numeric values: **0**
- Latitudes outside -90 to 90 degrees: **0**
- Longitudes outside -180 to 180 degrees: **0**
- Missing latitude/longitude pairs: **0**
- Negative depths: **0**

Observed numeric ranges:

| Field | Minimum | Maximum | Mean / note |
|---|---:|---:|---|
| Latitude | 5.4483 | 18.8533 | All coordinate values are numerically valid |
| Longitude | 119.1473 | 127.4282 | The eastern tail is offshore relative to the downloaded land-region bounds |
| Depth | 8.401 km | 605.561 km | No negative depths observed |
| Magnitude | 4.0 | 7.4 | Mean 4.5789; median 4.5 |

These checks show that the file is structurally clean. They do not prove that every record is scientifically complete for every analysis; for example, the absence of missing values does not establish that the dataset is a complete earthquake catalogue for the Philippines.

## 4. Geographic coverage of USGS records

All 612 `place` descriptions contain the word **“Philippines”**. There are no obvious records labelled as another country in the location text.

The observed coordinate extent is:

- Latitude: **5.4483 to 18.8533**
- Longitude: **119.1473 to 127.4282**

The geoBoundaries file has an overall extent of approximately:

- Longitude: **114.2779 to 126.6050**
- Latitude: **4.5873 to 21.1219**

At least **227 of 612 records (37.1%)** lie east of the easternmost longitude in the geoBoundaries file's overall extent. Their location descriptions still identify them as Philippine events, commonly east of Mindanao. This is consistent with offshore earthquakes rather than proof that they are outside the Philippines' broader seismic study area.

This finding is important: a point-in-polygon join against administrative land/region polygons will leave some legitimate offshore events without a region or province. Those events should be retained as raw and analytical records, with an explicit unassigned/offshore classification where appropriate.

## 5. geoBoundaries findings

### 5.1 Administrative level

The file is named `geoBoundaries-PHL-ADM1.geojson`, and all 17 features have `shapeType = ADM1`.

The 17 feature names are:

`ARMM`, `CAR`, `NCR`, `Ilocos Region`, `Cagayan Valley`, `Central Luzon`, `Calabarzon`, `Mimaropa`, `Zamboanga Peninsula`, `Bicol Region`, `Western Visayas`, `Central Visayas`, `Eastern Visayas`, `Northern Mindanao`, `Davao Region`, `Soccsksargen`, and `Caraga`.

These are first-level administrative regions, not provinces. The file does not contain a province-name field or an `ADM2` province layer.

### 5.2 Schema and geometry metadata

- Feature count: **17**
- CRS reported by the geospatial reader: **EPSG:4326**
- Encoding: **UTF-8**
- Attribute fields: `shapeISO`, `shapeName`, `shapeID`, `shapeGroup`, `shapeType`
- Attribute types: all observed as string/object fields
- Geometry types: **15 MultiPolygon** and **2 Polygon**
- Geometry objects: present for all 17 features inspected structurally
- Overall bounds: `[114.277892253, 4.587294497000073, 126.60496559600006, 21.12188547900007]` in longitude/latitude order

The dataset is a validly readable GeoJSON FeatureCollection, but it is unusually large for only 17 features because the coastline geometries are highly detailed. A complete in-memory Shapely topology-validation pass exceeded the available local memory during this audit. No destructive simplification was performed. Before production import, the geometry layer should receive a dedicated streaming/GDAL validation pass or be converted to a documented, derived simplified copy while the original remains preserved.

## 6. Can the boundary file support provincial assignments?

**No—not by itself.**

The file can support:

- Displaying Philippine administrative regions on a map
- Assigning some earthquake points to regions through a point-in-polygon operation
- Regional summaries, subject to an explicit treatment of offshore events
- A geographic context for the national study area

The file cannot support:

- Reliable province names
- Province-level earthquake counts
- Province rankings
- Province-based spatial joins

To implement provincial analysis, obtain a Philippine `ADM2` boundary dataset and inspect it separately before use. Do not derive or invent province polygons from the current ADM1 file.

Island-group filtering is also not directly available as a field. It will require a documented mapping from administrative regions to Luzon, Visayas, and Mindanao, plus a policy for offshore records that do not intersect a land-region polygon.

## 7. Dataset compatibility assessment

| Requirement | Assessment |
|---|---|
| Plot USGS coordinates with the boundary layer | Compatible in principle; both use longitude/latitude consistent with EPSG:4326 |
| Regional point-in-polygon assignment | Supported after handling the large geometries and offshore points |
| Provincial assignment | Not supported by this boundary file; ADM2 data is required |
| Island-group filtering | Not directly supported; requires documented region mapping and offshore rules |
| Date and magnitude filtering | Fully supported by the USGS fields |
| K-Means on earthquake coordinates | Supported, but the coordinate scope and projection choice must be documented |
| Historical trend analysis | Limited to the observed 2025 coverage unless additional data is obtained |
| Complete Philippine offshore analysis | Not guaranteed by land/region polygons alone |

Overall, the datasets are **partially compatible**. They are suitable for the first data-pipeline experiments and regional visualization, but they are not sufficient for the requested provincial ranking feature.

## 8. Recommended next data-processing steps

1. Preserve the raw files and record their filenames, sizes, source names, and inspection date in a dataset manifest.
2. Obtain and inspect an ADM2/province boundary dataset before implementing province assignments.
3. Create a canonical earthquake schema while preserving the original USGS columns and event IDs.
4. Parse `time` and `updated` into UTC-aware timestamps.
5. Keep separate quality flags for missing fields, invalid coordinates, offshore/unassigned geography, and duplicate source IDs.
6. Define the Philippine analytical spatial scope explicitly. Do not silently use a rectangular bounding box as the final national definition.
7. Decide whether the study will include offshore events outside administrative polygons. The recommended default is to retain them and mark their administrative assignment as unassigned/offshore.
8. Validate and, if necessary, create a derived simplified working copy of the large boundary file. Never overwrite the original GeoJSON.
9. Add a documented region-to-island-group mapping only after reviewing the boundary names and approving the classification rules.
10. Generate a data-quality report after cleaning, including retained rows, excluded rows, and the reason for every exclusion.
11. Use a Jupyter Notebook for exploratory summaries and visual checks, while keeping reusable loading, validation, transformation, and spatial logic in Python modules.
12. Only after these decisions are documented should the cleaned development dataset be imported into PostgreSQL.

## 9. Current limitations

- The USGS file covers only 2025, not a long historical period.
- The observed minimum magnitude is 4.0; the original query/filter settings are not included in the CSV.
- The available boundary file is ADM1/region-level, not ADM2/province-level.
- Administrative polygons do not classify every offshore earthquake.
- The very large GeoJSON requires memory-conscious geometry validation and processing.
- Exact polygon containment counts were not used as a final filtering rule in this phase; the verified geographic comparison used the boundary layer's published extent and the USGS coordinates, while preserving the distinction between land-region membership and broader offshore Philippine relevance.

