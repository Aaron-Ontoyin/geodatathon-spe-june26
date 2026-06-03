"""Assemble the clean, TVD-correct, log-joined per-sample reservoir table.

Each well's ``target_lithologies`` rows are the LAS samples within its Rotliegend
interval at a fixed along-hole step. We:

1. reconstruct each row's along-hole depth from the interval labels,
2. infer row orientation (top→base vs base→top) from the gamma-ray signature,
3. fill ``depth_tvd_m`` via the minimum-curvature survey, and
4. join the wireline logs (GR/RHOB/NPHI/DT) as imputation features.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import numpy.typing as npt
import pandas as pd

from geothermal import config
from geothermal.io import load_all_las, load_target_lithologies, load_well_paths
from geothermal.io.las_loader import LasData
from geothermal.petrophysics.survey import DeviationSurvey

FloatArray = npt.NDArray[np.float64]
Orientation = Literal["forward", "reversed"]

_MIN_ABS_CORR = 0.5  # below this, GR can't resolve orientation (e.g. clean sand)
_SONIC_CURVES = ("DT", "DTC")


def infer_orientation(
    gr_csv: FloatArray, gr_log: FloatArray, *, min_abs_corr: float = _MIN_ABS_CORR
) -> tuple[Orientation, float]:
    """Decide whether CSV rows run top→base ('forward') or base→top ('reversed').

    Correlates the CSV gamma-ray against the LAS gamma-ray sampled on the ascending
    (top→base) along-hole grid. Falls back to 'forward' when GR is too flat to tell.
    """
    if gr_csv.std() < 1e-9 or gr_log.std() < 1e-9:
        return "forward", 0.0
    r_forward = float(np.corrcoef(gr_csv, gr_log)[0, 1])
    r_reversed = float(np.corrcoef(gr_csv[::-1], gr_log)[0, 1])
    if abs(r_reversed) > abs(r_forward) and abs(r_reversed) >= min_abs_corr:
        return "reversed", abs(r_reversed)
    if abs(r_forward) >= min_abs_corr:
        return "forward", abs(r_forward)
    return "forward", max(abs(r_forward), abs(r_reversed))


def build_well_reservoir(well_id: str, *, las: LasData, survey: DeviationSurvey) -> pd.DataFrame:
    """Build the clean reservoir table for one well."""
    csv = load_target_lithologies()
    rows = pd.DataFrame(csv[csv["well_id"] == well_id]).reset_index(drop=True)
    n = len(rows)
    top_ah = float(_col(rows, "formation_top_tvd")[0])
    base_ah = float(_col(rows, "formation_base_tvd")[0])
    step = (base_ah - top_ah) / n

    ah_grid = top_ah + (np.arange(n) + 0.5) * step  # ascending, top→base
    gr_csv = _col(rows, "gamma_ray_api")
    orientation, confidence = infer_orientation(gr_csv, _sample(las, ("GR",), ah_grid))
    row_ah = ah_grid if orientation == "forward" else ah_grid[::-1]

    out = rows.rename(
        columns={
            "easting": "x",
            "northing": "y",
            "formation_top_tvd": "formation_top_ah_m",
            "formation_base_tvd": "formation_base_ah_m",
            "formation_thickness_m": "formation_thickness_ah_m",
        }
    )
    out["ah_m"] = row_ah
    out["depth_tvd_m"] = survey.tvd_at(row_ah)
    out["porosity_obs"] = _col(rows, "porosity_pct")
    out["log_gr"] = _sample(las, ("GR",), row_ah)
    out["log_rhob"] = _sample(las, ("RHOB",), row_ah)
    out["log_nphi"] = _sample(las, ("NPHI",), row_ah)
    out["log_dt"] = _sample(las, _SONIC_CURVES, row_ah)
    out["row_orientation"] = orientation
    out["orientation_confidence"] = confidence

    top_tvd, base_tvd = survey.tvd_at(np.array([top_ah, base_ah]))
    out["formation_top_tvd_m"] = top_tvd
    out["formation_base_tvd_m"] = base_tvd
    out["formation_thickness_tvd_m"] = base_tvd - top_tvd
    return out


def build_reservoir_table() -> pd.DataFrame:
    """Assemble the master per-sample reservoir table across all four wells."""
    las_by_well = load_all_las()
    surveys = {wid: DeviationSurvey.from_frame(df) for wid, df in load_well_paths().items()}
    frames = [
        build_well_reservoir(wid, las=las_by_well[wid], survey=surveys[wid])
        for wid in config.WELL_IDS
    ]
    return pd.concat(frames, ignore_index=True)


def _col(frame: pd.DataFrame, name: str) -> FloatArray:
    """Extract one column as a concrete float64 array (sidesteps pandas-stub unions)."""
    return np.asarray(frame[name], dtype=float)


def _sample(las: LasData, curve_names: tuple[str, ...], ah: npt.ArrayLike) -> FloatArray:
    """Interpolate the first available LAS curve onto along-hole depths ``ah``."""
    ah_arr = np.asarray(ah, dtype=float)
    depth = np.asarray(las.logs.index, dtype=float)
    for name in curve_names:
        if name not in las.logs.columns:
            continue
        values = _col(las.logs, name)
        valid = np.isfinite(depth) & np.isfinite(values)
        if int(valid.sum()) >= 2:
            return np.interp(ah_arr, depth[valid], values[valid], left=np.nan, right=np.nan)
    return np.full(ah_arr.shape, np.nan, dtype=float)
