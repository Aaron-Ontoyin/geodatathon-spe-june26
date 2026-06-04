"""Hybrid system cost model → system LCoE.

Capital and operating costs of the integrated heating + cooling system, combining
the provided LCOE.xlsx assumptions (well/pump cost, O&M, electricity price,
circulation-pump COP) with documented public unit costs for the surface components
(heat pump, absorption/compression chillers, HT-ATES, backup boiler). The headline
metric is the LCoE over the *combined* heat + cold delivered.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from geothermal.design.system import SystemDesign, SystemPerformance, heating_capacity_mw
from geothermal.economics.lcoe import GJ_PER_MWH, levelized_cost_eur_per_gj

# --- Subsurface (from LCOE.xlsx) ---
WELL_COST_MEUR = 3.237
PUMP_COST_MEUR = 0.3
CIRCULATION_PUMP_COP = 27.0

# --- Surface unit costs (documented public ranges; M€ unless noted) ---
HEAT_PLANT_KEUR_PER_MWTH = 150.0  # LCOE.xlsx direct-heat surface installation
HEAT_PUMP_KEUR_PER_MWTH = 700.0  # large industrial heat pump
ABSORPTION_KEUR_PER_MWTH = 400.0  # absorption chiller
COMPRESSION_KEUR_PER_MWTH = 150.0  # electric compression chiller
BACKUP_KEUR_PER_MWTH = 60.0  # gas peak boiler
ATES_MEUR = 2.0  # HT-ATES doublet + heat exchangers

# --- Operating costs ---
ELECTRICITY_PRICE_EUR_PER_MWHE = 150.0  # LCOE.xlsx
GAS_PRICE_EUR_PER_MWHTH = 35.0  # NL wholesale gas (fuel)
VARIABLE_OM_EUR_PER_MWHTH = 5.556  # LCOE.xlsx
FIXED_OM_RATE = 0.01  # fraction of CAPEX per year, LCOE.xlsx
BACKUP_BOILER_EFFICIENCY = 0.92


@dataclass(frozen=True, slots=True)
class SystemCosts:
    """CAPEX/OPEX and LCoE of one hybrid system design (costs in M€, LCoE in €/GJ)."""

    capex_meur: float
    annual_opex_meur: float
    lcoe_eur_per_gj: float
    lcoe_heat_only_eur_per_gj: float
    capex_breakdown: dict[str, float] = field(default_factory=dict)


def evaluate_costs(
    n_doublets: int, design: SystemDesign, performance: SystemPerformance
) -> SystemCosts:
    """Compute CAPEX, OPEX and LCoE for a sized hybrid system."""
    cap_heat = heating_capacity_mw(design)
    monthly = performance.monthly

    breakdown = {
        "wells_pumps": n_doublets * (2 * WELL_COST_MEUR + PUMP_COST_MEUR),
        "heat_plant": cap_heat * HEAT_PLANT_KEUR_PER_MWTH / 1000.0,
        "heat_pump": cap_heat * HEAT_PUMP_KEUR_PER_MWTH / 1000.0,
        "absorption_chiller": _peak(monthly, "abs_cool_mw") * ABSORPTION_KEUR_PER_MWTH / 1000.0,
        "compression_chiller": _peak(monthly, "comp_cool_mw") * COMPRESSION_KEUR_PER_MWTH / 1000.0,
        "backup_boiler": _peak(monthly, "backup_mw") * BACKUP_KEUR_PER_MWTH / 1000.0,
        "ht_ates": ATES_MEUR if performance.ates_discharge_gj > 1.0 else 0.0,
    }
    capex_meur = sum(breakdown.values())
    capex_eur = capex_meur * 1.0e6

    thermal_mwh = (performance.heat_delivered_gj + performance.cool_delivered_gj) / GJ_PER_MWH
    circulation_mwh_e = (performance.geo_heat_gj / GJ_PER_MWH) / CIRCULATION_PUMP_COP
    electricity_mwh_e = (
        performance.heat_pump_mwh_e + performance.compression_mwh_e + circulation_mwh_e
    )
    gas_mwh = (performance.backup_heat_gj / GJ_PER_MWH) / BACKUP_BOILER_EFFICIENCY

    annual_opex_eur = (
        VARIABLE_OM_EUR_PER_MWHTH * thermal_mwh
        + ELECTRICITY_PRICE_EUR_PER_MWHE * electricity_mwh_e
        + GAS_PRICE_EUR_PER_MWHTH * gas_mwh
        + FIXED_OM_RATE * capex_eur
    )

    combined_gj = performance.heat_delivered_gj + performance.cool_delivered_gj
    lcoe = levelized_cost_eur_per_gj(
        capex_eur=capex_eur, annual_opex_eur=annual_opex_eur, annual_energy_gj=combined_gj
    )
    lcoe_heat_only = levelized_cost_eur_per_gj(
        capex_eur=capex_eur,
        annual_opex_eur=annual_opex_eur,
        annual_energy_gj=performance.heat_delivered_gj,
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
