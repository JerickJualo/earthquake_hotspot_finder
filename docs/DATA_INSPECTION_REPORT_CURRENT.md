# Current Phase 1 Data Inspection Report

**Inspection date:** 2026-11-15  
**Active USGS file:** `backend/data/raw/usgs/accurate_2025_usgs_dataset.csv`  
**Active boundary file:** `backend/data/boundaries/geoBoundaries-PHL-ADM2.geojson`  
**Original files:** Preserved and not modified

This report supersedes the earlier audit that used the original `usgs_earthquake_dataset.csv` and the ADM1 boundary file.

## 1. Executive summary

The replacement files are much better aligned with the project requirements:

- The USGS CSV contains **794 records covering January 1 through December 31, 2025 UTC**.
- The CSV has **22 columns**, no missing values, no duplicate event IDs, and no basic numeric or coordinate violations.
- **772 records** have location descriptions containing “Philippines.” The remaining **22 records** are labelled as Taiwan, Indonesia, or Malaysia and should not be included automatically in a Philippines-only analysis.
- The geoBoundaries file contains **86 `ADM2` features**, which are province-level boundaries and are suitable for provincial assignment in principle.
- Both datasets use longitude/latitude conventions compatible with **WGS84 / EPSG:4326**.

The datasets are now compatible for the intended provincial analysis, with two important cautions: offshore events may not intersect a province polygon, and the USGS file contains nearby non-Philippine events that require an explicit geographic filtering rule.

## 2. File audit

| File | Size | Format |
|---|---:|---|
| `accurate_2025_usgs_dataset.csv` | 152,686 bytes | CSV |
| `geoBoundaries-PHL-ADM2.geojson` | 444,406,710 bytes, approximately 444.4 MB | GeoJSON |

The previous files remain in the workspace for reference. They were not overwritten.

## 3. USGS dataset findings

### 3.1 Count and date coverage

- Records: **794**
- Columns: **22**
- Earliest event: **2025-01-01 18:39:33.615 UTC**
- Latest event: **2025-12-31 17:30:42.385 UTC**
- Event coverage: **the complete 2025 calendar year**
- `updated` timestamps parse successfully and range from **2025-03-17** through **2026-09-06 UTC**.

The observed minimum magnitude is 4.0. This may reflect the original USGS search settings, but the CSV does not include the original search URL or query parameters, so the filtering rule should be documented as “observed in the file” rather than assumed.

### 3.2 Columns and observed types

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

Observed categorical values:

- `magType`: 724 `mb`, 67 `mww`, 3 `mwr`
- `net`: all 794 are `us`
- `type`: all 794 are `earthquake`
- `status`: all 794 are `reviewed`
- `locationSource`: all 794 are `us`
- `magSource`: all 794 are `us`

### 3.3 Missing, duplicate, and invalid values

The current CSV contains:

- Missing values: **0 in every column**
- Duplicate complete rows: **0**
- Duplicate non-null event IDs: **0**
- Unique non-null event IDs: **794**
- Invalid `time` timestamps: **0**
- Invalid `updated` timestamps: **0**
- Non-numeric values in numeric fields: **0**
- Non-finite numeric values: **0**
- Latitude outside -90 to 90 degrees: **0**
- Longitude outside -180 to 180 degrees: **0**
- Missing latitude/longitude pairs: **0**
- Negative depths: **0**

Observed ranges:

| Field | Minimum | Maximum | Summary |
|---|---:|---:|---|
| Latitude | 4.0214 | 21.9585 | Basic coordinate range is valid |
| Longitude | 116.7771 | 127.9340 | Includes nearby countries and offshore areas |
| Depth | 8.401 km | 634.664 km | No negative depths |
| Magnitude | 4.0 | 7.4 | Mean 4.5684; median 4.5 |

“No missing values” means every row is complete at the file level. It does not mean every record belongs inside the Philippines or that the catalogue is complete for all earthquake magnitudes.

## 4. Philippine geographic coverage

The `place` field contains “Philippines” in **772 of 794 records**. The **22 records without that label** are:

- 18 records labelled near Hengchun or Donggang, Taiwan
- 3 records north of Tobelo, Indonesia
- 1 record south-west of Kudat, Malaysia

Therefore, the dataset contains nearby non-Philippine earthquakes and must not be used without a geographic inclusion rule.

The USGS coordinate extent is:

- Latitude: **4.0214 to 21.9585**
- Longitude: **116.7771 to 127.9340**

The ADM2 boundary layer extent is approximately:

