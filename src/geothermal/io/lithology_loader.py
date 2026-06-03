"""Loader for ``target_lithologies.csv`` — the per-sample reservoir table.

This is the file with the trap: every row is flagged ``check`` because the depth
columns hold **along-hole** values despite a ``..._tvd`` name, ``depth_tvd_m`` is
entirely empty, and porosity/density have gaps. We load it faithfully (no silent
fixes) so the petrophysics module can reconcile depths and impute gaps explicitly.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from geothermal import config

_DTYPES: dict[str, str] = {
    "well_id": "string",
    "easting": "float64",
    "northing": "float64",
    "depth_tvd_m": "float64",
    "porosity_pct": "float64",
    "gamma_ray_api": "float64",
    "bulk_density_gcc": "float64",
    "formation_top_tvd": "float64",
    "formation_base_tvd": "float64",
    "formation_thickness_m": "float64",
    "distance_to_usp_km": "float64",
    "flag": "string",
    "flag_reason": "string",
}


def load_target_lithologies(
    path: str | Path = config.TARGET_LITHOLOGIES_CSV,
) -> pd.DataFrame:
    """Load the target lithologies table with explicit dtypes, as-is.

    The misleadingly-named ``formation_top_tvd`` / ``formation_base_tvd`` columns are
    along-hole depths; petrophysics renames/reconciles them to true TVD downstream.
    """
    df = pd.read_csv(path)
    for col, dtype in _DTYPES.items():
        if col in df.columns:
            df[col] = df[col].astype(dtype)
    return df
