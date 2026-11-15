# Phase 5 Geographical Clustering Findings

This report describes K-Means groupings in the provisional USGS 2025 development dataset. A cluster is a spatial grouping produced by the algorithm; it is not a confirmed earthquake hotspot, hazard ranking, recurrence estimate, or prediction.

## Configuration

- Records included in clustering: **772**
- Records excluded from clustering: **22**
- Selected number of clusters (K): **2**
- Silhouette score for selected K: **0.6716**
- Coordinate transformation: **WGS84 local azimuthal equidistant projection centered on the Philippines**
- Included assignment statuses: `assigned, offshore_or_unassigned`

The 22 nearby-country candidates were excluded because their Phase 3 status was `outside_study_scope_candidate`. They remain in the cleaned dataset and clustered output with null cluster labels.

## Candidate-K evaluation

The selected K maximizes the silhouette score among K=2 through K=8, with lower K preferred only when scores tie. Higher silhouette values indicate better separation under this metric; they do not prove geological or hazard significance.

| K | Inertia (m2) | Silhouette | Calinski-Harabasz | Davies-Bouldin |
|---:|---:|---:|---:|---:|
| 2 | 62831680734024.80 | 0.6716 | 1795.48 | 0.4888 |
| 3 | 32053212035831.47 | 0.5672 | 2126.70 | 0.6001 |
| 4 | 23736293670889.83 | 0.5542 | 2001.79 | 0.6093 |
| 5 | 15911789569108.48 | 0.5028 | 2330.99 | 0.6522 |
| 6 | 13021944349500.57 | 0.5121 | 2309.66 | 0.6392 |
| 7 | 10311397270096.77 | 0.5138 | 2461.08 | 0.6528 |
| 8 | 8939683729119.33 | 0.5178 | 2446.67 | 0.6952 |

## Cluster summaries

| Cluster | Records | Share | Centroid latitude | Centroid longitude | Mean magnitude | Mean depth (km) | Top assigned province |
|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | 142 | 18.39% | 16.7319 | 121.2983 | 4.594 | 47.630 | Ilocos Norte |
| 1 | 630 | 81.61% | 7.6934 | 126.0295 | 4.564 | 65.250 | Cebu |

## Interpretation limits

- K-Means uses projected longitude/latitude only. Magnitude, depth, and time are summarized after clustering and do not influence the labels.
- K-Means prefers roughly compact, distance-based groups and can be sensitive to the chosen K and study scope.
- Offshore records labelled as Philippine events are included by default; this is a configurable development choice, not a final research decision.
- Cluster labels are identifiers, not rankings. A larger cluster does not mean greater hazard.
- The results use one historical year of USGS data and must be rerun after PHIVOLCS data is inspected and imported.

## Figures

- [Geographical clusters](figures/geographic_clusters.png)
- [Cluster sizes](figures/cluster_sizes.png)