- Longitude: **114.2779 to 126.6050**
- Latitude: **4.5873 to 21.1219**

Using the boundary layer’s rectangular extent only as a diagnostic, 314 records fall outside that rectangle. This is not a final country filter because a rectangle is not a country boundary and because offshore Philippine earthquakes can legitimately lie outside administrative land polygons. The actual Philippines inclusion rule must be documented before cleaning.

## 5. geoBoundaries ADM2 findings

### 5.1 Administrative level

The file is named `geoBoundaries-PHL-ADM2.geojson`, and all 86 features have `shapeType = ADM2`.

The feature attributes include:

`shapeName`, `shapeISO`, `shapeID`, `shapeGroup`, and `shapeType`.

There are **86 unique `shapeName` values**, including province names such as Abra, Agusan del Norte, Aklan, Albay, Antique, Apayao, Aurora, Basilan, Bataan, Batangas, Benguet, Biliran, Bohol, Bukidnon, Bulacan, Cagayan, Camarines Norte, and Camarines Sur.

This is the required administrative level for province-level earthquake assignments.

### 5.2 Boundary metadata

- Feature count: **86**
- CRS reported by the geospatial reader: **EPSG:4326**
- Encoding: **UTF-8**
- Geometry types: **62 MultiPolygon** and **24 Polygon**
- Geometry type present for all 86 features inspected structurally
- Overall bounds: `[114.277892253, 4.587294497000073, 126.60496559600006, 21.12188547900007]`

The GeoJSON is unusually large because its province geometries contain highly detailed coastline coordinates. The original file must remain preserved. Any simplification for web display or faster spatial processing should be written as a separate derived file and documented.

A full in-memory topology-validity pass was not used during this audit because of the file size. The layer was structurally inspected for feature count, attributes, CRS, geometry types, and geometry presence. A memory-conscious geometry-validity check should be completed before production import.

## 6. Can the data support provincial assignments?

**Yes, in principle.**

The ADM2 layer provides province-level polygons and province names, while the USGS file provides latitude and longitude for every record. The required operation is a point-in-polygon spatial join.

The processing must still handle these cases explicitly:

- Philippine offshore earthquakes that do not intersect a province polygon
- Non-Philippine events in the USGS download
- Events exactly on a province boundary
- Province geometry validity and any overlapping polygons
- Whether a province assignment is based on land polygons only or on a separate study-area definition

Do not assign an offshore event to the nearest province unless that rule is explicitly approved and documented.

## 7. Dataset compatibility

| Requirement | Assessment |
|---|---|
| Plot earthquake points with province boundaries | Compatible; both use longitude/latitude consistent with EPSG:4326 |
| Assign events to provinces | Supported by ADM2 point-in-polygon processing |
| Province rankings | Supported after geographic filtering and assignment rules are defined |
| Island-group filtering | Requires a documented province-to-island-group mapping |
| Date and magnitude filters | Supported by the USGS fields |
| K-Means clustering | Supported, but the geographic inclusion rule and coordinate treatment must be documented |
| Historical analysis | Supported for the 2025 year; broader conclusions require more years of data |
| Offshore analysis | Requires a separate unassigned/offshore policy |

Overall, the replacement datasets are **compatible with the project’s intended geographic analysis**, including provincial analysis. They are not automatically clean for a Philippines-only study because 22 nearby non-Philippine records are present.

## 8. Recommended next data-processing steps

1. Preserve both raw files and record the active filenames, sizes, and inspection date.
2. Define the official Philippines inclusion rule before filtering. Do not use the rectangular extent as the final rule.
3. Keep all raw USGS rows, but add an analysis-scope flag such as `is_philippines_candidate` and a documented reason for exclusions.
4. Use the ADM2 layer for point-in-polygon province assignment.
5. Retain valid offshore events with `province_id = NULL` and an explicit `geographic_assignment_status` such as `offshore_or_unassigned`.
6. Validate province geometries before production import. If a simplified copy is needed, preserve the original ADM2 GeoJSON and document the simplification tolerance.
7. Normalize province names and create a reviewed province-to-island-group reference table.
8. Transform the USGS columns into the canonical schema while preserving all source columns and event IDs.
9. Use a Jupyter Notebook for exploratory summaries, maps, and quality checks; keep reusable cleaning and spatial logic in Python modules.
10. Generate a second data-quality report after filtering and spatial assignment, showing retained Philippine events, excluded nearby-country events, and unassigned offshore events.
11. Only after these rules are reviewed should the cleaned dataset be loaded into PostgreSQL.

