"""The property-provider seam: 'reservoir properties at (x, y)', source-agnostic.

Everything downstream (siting, capacity, Monte-Carlo) depends only on SiteProperties,
so the backing source (ThermoGIS grid now, full-percentile grid or live API later) can
change without touching the search or the cost model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np

from geothermal import config
from geothermal.resource.thermogis_grid import Scenario, grid_path, value_at

Source = Literal["measured", "thermogis_grid"]


@dataclass(frozen=True, slots=True)
class SiteProperties:
    """Reservoir properties at one location, plus its uncertainty and provenance."""

    x: float
    y: float
    transmissivity_dm: float
    temperature_c: float
    power_mw_p50: float
    depth_m: float
    sigma_log_trans: float
    source: Source


def grid_properties_at(
    root: Path,
    x: float,
    y: float,
    *,
    scenario: Scenario,
    min_dist_km: float,
    base_sigma_log_trans: float,
    sigma_interp_per_km: float,
) -> SiteProperties:
    """Assemble SiteProperties from the ThermoGIS grids at (x, y).

    ``min_dist_km`` is the distance to the nearest logged well; it inflates the modelled
    uncertainty because the P50 grid is less trustworthy far from real data. At a well
    (``min_dist_km`` ~ 0) the band collapses to ``base_sigma_log_trans`` (the narrow,
    measured-anchored width).
    """

    def g(prop: str) -> float:
        return value_at(grid_path(root, scenario=scenario, prop=prop), x, y)

    perm = g("permeability_p50")
    thick = g("thickness_p50")
    ntg = g("net_to_gross")
    transmissivity = perm * thick * ntg / 1000.0
    sigma = math.sqrt(base_sigma_log_trans**2 + (sigma_interp_per_km * min_dist_km) ** 2)
    return SiteProperties(
        x=x,
        y=y,
        transmissivity_dm=transmissivity,
        temperature_c=g("temperature"),
        power_mw_p50=g("power_p50"),
        depth_m=g("depth"),
        sigma_log_trans=sigma,
        source="thermogis_grid",
    )


def nearest_well_km(x: float, y: float) -> float:
    """Distance (km) from (x, y) to the nearest of the four logged wells."""
    d = [np.hypot(x - config.WELLS[w].x, y - config.WELLS[w].y) for w in config.WELL_IDS]
    return float(min(d) / 1000.0)
