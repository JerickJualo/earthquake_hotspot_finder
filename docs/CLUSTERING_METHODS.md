# Phase 5 Clustering Methods

## Scope and input

Phase 5 uses `backend/data/processed/cleaned_usgs_2025.csv`, the output of Phase 3. The clustering service uses only geographic coordinates as features. Magnitude, depth, and time are not used to create the cluster labels; they are summarized afterward.

By default, records with Phase 3 statuses `assigned` and `offshore_or_unassigned` are eligible. The 22 `outside_study_scope_candidate` records are retained in the clustered output but receive null cluster labels. This is a configurable development choice and must be reviewed before final research analysis.

## Coordinate preparation and transformation

Coordinates begin in WGS84 geographic coordinates (`EPSG:4326`). They are transformed to a local WGS84 azimuthal-equidistant projection centered on the Philippines (`12.8797°N, 121.7740°E`). This gives K-Means metric inputs in meters rather than mixing degrees of latitude and longitude.

Rows with missing, non-finite, or out-of-range coordinates are retained with `excluded_invalid_coordinates` status and are not clustered. No artificial coordinates are imputed.

## K-Means procedure

1. Evaluate K values from 2 through 8 using the projected coordinate matrix.
2. Calculate inertia, silhouette score, Calinski-Harabasz score, and Davies-Bouldin score.
3. Select the K with the highest silhouette score; use the lower K only if scores tie.
4. Fit deterministic K-Means with `random_state=42`, `n_init=20`.
5. Canonicalize labels by projected centroid position so labels are reproducible identifiers rather than raw library labels.
6. Calculate cluster sizes, percentages, centroids, geographic ranges, mean and maximum magnitude, mean depth, and assigned-province summaries.

The default run selected K=2 from 772 eligible records. Its silhouette score was 0.6716. This metric describes separation under the selected representation; it does not prove a geological boundary or a hazard hotspot.

## Edge cases and safety rules

- Empty or out-of-scope inputs raise a clear error instead of producing fabricated clusters.
- K values greater than the number of records or unique coordinate points are rejected or marked skipped during evaluation.
- Duplicate coordinates are allowed when the requested K does not exceed the number of unique coordinate points.
- Excluded rows remain in the output with explicit status and null cluster labels.
- The raw datasets and the cleaned Phase 3 dataset are never overwritten.

## Outputs and rerun command

Run from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m app.services.run_clustering
```

The reusable service is `backend/app/services/clustering_service.py`. Generated development artifacts are:

- `backend/data/processed/clustered_usgs_2025.csv`
- `docs/clustering/cluster_evaluation.csv`
- `docs/clustering/cluster_metadata.json`
- `docs/clustering/cluster_summaries.csv`
- `docs/clustering/CLUSTERING_FINDINGS.md`
- `docs/clustering/figures/`

## Interpretation limits

K-Means creates compact distance-based partitions. It is not a density estimator, recurrence model, risk model, or earthquake prediction method. Results can change when the source catalogue, spatial inclusion rule, projection, or requested K changes. All USGS results are provisional and must be rerun after the PHIVOLCS dataset is independently inspected and imported.
