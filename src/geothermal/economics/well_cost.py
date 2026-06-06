"""Well CAPEX as a function of along-hole depth, ported from the provided LCOE.xlsx.

LCOE.xlsx cell D12 computes the cost of one well as:

    well_cost (M€) = scaling * (0.2 * d^2 + 700 * d + 250000) * 1e-6

where ``d`` is the along-hole depth of a single well in metres and ``scaling`` is the
well-cost scaling factor (1.5). We use the spreadsheet's OWN formula (ThermoGIS publishes
a different one) so our costs stay consistent with the provided model, and we evaluate it
at the Utrecht reservoir depth rather than the spreadsheet's 1800 m worked example (which
is why its base case reads 3.237 M€).
"""

from __future__ import annotations

# LCOE.xlsx D12: scaling x quadratic polynomial in along-hole depth.
WELL_COST_SCALING = 1.5
WELL_COST_QUAD = 0.2
WELL_COST_LIN = 700.0
WELL_COST_CONST = 250000.0


def well_capex_meur(along_hole_depth_m: float) -> float:
    """Cost of one well (M€) at the given along-hole depth, per the LCOE.xlsx formula."""
    d = along_hole_depth_m
    eur = WELL_COST_SCALING * (WELL_COST_QUAD * d * d + WELL_COST_LIN * d + WELL_COST_CONST)
    return eur / 1.0e6
