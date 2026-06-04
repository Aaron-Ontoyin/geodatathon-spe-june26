"""The single, typed bag of tunable assumptions for the whole pipeline.

Every economic, design and siting lever the analysis depends on lives here with a
documented default. Functions across the pipeline accept ``assumptions`` so the
optimiser, sensitivity tests, the agentic workflow and the app can all vary them by
passing a different :class:`Assumptions` — nothing is a buried magic number.

Calibration constants that are *fitted to data* (e.g. the flow-vs-transmissivity
coefficient validated against ThermoGIS) deliberately stay in their own modules —
they are measurements, not assumptions to sweep.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Assumptions:
    """All tunable design + economic + siting parameters, with defaults."""

    # --- Demand (MW peaks) ---
    heating_peak_mw: float = 10.0
    cooling_peak_mw: float = 5.0

    # --- Integrated system design ---
    heat_pump_cop: float = 4.5
    absorption_cop: float = 0.7
    compression_cop: float = 5.0
    free_cooling_mw: float = 1.0
    ates_round_trip: float = 0.75
    injection_temp_c: float = 30.0  # heat-pump-assisted district-heating return

    # --- Resource siting ---
    min_well_spacing_km: float = 1.5  # doublet spacing to avoid thermal breakthrough
    demand_distance_weight_mw_per_km: float = 0.1  # tie-breaker toward the demand

    # --- CAPEX unit costs ---
    well_cost_meur: float = 3.237  # per well (LCOE.xlsx)
    pump_cost_meur: float = 0.3  # per doublet (LCOE.xlsx)
    heat_plant_keur_per_mwth: float = 150.0
    heat_pump_keur_per_mwth: float = 700.0
    absorption_keur_per_mwth: float = 400.0
    compression_keur_per_mwth: float = 150.0
    backup_keur_per_mwth: float = 60.0
    ates_meur: float = 2.0

    # --- OPEX / prices ---
    electricity_price_eur_per_mwhe: float = 150.0  # LCOE.xlsx
    gas_price_eur_per_mwhth: float = 35.0
    variable_om_eur_per_mwhth: float = 5.556  # LCOE.xlsx
    fixed_om_rate: float = 0.01  # fraction of CAPEX per year
    circulation_pump_cop: float = 27.0  # LCOE.xlsx
    backup_boiler_efficiency: float = 0.92

    # --- Finance ---
    discount_rate: float = 0.093  # effective; reproduces LCOE.xlsx base case
    economic_lifetime_years: int = 15

    # --- Feasibility constraint ---
    max_backup_fraction: float = 0.15  # geothermal-based, not a gas plant in disguise


DEFAULT_ASSUMPTIONS = Assumptions()
