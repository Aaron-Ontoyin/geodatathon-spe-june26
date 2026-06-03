"""Directional-survey geometry: along-hole (measured) depth → true vertical depth.

Uses the **minimum-curvature method**, the industry standard for wellbore survey
calculations. Above the first survey station the well is treated as vertical
(TVD = MD), which matches the provider's own convention (TVD₀ = MD₀).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
import pandas as pd
from scipy.interpolate import PchipInterpolator

FloatArray = npt.NDArray[np.float64]

_VERTICAL_DOGLEG_RAD = 1e-10  # below this the ratio factor is 1 (straight segment)


@dataclass(frozen=True, slots=True)
class SurveyPath:
    """Cumulative 3-D wellbore position at each survey station (metres).

    ``north`` / ``east`` are relative to the first station; ``tvd`` is seeded with
    ``MD₀`` so absolute TVD matches the surface reference.
    """

    tvd: FloatArray
    north: FloatArray
    east: FloatArray


def minimum_curvature(
    md: npt.ArrayLike, inclination_deg: npt.ArrayLike, azimuth_deg: npt.ArrayLike
) -> SurveyPath:
    """Compute TVD / northing / easting at each station via minimum curvature.

    Args:
        md: Measured (along-hole) depth at each station, metres, ascending.
        inclination_deg: Hole inclination from vertical, degrees.
        azimuth_deg: Hole azimuth, degrees.

    Returns:
        A :class:`SurveyPath` with one value per input station.
    """
    md_a = np.asarray(md, dtype=float)
    inc = np.radians(np.asarray(inclination_deg, dtype=float))
    azi = np.radians(np.asarray(azimuth_deg, dtype=float))
    if not (md_a.shape == inc.shape == azi.shape):
        raise ValueError("md, inclination and azimuth must have the same shape")
    if md_a.size < 2:
        raise ValueError("at least two survey stations are required")

    inc1, inc2 = inc[:-1], inc[1:]
    azi1, azi2 = azi[:-1], azi[1:]
    d_md = np.diff(md_a)

    cos_dogleg = np.cos(inc2 - inc1) - np.sin(inc1) * np.sin(inc2) * (1.0 - np.cos(azi2 - azi1))
    dogleg = np.arccos(np.clip(cos_dogleg, -1.0, 1.0))
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(dogleg < _VERTICAL_DOGLEG_RAD, 1.0, (2.0 / dogleg) * np.tan(dogleg / 2.0))

    half = d_md / 2.0 * ratio
    d_tvd = half * (np.cos(inc1) + np.cos(inc2))
    d_north = half * (np.sin(inc1) * np.cos(azi1) + np.sin(inc2) * np.cos(azi2))
    d_east = half * (np.sin(inc1) * np.sin(azi1) + np.sin(inc2) * np.sin(azi2))

    tvd = np.concatenate([md_a[:1], md_a[0] + np.cumsum(d_tvd)])
    north = np.concatenate([[0.0], np.cumsum(d_north)])
    east = np.concatenate([[0.0], np.cumsum(d_east)])
    return SurveyPath(tvd=tvd, north=north, east=east)


@dataclass(frozen=True, slots=True)
class DeviationSurvey:
    """A well's survey with a monotone MD→TVD map for re-depthing logs and tops."""

    md: FloatArray
    tvd: FloatArray
    first_station_md: float
    _interp: PchipInterpolator

    @classmethod
    def from_frame(cls, survey: pd.DataFrame) -> DeviationSurvey:
        """Build from a survey frame with md_m / inclination_deg / azimuth_deg columns."""
        clean = survey.dropna(subset=["md_m", "inclination_deg", "azimuth_deg"]).sort_values("md_m")
        md = clean["md_m"].to_numpy(dtype=float)
        path = minimum_curvature(
            md, clean["inclination_deg"].to_numpy(), clean["azimuth_deg"].to_numpy()
        )
        interp = PchipInterpolator(md, path.tvd, extrapolate=True)
        return cls(md=md, tvd=path.tvd, first_station_md=float(md[0]), _interp=interp)

    def tvd_at(self, md_query: npt.ArrayLike) -> FloatArray:
        """Map measured depth(s) to TVD; vertical (TVD = MD) above the first station."""
        query = np.asarray(md_query, dtype=float)
        interpolated = np.asarray(self._interp(query), dtype=float)
        return np.where(query <= self.first_station_md, query, interpolated)
