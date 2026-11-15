"""Command-line runner for Phase 5 geographical K-Means clustering."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.services.clustering_service import ClusteringConfig, run_clustering


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = PROJECT_ROOT / "backend/data/processed/cleaned_usgs_2025.csv"
DEFAULT_OUTPUT_DATASET = PROJECT_ROOT / "backend/data/processed/clustered_usgs_2025.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs/clustering"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dataset", type=Path, default=DEFAULT_OUTPUT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--min-k", type=int, default=2)
    parser.add_argument("--max-k", type=int, default=8)
    args = parser.parse_args()
    result = run_clustering(
        args.input,
        args.output_dataset,
        args.output_dir,
        config=ClusteringConfig(min_k=args.min_k, max_k=args.max_k),
    )
    print(f"Selected K: {result['metadata']['selected_k']}")
    print(f"Clustered records: {result['metadata']['eligible_record_count']}")
    print(f"Created dataset: {args.output_dataset}")
    print(f"Created results: {args.output_dir}")


if __name__ == "__main__":
    main()
