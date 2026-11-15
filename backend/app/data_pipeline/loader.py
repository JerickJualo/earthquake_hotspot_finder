"""Dataset loading functions."""

from pathlib import Path

import pandas as pd


def load_usgs_csv(path: Path) -> pd.DataFrame:
    """Load a USGS CSV without changing the original file."""

    if not path.exists():
        raise FileNotFoundError(f"USGS dataset not found: {path}")
    if path.suffix.lower() != ".csv":
        raise ValueError(f"Expected a CSV file, received: {path.name}")

    return pd.read_csv(path)
