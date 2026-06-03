"""Single entry point for the clean, analysis-ready reservoir dataset.

Builds the full Phase-1 chain (assemble → impute porosity → derive permeability)
and caches it to parquet so downstream phases load instantly instead of rebuilding
from the raw LAS/Excel on every run.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from geothermal import config
from geothermal.petrophysics import add_permeability, build_reservoir_table, impute_porosity

DEFAULT_CACHE_PATH: Path = config.OUTPUTS_DIR / "clean_reservoir.parquet"


def build_clean_dataset() -> pd.DataFrame:
    """Build the clean per-sample reservoir dataset from raw inputs (no caching)."""
    return add_permeability(impute_porosity(build_reservoir_table()))


def clean_reservoir_dataset(
    *, refresh: bool = False, cache_path: Path = DEFAULT_CACHE_PATH
) -> pd.DataFrame:
    """Return the clean dataset, reading the parquet cache unless ``refresh`` is set."""
    if not refresh and cache_path.exists():
        return pd.read_parquet(cache_path)
    dataset = build_clean_dataset()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_parquet(cache_path, index=False)
    return dataset
