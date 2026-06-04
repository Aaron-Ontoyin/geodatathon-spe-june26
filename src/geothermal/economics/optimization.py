"""Least-LCoE design optimisation and Monte-Carlo LCoE bands (Phase 4).

Couples resource (Phase 2 power), design (Phase 3 dispatch) and cost (Phase 4) into
a single evaluation, sweeps the design space for the minimum-LCoE system that meets
the demand without leaning on backup, and propagates the (large) transmissivity
uncertainty into an LCoE P10/P50/P90 band.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from geothermal.design import SystemDesign, district_demand, heating_capacity_mw, simulate
from geothermal.economics.costs import SystemCosts, evaluate_costs
from geothermal.resource.power import well_power_mw

# A favourable BLT-class doublet in the NE trend (the sited target).
REPRESENTATIVE_TRANSMISSIVITY_DM = 9.0
REPRESENTATIVE_TEMPERATURE_C = 77.0
DESIGN_INJECTION_TEMP_C = 30.0  # heat-pump-assisted district-heating return
MAX_BACKUP_FRACTION = 0.15  # a geothermal-based system, not a gas plant in disguise

# Transmissivity P90 / P50 / P10 (Dm) for a BLT-class location — wide uncertainty.
_TRANS_P90, _TRANS_P50, _TRANS_P10 = 1.3, 9.3, 66.1
_Z80 = 1.2816  # z-score for the P10/P90 (10/90) lognormal span


def doublet_capacity_mw(
    injection_temp_c: float = DESIGN_INJECTION_TEMP_C,
    *,
    transmissivity_dm: float = REPRESENTATIVE_TRANSMISSIVITY_DM,
    temperature_c: float = REPRESENTATIVE_TEMPERATURE_C,
) -> float:
    """Thermal capacity (MW) of one representative doublet at a chosen injection temp."""
    return float(well_power_mw(transmissivity_dm, temperature_c, injection_temp_c=injection_temp_c))


@dataclass(frozen=True, slots=True)
class DesignCandidate:
    """A sized design with its performance, cost and feasibility."""

    n_doublets: int
    injection_temp_c: float
    heat_pump_cop: float
    geo_capacity_mw: float
    heating_capacity_mw: float
    backup_fraction: float
    meets_demand: bool
    lcoe_eur_per_gj: float
    capex_meur: float
    costs: SystemCosts


def evaluate_candidate(
    n_doublets: int,
    *,
    injection_temp_c: float = DESIGN_INJECTION_TEMP_C,
    heat_pump_cop: float = 4.5,
) -> DesignCandidate:
    """Build, simulate and cost one design; flag whether it meets demand on geothermal."""
    geo_capacity = n_doublets * doublet_capacity_mw(injection_temp_c)
    design = SystemDesign(geo_capacity_mw=geo_capacity, heat_pump_cop=heat_pump_cop)
    perf = simulate(design, district_demand())
    costs = evaluate_costs(n_doublets, design, perf)
    backup_fraction = (
        perf.backup_heat_gj / perf.heat_delivered_gj if perf.heat_delivered_gj else 1.0
    )
    return DesignCandidate(
        n_doublets=n_doublets,
        injection_temp_c=injection_temp_c,
        heat_pump_cop=heat_pump_cop,
        geo_capacity_mw=geo_capacity,
        heating_capacity_mw=heating_capacity_mw(design),
        backup_fraction=backup_fraction,
        meets_demand=backup_fraction <= MAX_BACKUP_FRACTION,
        lcoe_eur_per_gj=costs.lcoe_eur_per_gj,
        capex_meur=costs.capex_meur,
        costs=costs,
    )


def optimize(
    *,
    doublet_options: tuple[int, ...] = (1, 2, 3),
    injection_temp_c: float = DESIGN_INJECTION_TEMP_C,
    heat_pump_cop: float = 4.5,
) -> list[DesignCandidate]:
    """Return feasible designs sorted by ascending LCoE (best first)."""
    candidates = [
        evaluate_candidate(n, injection_temp_c=injection_temp_c, heat_pump_cop=heat_pump_cop)
        for n in doublet_options
    ]
    feasible = [c for c in candidates if c.meets_demand]
    return sorted(feasible, key=lambda c: c.lcoe_eur_per_gj)


def monte_carlo_lcoe_samples(
    n_doublets: int,
    *,
    injection_temp_c: float = DESIGN_INJECTION_TEMP_C,
    heat_pump_cop: float = 4.5,
    n_samples: int = 2000,
    seed: int = 42,
) -> np.ndarray:
    """Sample LCoE under the lognormal transmissivity uncertainty (correlated field)."""
    rng = np.random.default_rng(seed)
    mu = np.log(_TRANS_P50)
    sigma = (np.log(_TRANS_P10) - np.log(_TRANS_P90)) / (2.0 * _Z80)
    demand = district_demand()

    lcoes = np.empty(n_samples, dtype=float)
    for i in range(n_samples):
        transmissivity = float(rng.lognormal(mu, sigma))
        geo = n_doublets * doublet_capacity_mw(injection_temp_c, transmissivity_dm=transmissivity)
        design = SystemDesign(geo_capacity_mw=geo, heat_pump_cop=heat_pump_cop)
        perf = simulate(design, demand)
        lcoes[i] = evaluate_costs(n_doublets, design, perf).lcoe_eur_per_gj
    return lcoes


def lcoe_monte_carlo(
    n_doublets: int,
    *,
    injection_temp_c: float = DESIGN_INJECTION_TEMP_C,
    heat_pump_cop: float = 4.5,
    n_samples: int = 2000,
    seed: int = 42,
) -> dict[str, float]:
    """Monte-Carlo LCoE band (P10/P50/P90 and mean) from the transmissivity uncertainty."""
    lcoes = monte_carlo_lcoe_samples(
        n_doublets,
        injection_temp_c=injection_temp_c,
        heat_pump_cop=heat_pump_cop,
        n_samples=n_samples,
        seed=seed,
    )
    return {
        "p10": float(np.percentile(lcoes, 10)),
        "p50": float(np.percentile(lcoes, 50)),
        "p90": float(np.percentile(lcoes, 90)),
        "mean": float(np.mean(lcoes)),
    }
