"""Read the ThermoGIS regional NetCDF property grids (1 km, RD-New metres).

Each file holds a single ``data`` variable on (y, x) coordinates. We never modify the
grids; we crop to the area of interest and look up the nearest cell at a query point.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np
import numpy.typing as npt
import xarray as xr

FloatArray = npt.NDArray[np.float64]

Scenario = Literal["basecase", "heat_pump", "well_stimulation", "well_stimulation_heat_pump"]

_SCENARIO_DIR: dict[str, str] = {
    "basecase": "BaseCase",
    "heat_pump": "Heat Pump",
    "well_stimulation": "Well Stimulation",
    "well_stimulation_heat_pump": "Well Stimulation & Heat Pump",
}
_SCENARIO_SUFFIX: dict[str, str] = {
    "basecase": "",
    "heat_pump": "_HP",
    "well_stimulation": "_STIM",
    "well_stimulation_heat_pump": "_STIM_HP",
}
_RESERVOIR_DIR = "6_Permian/Upper Rotliegend Gp (RO)"


def value_at(path: Path, x: float, y: float) -> float:
    """Nearest-cell value of the grid in ``path`` at RD coordinate (x, y)."""
    with xr.open_dataset(path) as ds:
        return float(ds["data"].sel(x=x, y=y, method="nearest").values)


def crop_box(
    path: Path, *, center: tuple[float, float], size_m: float
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Return (xs, ys, values) for the square box of side ``size_m`` centred on ``center``."""
    cx, cy = center
    half = size_m / 2.0
    with xr.open_dataset(path) as ds:
        sub = ds["data"].sel(x=slice(cx - half, cx + half), y=slice(cy - half, cy + half))
        return (
            np.asarray(sub["x"].values, dtype=float),
            np.asarray(sub["y"].values, dtype=float),
            np.asarray(sub.values, dtype=float),
        )


def grid_path(root: Path, *, scenario: Scenario, prop: str) -> Path:
    """Path to a ThermoGIS property grid for the Rotliegend, given scenario and property."""
    return (
        Path(root) / _RESERVOIR_DIR / _SCENARIO_DIR[scenario]
        / f"RO_STACKED_{prop}{_SCENARIO_SUFFIX[scenario]}.nc"
    )
