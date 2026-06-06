"""Multi-location doublet-program search.

A 'program' is a set of chosen doublet sites. Capacity is additive across sites; the
LCoE is computed once at the system level (shared surface plant + demand saturation).
Each site's wells are costed at its OWN depth (per-site well CAPEX, summed), so deeper
sites genuinely cost more, the depth signal is not averaged away.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

import numpy as np

from geothermal.assumptions import DEFAULT_ASSUMPTIONS, Assumptions
from geothermal.design import district_demand, simulate
from geothermal.economics.costs import SystemCosts, evaluate_costs
from geothermal.economics.optimization import design_for
from geothermal.economics.well_cost import well_capex_meur
from geothermal.resource.power import well_power_mw
from geothermal.resource.properties import SiteProperties


@dataclass(frozen=True, slots=True)
class Program:
    """A chosen set of doublet sites with its sized system, cost and feasibility."""

    sites: tuple[SiteProperties, ...]
    n_doublets: int
    geo_capacity_mw: float
    backup_fraction: float
    meets_demand: bool
    lcoe_eur_per_gj: float
    capex_meur: float
    costs: SystemCosts


def evaluate_program(
    sites: list[SiteProperties], *, assumptions: Assumptions = DEFAULT_ASSUMPTIONS
) -> Program:
    """Size, simulate and cost the integrated system for a chosen set of doublet sites."""
    a = assumptions
    geo = sum(
        float(well_power_mw(s.transmissivity_dm, s.temperature_c, injection_temp_c=a.injection_temp_c))  # noqa: E501
        for s in sites
    )
    design = design_for(geo, a)
    perf = simulate(design, district_demand(assumptions=a))
    wells_capex = sum(
        2.0 * well_capex_meur(s.depth_m * a.well_curvature_factor) for s in sites
    ) + len(sites) * a.pump_cost_meur
    transmission = _transmission_capex_meur(sites, a)
    costs = evaluate_costs(
        len(sites), design, perf, assumptions=a,
        wells_capex_meur=wells_capex, transmission_capex_meur=transmission,
    )
    backup = perf.backup_heat_gj / perf.heat_delivered_gj if perf.heat_delivered_gj else 1.0
    return Program(
        sites=tuple(sites),
        n_doublets=len(sites),
        geo_capacity_mw=geo,
        backup_fraction=backup,
        meets_demand=backup <= a.max_backup_fraction,
        lcoe_eur_per_gj=costs.lcoe_eur_per_gj,
        capex_meur=costs.capex_meur,
        costs=costs,
    )


def search_program(
    shortlist: list[SiteProperties],
    *,
    assumptions: Assumptions = DEFAULT_ASSUMPTIONS,
    min_spacing_km: float,
) -> Program | None:
    """Exhaustively search programs of size 1..N for the least-LCoE feasible one.

    Stops growing k once the best feasible LCoE at size k is no better than at k-1
    (LCoE is U-shaped in doublet count). Returns None if nothing is feasible.
    """
    min_spacing_m = min_spacing_km * 1000.0
    best: Program | None = None
    best_at_prev = float("inf")
    for k in range(1, min(len(shortlist), assumptions.max_program_doublets) + 1):
        best_k: Program | None = None
        for combo in itertools.combinations(shortlist, k):
            if not _spaced(combo, min_spacing_m):
                continue
            prog = evaluate_program(list(combo), assumptions=assumptions)
            if not prog.meets_demand:
                continue
            if best_k is None or prog.lcoe_eur_per_gj < best_k.lcoe_eur_per_gj:
                best_k = prog
        if best_k is None:
            continue
        if best is None or best_k.lcoe_eur_per_gj < best.lcoe_eur_per_gj:
            best = best_k
        if best_k.lcoe_eur_per_gj >= best_at_prev:
            break
        best_at_prev = best_k.lcoe_eur_per_gj
    return best


def program_monte_carlo(
    sites: list[SiteProperties],
    *,
    assumptions: Assumptions = DEFAULT_ASSUMPTIONS,
    n_samples: int = 2000,
    seed: int = 42,
) -> dict[str, float]:
    """LCoE band for a program, drawing each site's transmissivity independently.

    Each scenario: draw one lognormal transmissivity per site (its own median + sigma),
    sum the per-site capacities, then compute the system LCoE once.
    """
    a = assumptions
    rng = np.random.default_rng(seed)
    demand = district_demand(assumptions=a)
    mu = np.array([np.log(max(s.transmissivity_dm, 1e-6)) for s in sites])
    sigma = np.array([s.sigma_log_trans for s in sites])
    # depth and location are not stochastic, so wells CAPEX and transmission are the same
    # every scenario: compute once.
    wells_capex = sum(
        2.0 * well_capex_meur(s.depth_m * a.well_curvature_factor) for s in sites
    ) + len(sites) * a.pump_cost_meur
    transmission = _transmission_capex_meur(sites, a)

    lcoes = np.empty(n_samples, dtype=float)
    for i in range(n_samples):
        draws = rng.lognormal(mu, sigma)
        geo = sum(
            float(well_power_mw(t, s.temperature_c, injection_temp_c=a.injection_temp_c))
            for t, s in zip(draws, sites, strict=True)
        )
        design = design_for(geo, a)
        perf = simulate(design, demand)
        lcoes[i] = evaluate_costs(
            len(sites), design, perf, assumptions=a,
            wells_capex_meur=wells_capex, transmission_capex_meur=transmission,
        ).lcoe_eur_per_gj
    return {
        "p10": float(np.percentile(lcoes, 10)),
        "p50": float(np.percentile(lcoes, 50)),
        "p90": float(np.percentile(lcoes, 90)),
        "mean": float(lcoes.mean()),
    }


def _spaced(combo: tuple[SiteProperties, ...], min_spacing_m: float) -> bool:
    for a_site, b_site in itertools.combinations(combo, 2):
        if np.hypot(a_site.x - b_site.x, a_site.y - b_site.y) < min_spacing_m:
            return False
    return True


def _transmission_capex_meur(
    sites: tuple[SiteProperties, ...] | list[SiteProperties], a: Assumptions
) -> float:
    """Pipeline CAPEX (M€): each site connects to the demand district at a.aoi_center_rd."""
    cx, cy = a.aoi_center_rd
    return sum(
        a.transmission_meur_per_km * float(np.hypot(s.x - cx, s.y - cy)) / 1000.0 for s in sites
    )
