"""Geothermal doublet power model, calibrated to ThermoGIS.

Thermal power of a producer/injector doublet is ``P = Q · ρcp · ΔT`` where the
volumetric flow ``Q`` a doublet can sustain scales with reservoir transmissivity
(``k·h``). Calibrating against the four ThermoGIS wells gives:

* flow ≈ ``11.4 m³/h`` per Dm of transmissivity, above a ``~1.0 Dm`` viability
  threshold (below which a doublet cannot sustain economic flow) and capped at a
  realistic pump ceiling (``~480 m³/h ≈ 133 L/s``) in the high-transmissivity tail, and
* an effective injection temperature of ``~39 °C`` (ThermoGIS convention).

With those constants the model reproduces ThermoGIS P50 power at every well, so it
can be trusted on interpolated transmissivity at prospective new locations.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

from geothermal.config import RHO_CP_WATER

FloatArray = npt.NDArray[np.float64]

FLOW_PER_TRANSMISSIVITY_M3H_PER_DM = 11.4
MIN_VIABLE_TRANSMISSIVITY_DM = 1.0
MAX_FLOW_M3_H = 480.0  # realistic geothermal pump ceiling (~133 L/s)
REFERENCE_INJECTION_TEMP_C = 39.0


def geothermal_power_mw(
    flow_m3_h: npt.ArrayLike, delta_t_c: npt.ArrayLike, *, rho_cp: float = RHO_CP_WATER
) -> FloatArray:
    """Thermal power (MW) of a doublet: ``Q·ρcp·ΔT`` with Q in m³/h, ΔT in K."""
    flow = np.asarray(flow_m3_h, dtype=float) / 3600.0  # m³/h → m³/s
    return flow * rho_cp * np.asarray(delta_t_c, dtype=float) / 1.0e6


def doublet_flow_m3_h(
    transmissivity_dm: npt.ArrayLike,
    *,
    coeff: float = FLOW_PER_TRANSMISSIVITY_M3H_PER_DM,
    min_viable_dm: float = MIN_VIABLE_TRANSMISSIVITY_DM,
    max_flow_m3_h: float = MAX_FLOW_M3_H,
) -> FloatArray:
    """Sustainable doublet flow (m³/h): linear in transmissivity, zero below the
    viability threshold and capped at the pump ceiling above it."""
    transmissivity = np.asarray(transmissivity_dm, dtype=float)
    flow = np.minimum(coeff * transmissivity, max_flow_m3_h)
    return np.where(transmissivity >= min_viable_dm, flow, 0.0)


def well_power_mw(
    transmissivity_dm: npt.ArrayLike,
    temperature_c: npt.ArrayLike,
    *,
    injection_temp_c: float = REFERENCE_INJECTION_TEMP_C,
    coeff: float = FLOW_PER_TRANSMISSIVITY_M3H_PER_DM,
    min_viable_dm: float = MIN_VIABLE_TRANSMISSIVITY_DM,
) -> FloatArray:
    """Doublet thermal power (MW) from reservoir transmissivity and temperature."""
    flow = doublet_flow_m3_h(transmissivity_dm, coeff=coeff, min_viable_dm=min_viable_dm)
    delta_t = np.maximum(np.asarray(temperature_c, dtype=float) - injection_temp_c, 0.0)
    return geothermal_power_mw(flow, delta_t)
