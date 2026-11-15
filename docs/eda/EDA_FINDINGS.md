# Phase 4 Exploratory Data Analysis

This analysis uses the cleaned USGS 2025 development dataset. The results are provisional and descriptive; they are not earthquake predictions or final PHIVOLCS research conclusions.

## Dataset and scope

- Records analyzed: **794**
- Event coverage: **2025-01-01T18:39:33.615000+00:00** to **2025-12-31T17:30:42.385000+00:00** (UTC)
- Province-assigned records: **120**
- Philippine-labelled offshore/unassigned records: **652**
- Nearby-country candidates retained for review: **22**

## Descriptive findings

- Magnitude: mean **4.568**, median **4.500**, range **4.0–7.4**.
- Depth: mean **61.742 km**, median **35.000 km**, range **8.401–634.664 km**.
- The month with the most records was **2025-10** with **234** records.
- The ADM2 assignment covers **37** provinces in this dataset.

### Provinces with the most assigned records

| Province | Assigned records |
|---|---:|
| Cebu | 16 |
| Ilocos Norte | 7 |
| Surigao del Sur | 7 |
| Surigao del Norte | 6 |
| Leyte | 6 |

## Interpretation cautions

- Province counts describe only records whose coordinates intersected an ADM2 polygon. No nearest-province fallback was used.
- Offshore records are retained and visibly separated; excluding or including them in later research statistics requires an explicit study rule.
- The dataset covers one historical year. Time-based observations should not be described as current activity.
- These descriptive results do not establish causation, recurrence probability, risk, or prediction.

## Visualizations

- [Magnitude Distribution](figures/magnitude_distribution.png)
- [Depth Distribution](figures/depth_distribution.png)
- [Monthly Activity](figures/monthly_activity.png)
- [Geographical Distribution](figures/geographical_distribution.png)
- [Province Activity](figures/province_activity.png)
- [Magnitude Vs Depth](figures/magnitude_vs_depth.png)
