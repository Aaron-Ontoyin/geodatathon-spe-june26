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
    well_cost_meur: float = Field(
        default=4.331,
        ge=0,
        description=(
            "Cost per well (M€). The LCOE.xlsx well-cost formula (D12) evaluated at the "
            "Utrecht Rotliegend depth (~2281 m), not the spreadsheet's 1800 m worked example "
            "(which gives 3.237). See geothermal.economics.well_cost."
        ),
    )
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
    transmission_meur_per_km: float = Field(
        default=0.8,
        ge=0,
        description=(
            "District-heat transmission main cost (M€ per km) from a doublet site to the "
            "demand district. Assessment-level, capacity-agnostic."
        ),
    )
    demand_connection_km: float = Field(
        default=0.5,
        ge=0,
        description=(
            "Representative distance (km) from the recommended near-demand doublet to the "
            "district network; sets its transmission cost in the canonical economics (the "
            "sited location is ~0.5 km from the demand district)."
        ),
    )

    # --- OPEX / prices ---
    electricity_price_eur_per_mwhe: float = Field(
        default=150.0, ge=0, description="Electricity price (€/MWhe)."
    )
    gas_price_eur_per_mwhth: float = Field(
        default=35.0, ge=0, description="Gas fuel price (€/MWhth)."
    )
    variable_om_eur_per_mwhth: float = Field(
        default=0.0,
        ge=0,
        description=(
            "Other variable O&M (€/MWhth). Circulation-pump electricity (the provided "
            "LCOE.xlsx variable O&M, = electricity_price / circulation_pump_cop) is modelled "
            "explicitly in the electricity term, so it must not be duplicated here."
        ),
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

    # --- Area of interest and siting ---
    aoi_center_rd: tuple[float, float] = Field(
        default=(141171.0, 454890.0),
        description=(
            "Demand-district centre (RD-New metres); the 20x20 km siting box centres here."
        ),
    )
    aoi_size_km: float = Field(
        default=20.0, gt=0, description="Side length of the square siting box (km)."
    )
    viability_floor_mw: float = Field(
        default=2.0,
        ge=0,
        description="Minimum ThermoGIS doublet power (MW) for a cell to be a candidate site.",
    )
    shortlist_size: int = Field(
        default=12,
        ge=4,
        description="Strongest candidate cells kept for the exhaustive program search.",
    )
    max_program_doublets: int = Field(
        default=4, ge=1, description="Backstop cap on doublets in a program."
    )
    well_curvature_factor: float = Field(
        default=1.1, ge=1, description="Along-hole/TVD ratio for deviated wells."
    )
    base_sigma_log_trans: float = Field(
        default=1.5,
        ge=0,
        description="Base log-transmissivity spread, from the 4 wells' P10/P90 bands.",
    )
    sigma_interp_per_km: float = Field(
        default=0.03,
        ge=0,
        description="Extra log-transmissivity uncertainty per km from the nearest logged well.",
    )


DEFAULT_ASSUMPTIONS = Assumptions()
