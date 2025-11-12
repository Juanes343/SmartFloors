"""Data ingestion utilities for SmartFloors."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

DATA_COLUMNS = [
    "timestamp",
    "edificio",
    "piso",
    "temp_c",
    "humedad_pct",
    "energia_kw",
]


def load_dataset(path: Optional[Path] = None) -> pd.DataFrame:
    """Load the SmartFloors dataset.

    Parameters
    ----------
    path:
        Optional path to a CSV file. When omitted, the default dataset shipped with the
        project (``data/smartfloors_sample.csv``) is used.

    Returns
    -------
    pandas.DataFrame
        DataFrame with parsed timestamps and the expected column names.
    """

    if path is None:
        path = Path(__file__).resolve().parent.parent / "data" / "smartfloors_sample.csv"

    df = pd.read_csv(path, parse_dates=["timestamp"])
    missing = [col for col in DATA_COLUMNS if col not in df.columns]
    if missing:
        missing_str = ", ".join(missing)
        raise ValueError(f"El dataset no contiene las columnas requeridas: {missing_str}.")

    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


__all__ = ["load_dataset", "DATA_COLUMNS"]
