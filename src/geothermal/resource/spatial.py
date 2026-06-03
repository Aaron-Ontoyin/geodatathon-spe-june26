"""Spatial resource map across the Utrecht box and new-well siting (Phase 2).

With only four wells (two viable, two tight) a kriged surface would be badly
under-constrained, so we use **inverse-distance weighting** on log-transmissivity
and temperature — bounded by the data, transparent, and honest about its limits.
The map drives siting: a new doublet wants high interpolated power, adequate spacing
from existing wells, and proximity to the demand district (short pipelines).

A denser ThermoGIS regional grid would refine this; that enrichment is exactly what
the agentic workflow (Phase 5) automates.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from geothermal import config
from geothermal.io import load_thermogis
from geothermal.resource.assessment import locate_demand_center
from geothermal.resource.power import well_power_mw

FloatArray = npt.NDArray[np.float64]

_IDW_POWER = 2.0
_IDW_EPS = 1.0e-6
_GRID_MARGIN_M = 2000.0
_DEMAND_WEIGHT_MW_PER_KM = 0.1  # trade pipeline distance against deliverable power


@dataclass(frozen=True, slots=True)
class ResourceGrid:
    """Gridded resource properties over the area of interest (RD-New metres)."""

    x: FloatArray
    y: FloatArray
    transmissivity_dm: FloatArray
    temperature_c: FloatArray
    power_mw: FloatArray


def _well_arrays() -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
    tg = load_thermogis()
    xs, ys, trans, temps = [], [], [], []
    for wid in config.WELL_IDS:
        well = config.WELLS[wid]
        xs.append(well.x)
        ys.append(well.y)
        trans.append(tg[wid].value("Transmissivity"))
        temps.append(tg[wid].value("Temperature"))
    return (
        np.asarray(xs, dtype=float),
        np.asarray(ys, dtype=float),
        np.asarray(trans, dtype=float),
        np.asarray(temps, dtype=float),
    )


def interpolate_resource(
    query_x: npt.ArrayLike, query_y: npt.ArrayLike
) -> tuple[FloatArray, FloatArray]:
    """IDW-interpolate (transmissivity Dm, temperature °C) at the query points.

    Transmissivity is interpolated in log-space because it spans orders of magnitude.
    """
    qx = np.asarray(query_x, dtype=float)
    qy = np.asarray(query_y, dtype=float)
    wx, wy, wt, wtemp = _well_arrays()

    dist = np.hypot(qx[..., None] - wx, qy[..., None] - wy)
    weights = 1.0 / (dist**_IDW_POWER + _IDW_EPS)
    weights /= weights.sum(axis=-1, keepdims=True)

    log_trans = np.power(10.0, np.sum(weights * np.log10(wt), axis=-1))
    temperature = np.sum(weights * wtemp, axis=-1)
    return log_trans, temperature


def resource_grid(n: int = 80) -> ResourceGrid:
    """Build an n×n resource map over the wells' bounding box plus a margin."""
    wx, wy, _, _ = _well_arrays()
    xs = np.linspace(wx.min() - _GRID_MARGIN_M, wx.max() + _GRID_MARGIN_M, n)
    ys = np.linspace(wy.min() - _GRID_MARGIN_M, wy.max() + _GRID_MARGIN_M, n)
    grid_x, grid_y = np.meshgrid(xs, ys)
    transmissivity, temperature = interpolate_resource(grid_x, grid_y)
    power = well_power_mw(transmissivity, temperature)
    return ResourceGrid(
        x=grid_x,
        y=grid_y,
        transmissivity_dm=transmissivity,
        temperature_c=temperature,
        power_mw=power,
    )


def recommend_new_well(*, min_spacing_km: float = 1.5, grid_n: int = 120) -> dict[str, float]:
    """Recommend a new doublet location: high power, well-spaced, near the demand.

    Scores grid cells by ``power − weight · distance_to_demand`` among cells at least
    ``min_spacing_km`` from every existing well, and returns the best one.
    """
    grid = resource_grid(grid_n)
    usp_x, usp_y = locate_demand_center()
    wx, wy, _, _ = _well_arrays()

    nearest_well_km = (
        np.min(np.hypot(grid.x[..., None] - wx, grid.y[..., None] - wy), axis=-1) / 1000.0
    )
    demand_km = np.hypot(grid.x - usp_x, grid.y - usp_y) / 1000.0

    spaced = nearest_well_km >= min_spacing_km
    score = np.where(spaced, grid.power_mw - _DEMAND_WEIGHT_MW_PER_KM * demand_km, -np.inf)
    idx = np.unravel_index(int(np.argmax(score)), score.shape)
    return {
        "x": float(grid.x[idx]),
        "y": float(grid.y[idx]),
        "transmissivity_dm": float(grid.transmissivity_dm[idx]),
        "temperature_c": float(grid.temperature_c[idx]),
        "power_mw_p50": float(grid.power_mw[idx]),
        "distance_to_usp_km": float(demand_km[idx]),
        "distance_to_blt_km": float(
            np.hypot(grid.x[idx] - config.WELLS["BLT-01"].x, grid.y[idx] - config.WELLS["BLT-01"].y)
            / 1000.0
        ),
    }
