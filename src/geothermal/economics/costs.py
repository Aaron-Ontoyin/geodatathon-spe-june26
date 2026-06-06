"""Hybrid system cost model → system LCoE.

Capital and operating costs of the integrated heating + cooling system. Every unit
cost and price is read from the :class:`~geothermal.assumptions.Assumptions` config
(defaults from LCOE.xlsx + documented public ranges), so the optimiser, sensitivity
tests and app can vary them. The headline metric is the LCoE over the *combined*
heat + cold delivered.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from geothermal.assumptions import DEFAULT_ASSUMPTIONS, Assumptions
from geothermal.design.system import SystemDesign, SystemPerformance, heating_capacity_mw
from geothermal.economics.lcoe import GJ_PER_MWH, levelized_cost_eur_per_gj


@dataclass(frozen=True, slots=True)
class SystemCosts:
    """CAPEX/OPEX and LCoE of one hybrid system design (costs in M€, LCoE in €/GJ)."""

    capex_meur: float
    annual_opex_meur: float
    lcoe_eur_per_gj: float
    lcoe_heat_only_eur_per_gj: float
    capex_breakdown: dict[str, float] = field(default_factory=dict)


def evaluate_costs(
    n_doublets: int,
    design: SystemDesign,
    performance: SystemPerformance,
    *,
    assumptions: Assumptions = DEFAULT_ASSUMPTIONS,
    wells_capex_meur: float | None = None,
) -> SystemCosts:
    """Compute CAPEX, OPEX and LCoE for a sized hybrid system."""
    a = assumptions
    cap_heat = heating_capacity_mw(design)
    monthly = performance.monthly

    breakdown = {
        "wells_pumps": (
            wells_capex_meur
            if wells_capex_meur is not None
            else n_doublets * (2 * a.well_cost_meur + a.pump_cost_meur)
        ),
        "heat_plant": cap_heat * a.heat_plant_keur_per_mwth / 1000.0,
        "heat_pump": cap_heat * a.heat_pump_keur_per_mwth / 1000.0,
        "absorption_chiller": _peak(monthly, "abs_cool_mw") * a.absorption_keur_per_mwth / 1000.0,
        "compression_chiller": _peak(monthly, "comp_cool_mw")
        * a.compression_keur_per_mwth
        / 1000.0,
        "backup_boiler": _peak(monthly, "backup_mw") * a.backup_keur_per_mwth / 1000.0,
        "ht_ates": a.ates_meur if performance.ates_discharge_gj > 1.0 else 0.0,
    }
    capex_meur = sum(breakdown.values())
    capex_eur = capex_meur * 1.0e6

    thermal_mwh = (performance.heat_delivered_gj + performance.cool_delivered_gj) / GJ_PER_MWH
    # Circulation-pump electricity = geothermal throughput / COP, charged at the electricity
    # price. This IS the provided LCOE.xlsx "variable O&M" (defined there as price / COP), so
    # it is counted here only, never also in variable_om_eur_per_mwhth (which would double it).
    circulation_mwh_e = (performance.geo_heat_gj / GJ_PER_MWH) / a.circulation_pump_cop
    electricity_mwh_e = (
        performance.heat_pump_mwh_e + performance.compression_mwh_e + circulation_mwh_e
    )
    gas_mwh = (performance.backup_heat_gj / GJ_PER_MWH) / a.backup_boiler_efficiency

    annual_opex_eur = (
        a.variable_om_eur_per_mwhth * thermal_mwh
        + a.electricity_price_eur_per_mwhe * electricity_mwh_e
        + a.gas_price_eur_per_mwhth * gas_mwh
        + a.fixed_om_rate * capex_eur
    )

    combined_gj = performance.heat_delivered_gj + performance.cool_delivered_gj
    lcoe = levelized_cost_eur_per_gj(
        capex_eur=capex_eur,
        annual_opex_eur=annual_opex_eur,
        annual_energy_gj=combined_gj,
        discount_rate=a.discount_rate,
        lifetime_years=a.economic_lifetime_years,
    )
    lcoe_heat_only = levelized_cost_eur_per_gj(
        capex_eur=capex_eur,
        annual_opex_eur=annual_opex_eur,
        annual_energy_gj=performance.heat_delivered_gj,
        discount_rate=a.discount_rate,
        lifetime_years=a.economic_lifetime_years,
    )
    return SystemCosts(
        capex_meur=capex_meur,
        annual_opex_meur=annual_opex_eur / 1.0e6,
        lcoe_eur_per_gj=lcoe,
        lcoe_heat_only_eur_per_gj=lcoe_heat_only,
        capex_breakdown=breakdown,
    )


def _peak(monthly: pd.DataFrame, column: str) -> float:
    return float(np.asarray(monthly[column], dtype=float).max())
