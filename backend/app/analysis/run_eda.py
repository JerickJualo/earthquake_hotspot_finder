"""Command-line runner for Phase 4 exploratory analysis."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.analysis.eda import run_eda


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = PROJECT_ROOT / "backend/data/processed/cleaned_usgs_2025.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs/eda"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run_eda(args.input, args.output_dir)
    print(f"Created findings: {result['findings_path']}")
    print(f"Created figures: {len(result['figure_paths'])}")
    print(f"Created statistical files: {len(result['statistical_paths'])}")


if __name__ == "__main__":
    main()
