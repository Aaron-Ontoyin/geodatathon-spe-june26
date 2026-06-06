"""Area-of-interest siting: candidate generation over the demand-centred box.

Candidates are a regular lattice (pitch = min well spacing) unioned with the four wells
at their exact coordinates, deduped so no pair is closer than the pitch. All candidates
are equal; only their properties (and uncertainty) differ.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np
import numpy.typing as npt

from geothermal import config
from geothermal.assumptions import DEFAULT_ASSUMPTIONS, Assumptions
from geothermal.resource.properties import SiteProperties, grid_properties_at, nearest_well_km
from geothermal.resource.thermogis_grid import Scenario

FloatArray = npt.NDArray[np.float64]

SiteProvider = Callable[[float, float], SiteProperties]


def candidate_lattice(
    *, center: tuple[float, float], size_km: float, pitch_km: float
) -> FloatArray:
    """Return an (N, 2) array of candidate (x, y) points: lattice union wells, deduped to pitch."""
    cx, cy = center
    half = size_km * 1000.0 / 2.0
    pitch = pitch_km * 1000.0
    xs = np.arange(cx - half, cx + half + 1e-6, pitch)
    ys = np.arange(cy - half, cy + half + 1e-6, pitch)
    gx, gy = np.meshgrid(xs, ys)
    lattice = np.column_stack([gx.ravel(), gy.ravel()])

    wells = np.array([[config.WELLS[w].x, config.WELLS[w].y] for w in config.WELL_IDS], dtype=float)
    in_box = (np.abs(wells[:, 0] - cx) <= half) & (np.abs(wells[:, 1] - cy) <= half)
    wells_in = wells[in_box]

    if wells_in.size:
        d = np.hypot(
            lattice[:, None, 0] - wells_in[None, :, 0],
            lattice[:, None, 1] - wells_in[None, :, 1],
        )
        keep = d.min(axis=1) >= pitch
        lattice = lattice[keep]
        return np.vstack([wells_in, lattice])
    return lattice


def build_candidates(
    points: FloatArray, *, provider: SiteProvider, viability_floor_mw: float
) -> list[SiteProperties]:
    """Evaluate provider at each point, keeping finite, present, viable cells."""
    out: list[SiteProperties] = []
    for x, y in points:
        sp = provider(float(x), float(y))
        if np.isfinite(sp.power_mw_p50) and sp.power_mw_p50 >= viability_floor_mw:
            out.append(sp)
    return out


def shortlist(sites: list[SiteProperties], *, size: int) -> list[SiteProperties]:
    """Strongest `size` sites by P50 power (the program search runs over these)."""
    return sorted(sites, key=lambda s: s.power_mw_p50, reverse=True)[:size]


def shortlist_from_grid(
    root: Path,
    *,
    assumptions: Assumptions = DEFAULT_ASSUMPTIONS,
    scenario: Scenario = "heat_pump",
) -> list[SiteProperties]:
    """Full grid-backed candidate pipeline: lattice -> properties -> filter -> shortlist."""
    a = assumptions
    pts = candidate_lattice(
        center=a.aoi_center_rd, size_km=a.aoi_size_km, pitch_km=a.min_well_spacing_km
    )

    def provider(x: float, y: float) -> SiteProperties:
        return grid_properties_at(
            root,
            x,
            y,
            scenario=scenario,
            min_dist_km=nearest_well_km(x, y),
            base_sigma_log_trans=a.base_sigma_log_trans,
            sigma_interp_per_km=a.sigma_interp_per_km,
        )

    sites = build_candidates(pts, provider=provider, viability_floor_mw=a.viability_floor_mw)
    return shortlist(sites, size=a.shortlist_size)
