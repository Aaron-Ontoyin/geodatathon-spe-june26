"""The single, typed, self-validating bag of tunable assumptions for the pipeline.

A Pydantic model so it validates its own values, carries human-readable descriptions
(reused in the CLI template and the API's OpenAPI docs), and can be used directly as
a FastAPI request body. Every economic, design and siting lever lives here with a
documented default and sensible bounds.

Calibration constants fitted to data (e.g. the flow-vs-transmissivity coefficient
validated against ThermoGIS) deliberately stay in their own modules — they are
measurements, not assumptions to sweep.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Assumptions(BaseModel):
    """All tunable design + economic + siting parameters."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    # --- Demand (MW peaks) ---
    heating_peak_mw: float = Field(
        default=10.0, gt=0, description="Peak district heating demand (MWth)."
    )
    cooling_peak_mw: float = Field(
        default=5.0, gt=0, description="Peak district cooling demand (MWth)."
    )

    # --- Integrated system design ---
    heat_pump_cop: float = Field(
        default=4.5, gt=1, description="Heat-pump coefficient of performance."
    )
    absorption_cop: float = Field(
        default=0.7, gt=0, description="Absorption-chiller COP (cooling/heat)."
    )
    compression_cop: float = Field(
        default=5.0, gt=0, description="Electric compression-chiller COP."
    )
    free_cooling_mw: float = Field(
        default=1.0, ge=0, description="Free-cooling capacity from the cold side (MW)."
    )
    ates_round_trip: float = Field(
        default=0.75, gt=0, le=1, description="HT-ATES seasonal round-trip efficiency."
    )
    injection_temp_c: float = Field(default=30.0, ge=0, description="Reinjection temperature (°C).")

    # --- Resource siting ---
    min_well_spacing_km: float = Field(
        default=1.5, gt=0, description="Min doublet spacing (km) to avoid breakthrough."
    )
    demand_distance_weight_mw_per_km: float = Field(
        default=0.1, ge=0, description="Siting tie-breaker: MW traded per km closer to demand."
    )

    # --- CAPEX unit costs ---
    well_cost_meur: float = Field(default=3.237, ge=0, description="Cost per well (M€).")
    pump_cost_meur: float = Field(default=0.3, ge=0, description="Pump cost per doublet (M€).")
    heat_plant_keur_per_mwth: float = Field(
        default=150.0, ge=0, description="Surface heat plant (k€/MWth)."
    )
    heat_pump_keur_per_mwth: float = Field(default=700.0, ge=0, description="Heat pump (k€/MWth).")
    absorption_keur_per_mwth: float = Field(
        default=400.0, ge=0, description="Absorption chiller (k€/MWth)."
    )
    compression_keur_per_mwth: float = Field(
        default=150.0, ge=0, description="Compression chiller (k€/MWth)."
    )
    backup_keur_per_mwth: float = Field(
        default=60.0, ge=0, description="Gas peak boiler (k€/MWth)."
    )
    ates_meur: float = Field(
        default=2.0, ge=0, description="HT-ATES doublet + heat exchangers (M€)."
    )

    # --- OPEX / prices ---
    electricity_price_eur_per_mwhe: float = Field(
        default=150.0, ge=0, description="Electricity price (€/MWhe)."
    )
    gas_price_eur_per_mwhth: float = Field(
        default=35.0, ge=0, description="Gas fuel price (€/MWhth)."
    )
    variable_om_eur_per_mwhth: float = Field(
        default=5.556, ge=0, description="Variable O&M (€/MWhth)."
    )
    fixed_om_rate: float = Field(
        default=0.01, ge=0, le=1, description="Fixed O&M as a fraction of CAPEX per year."
    )
    circulation_pump_cop: float = Field(
        default=27.0, gt=0, description="Circulation-pump COP (thermal/electric)."
    )
    backup_boiler_efficiency: float = Field(
        default=0.92, gt=0, le=1, description="Backup boiler efficiency."
    )

    # --- Finance ---
    discount_rate: float = Field(
        default=0.093, ge=0, lt=1, description="Effective discount rate (reproduces LCOE.xlsx)."
    )
    economic_lifetime_years: int = Field(default=15, ge=1, description="Economic lifetime (years).")

    # --- Feasibility constraint ---
    max_backup_fraction: float = Field(
        default=0.15,
        ge=0,
        le=1,
        description="Max share of heat from backup for a design to count as geothermal.",
    )


DEFAULT_ASSUMPTIONS = Assumptions()
