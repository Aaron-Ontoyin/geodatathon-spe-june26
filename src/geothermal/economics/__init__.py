"""Phase 4 — techno-economics (Challenge 2B).

A Python port of the provided TNO/ECN LCOE model (calibrated to reproduce its
base case), extended for the hybrid heating + cooling system, plus a least-LCoE
design optimisation and a Monte-Carlo LCoE band.
"""

from geothermal.economics.costs import SystemCosts, evaluate_costs
from geothermal.economics.lcoe import (
    DISCOUNT_RATE,
    ECONOMIC_LIFETIME_YEARS,
    capital_recovery_factor,
    levelized_cost_eur_per_gj,
    levelized_cost_eur_per_mwh,
)
from geothermal.economics.optimization import (
    DesignCandidate,
    doublet_capacity_mw,
    evaluate_candidate,
    lcoe_monte_carlo,
    monte_carlo_lcoe_samples,
    optimize,
)

__all__ = [
    "DISCOUNT_RATE",
    "ECONOMIC_LIFETIME_YEARS",
    "DesignCandidate",
    "SystemCosts",
    "capital_recovery_factor",
    "doublet_capacity_mw",
    "evaluate_candidate",
    "evaluate_costs",
    "lcoe_monte_carlo",
    "levelized_cost_eur_per_gj",
    "levelized_cost_eur_per_mwh",
    "monte_carlo_lcoe_samples",
    "optimize",
]
