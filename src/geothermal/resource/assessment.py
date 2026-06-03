"""Per-well probabilistic power and location of the demand district (Phase 2).

* ``well_power_percentiles`` maps the ThermoGIS transmissivity P90/P50/P10 through
  the calibrated doublet model to a P90/P50/P10 power band per well — honest
  uncertainty rather than a single number.
* ``locate_demand_center`` trilaterates Utrecht Science Park (the load) from the
  ``distance_to_usp_km`` recorded for every well, so new wells can be sited near it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from geothermal import config
from geothermal.io import load_target_lithologies, load_thermogis
from geothermal.resource.power import REFERENCE_INJECTION_TEMP_C, well_power_mw

_PERCENTILES = ("P90", "P50", "P10")


def well_power_percentiles(*, injection_temp_c: float = REFERENCE_INJECTION_TEMP_C) -> pd.DataFrame:
    """Per-well P90/P50/P10 doublet power (MW), with the ThermoGIS P50 for comparison."""
    thermogis = load_thermogis()
    records: dict[str, dict[str, float]] = {}
    for wid in config.WELL_IDS:
        well = thermogis[wid]
        temperature = well.value("Temperature")
        record = {
            pct: float(
                well_power_mw(
                    well.value("Transmissivity", pct),
                    temperature,
                    injection_temp_c=injection_temp_c,
                )
            )
            for pct in _PERCENTILES
        }
        record["thermogis_P50"] = well.value("Power", "P50")
        records[wid] = record
    return pd.DataFrame.from_dict(records, orient="index")


def locate_demand_center() -> tuple[float, float]:
    """Least-squares trilateration of the demand district from per-well distances."""
    csv = load_target_lithologies()
    coords: list[tuple[float, float]] = []
    distances: list[float] = []
    for wid in config.WELL_IDS:
        g = csv[csv["well_id"] == wid]
        coords.append((float(np.asarray(g["easting"])[0]), float(np.asarray(g["northing"])[0])))
        distances.append(float(np.asarray(g["distance_to_usp_km"])[0]) * 1000.0)

    points = np.asarray(coords, dtype=float)
    radii = np.asarray(distances, dtype=float)
    x0, y0 = points[0]
    r0 = radii[0]

    # Linearise ‖p − wᵢ‖ = rᵢ by subtracting the first well's equation.
    a_rows = 2.0 * (points[1:] - np.array([x0, y0]))
    b_vals = (points[1:, 0] ** 2 + points[1:, 1] ** 2 - x0**2 - y0**2) - (radii[1:] ** 2 - r0**2)
    solution, *_ = np.linalg.lstsq(a_rows, b_vals, rcond=None)
    return float(solution[0]), float(solution[1])


def distance_km(x1: float, y1: float, x2: float, y2: float) -> float:
    """Planar distance in km between two RD-New points (metres)."""
    return float(np.hypot(x1 - x2, y1 - y2)) / 1000.0
