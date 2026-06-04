"""Integrated geothermal heating + cooling system — monthly energy balance.

Assessment-level (no thermodynamic cycle modelling, per the brief): components are
represented by capacities, coefficients of performance, and a monthly dispatch.

Dispatch each month:
  heating  ← geothermal upgraded by the heat pump, then HT-ATES discharge, then backup
  cooling  ← absorption chiller driven by *spare* geothermal heat, then free cooling
             from the cold ATES well, then an electric compression chiller
Spare summer geothermal heat that is not used for cooling charges the HT-ATES for
winter. Because summer cooling and storage employ capacity a heating-only system
would leave idle, the geothermal utilisation (and therefore the LCoE) improves.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
import pandas as pd

from geothermal.design.demand import GJ_PER_MWH, HOURS_PER_MONTH, DemandProfile

FloatArray = npt.NDArray[np.float64]
_HOURS_PER_YEAR = 8760.0


@dataclass(frozen=True, slots=True)
class SystemDesign:
    """Design parameters for the integrated system."""

    geo_capacity_mw: float = 10.0  # geothermal thermal capacity (≈ doublet programme P50)
    heat_pump_cop: float = 4.5
    absorption_cop: float = 0.7
    compression_cop: float = 5.0
    free_cooling_mw: float = 1.0
    ates_round_trip: float = 0.75
    ates_capacity_gj: float = 5.0e5


@dataclass(frozen=True, slots=True)
class SystemPerformance:
    """Annual performance of a simulated system (energy in GJ, electricity in MWh_e)."""

    heat_delivered_gj: float
    cool_delivered_gj: float
    geo_hp_heat_gj: float  # heating delivered by geothermal + heat pump
    geo_heat_gj: float  # total geothermal thermal extracted (heating + cooling + storage)
    ates_discharge_gj: float
    backup_heat_gj: float
    heat_pump_mwh_e: float
    compression_mwh_e: float
    absorption_cool_gj: float
    geo_capacity_factor: float
    geo_capacity_factor_heating_only: float
    heating_capacity_mw: float
    monthly: pd.DataFrame


def heating_capacity_mw(design: SystemDesign) -> float:
    """Heating capacity (MW): geothermal heat upgraded by the heat pump, ``geo·COP/(COP−1)``."""
    cop = design.heat_pump_cop
    return design.geo_capacity_mw * cop / (cop - 1.0)


def simulate(design: SystemDesign, demand: DemandProfile) -> SystemPerformance:
    """Run the monthly dispatch and return the annual energy balance."""
    hours = HOURS_PER_MONTH
    geo = design.geo_capacity_mw
    cop = design.heat_pump_cop
    cap_heat = heating_capacity_mw(design)

    heating = demand.heating_mw
    cooling = demand.cooling_mw

    # --- Heating from geothermal + heat pump ---
    heat_geo_hp = np.minimum(heating, cap_heat)  # MW delivered
    geo_for_heat = heat_geo_hp * (cop - 1.0) / cop  # MW geothermal thermal
    hp_elec = heat_geo_hp / cop  # MW electric
    heat_remaining_mwh = (heating - heat_geo_hp) * hours

    # --- Cooling: absorption (spare geo) → free cooling → compression ---
    geo_spare = np.maximum(geo - geo_for_heat, 0.0)
    abs_cool = np.minimum(cooling, geo_spare * design.absorption_cop)  # MW cooling
    geo_for_abs = abs_cool / design.absorption_cop  # MW geothermal thermal
    free_cool = np.minimum(cooling - abs_cool, design.free_cooling_mw)
    comp_cool = np.maximum(cooling - abs_cool - free_cool, 0.0)
    comp_elec = comp_cool / design.compression_cop

    # --- Seasonal HT-ATES: charge summer surplus, discharge to cover the winter deficit ---
    geo_charge_available_mwh = np.maximum(geo_spare - geo_for_abs, 0.0) * hours
    discharge_need_mwh = min(
        float(np.sum(heat_remaining_mwh)), design.ates_capacity_gj / GJ_PER_MWH
    )
    charge_mwh = min(
        discharge_need_mwh / design.ates_round_trip, float(np.sum(geo_charge_available_mwh))
    )
    actual_discharge_mwh = charge_mwh * design.ates_round_trip

    ates_discharge = _allocate(heat_remaining_mwh, actual_discharge_mwh)
    ates_charge = _allocate(geo_charge_available_mwh, charge_mwh)
    backup_mwh = heat_remaining_mwh - ates_discharge

    # --- Geothermal utilisation (guard the dud-well case where geo capacity is 0) ---
    geo_used_mwh = geo_for_heat * hours + geo_for_abs * hours + ates_charge
    geo_capacity_mwh_year = geo * _HOURS_PER_YEAR
    capacity_factor = float(np.sum(geo_used_mwh) / geo_capacity_mwh_year) if geo > 0 else 0.0
    capacity_factor_heating = (
        float(np.sum(geo_for_heat * hours) / geo_capacity_mwh_year) if geo > 0 else 0.0
    )

    monthly = pd.DataFrame(
        {
            "month": demand.month,
            "heating_mw": heating,
            "cooling_mw": cooling,
            "geo_heat_mw": geo_for_heat,
            "hp_elec_mw": hp_elec,
            "abs_cool_mw": abs_cool,
            "free_cool_mw": free_cool,
            "comp_cool_mw": comp_cool,
            "backup_mw": backup_mwh / hours,
            "ates_discharge_mw": ates_discharge / hours,
        }
    )

    return SystemPerformance(
        heat_delivered_gj=float(np.sum(heating) * hours * GJ_PER_MWH),
        cool_delivered_gj=float(np.sum(cooling) * hours * GJ_PER_MWH),
        geo_hp_heat_gj=float(np.sum(heat_geo_hp) * hours * GJ_PER_MWH),
        geo_heat_gj=float(np.sum(geo_used_mwh) * GJ_PER_MWH),
        ates_discharge_gj=float(np.sum(ates_discharge) * GJ_PER_MWH),
        backup_heat_gj=float(np.sum(backup_mwh) * GJ_PER_MWH),
        heat_pump_mwh_e=float(np.sum(hp_elec) * hours),
        compression_mwh_e=float(np.sum(comp_elec) * hours),
        absorption_cool_gj=float(np.sum(abs_cool) * hours * GJ_PER_MWH),
        geo_capacity_factor=capacity_factor,
        geo_capacity_factor_heating_only=capacity_factor_heating,
        heating_capacity_mw=cap_heat,
        monthly=monthly,
    )


def _allocate(weights_mwh: FloatArray, total_mwh: float) -> FloatArray:
    """Distribute ``total_mwh`` across months in proportion to ``weights_mwh`` (capped)."""
    total_weight = float(np.sum(weights_mwh))
    if total_weight <= 0.0 or total_mwh <= 0.0:
        return np.zeros_like(weights_mwh)
    return np.minimum(weights_mwh * (total_mwh / total_weight), weights_mwh)
