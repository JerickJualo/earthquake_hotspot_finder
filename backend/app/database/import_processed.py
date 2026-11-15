"""Command-line importer for the Phase 3 processed dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.core.config import settings
from app.database.connection import SessionLocal
from app.database.import_service import import_processed_dataset


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = PROJECT_ROOT / "backend/data/processed/clustered_usgs_2025.csv"
DEFAULT_CLUSTER_METADATA = PROJECT_ROOT / "docs/clustering/cluster_metadata.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--import-id", default="usgs-2025-development-v1")
    parser.add_argument("--source-name", default="USGS")
    parser.add_argument("--dataset-version", default="2025-development")
    parser.add_argument("--cluster-metadata", type=Path, default=DEFAULT_CLUSTER_METADATA)
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Replace only records owned by the specified import ID.",
    )
    args = parser.parse_args()
    settings.require_configured_database_url()
    with SessionLocal() as session:
        result = import_processed_dataset(
            session,
            args.input,
            import_id=args.import_id,
            source_name=args.source_name,
            dataset_version=args.dataset_version,
            replace_existing=args.replace_existing,
            cluster_metadata_path=args.cluster_metadata,
        )
    print(result)


if __name__ == "__main__":
    main()
