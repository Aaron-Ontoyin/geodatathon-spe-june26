"""District heating and cooling demand profiles for the Utrecht neighbourhood.

Monthly profiles (peak ``10 MWth`` heating, ``5 MWth`` cooling) shaped to the Dutch
climate: heating concentrated in winter, cooling in summer. The complementary
seasons are precisely what makes seasonal storage and summer cooling valuable.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from geothermal import config

FloatArray = npt.NDArray[np.float64]

HOURS_PER_MONTH = 8760.0 / 12.0
GJ_PER_MWH = 3.6

# Monthly fraction of peak demand, January … December (degree-day shaped, NL).
_HEATING_SHAPE = np.array([1.00, 0.95, 0.75, 0.50, 0.25, 0.10, 0.05, 0.05, 0.20, 0.50, 0.80, 0.95])
_COOLING_SHAPE = np.array([0.00, 0.00, 0.00, 0.10, 0.30, 0.60, 1.00, 0.90, 0.40, 0.10, 0.00, 0.00])


@dataclass(frozen=True, slots=True)
class DemandProfile:
    """Monthly heating and cooling demand (MW) for a calendar year."""

    month: FloatArray  # 1 … 12
    heating_mw: FloatArray
    cooling_mw: FloatArray


def district_demand(
    *,
    heating_peak_mw: float = config.HEATING_DEMAND_MWTH,
    cooling_peak_mw: float = config.COOLING_DEMAND_MWTH,
) -> DemandProfile:
    """Monthly demand profile scaled to the given peak heating/cooling loads."""
    return DemandProfile(
        month=np.arange(1, 13, dtype=float),
        heating_mw=_HEATING_SHAPE * heating_peak_mw,
        cooling_mw=_COOLING_SHAPE * cooling_peak_mw,
    )


def annual_energy_gj(profile: DemandProfile) -> tuple[float, float]:
    """Annual heating and cooling energy delivered (GJ)."""
    heat = float(np.sum(profile.heating_mw) * HOURS_PER_MONTH * GJ_PER_MWH)
    cold = float(np.sum(profile.cooling_mw) * HOURS_PER_MONTH * GJ_PER_MWH)
    return heat, cold


def full_load_hours(profile: DemandProfile) -> tuple[float, float]:
    """Equivalent full-load hours for heating and cooling."""
    heat = float(np.sum(profile.heating_mw) * HOURS_PER_MONTH / np.max(profile.heating_mw))
    cool = float(np.sum(profile.cooling_mw) * HOURS_PER_MONTH / np.max(profile.cooling_mw))
    return heat, cool
