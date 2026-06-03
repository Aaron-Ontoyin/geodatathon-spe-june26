"""Fill missing porosity and derive permeability for the reservoir table (Phase 1).

EVD-01 and JUT-01 have no measured porosity, so we impute it from the bulk-density
log via the **density-porosity** relation, linearly calibrated against the wells
that *do* have porosity (BLT-01, PKP-01). A physics-anchored model calibrated on two
wells generalises across wells far better than a free-form ML fit on the same two.

Permeability (absent per-sample) is derived from porosity with a log-linear
poro-perm trend fitted to the ThermoGIS P50 values for the four wells.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
import pandas as pd

from geothermal import config
from geothermal.io import load_thermogis

FloatArray = npt.NDArray[np.float64]

MATRIX_DENSITY_SANDSTONE = 2.65  # g/cc, quartz
FLUID_DENSITY_BRINE = 1.05  # g/cc, formation brine
_POROSITY_RANGE_PCT = (0.0, 40.0)
_MIN_PERM_MD = 0.1  # floor for fitting log10(perm)


def density_porosity(
    rhob: npt.ArrayLike,
    *,
    matrix_density: float = MATRIX_DENSITY_SANDSTONE,
    fluid_density: float = FLUID_DENSITY_BRINE,
) -> FloatArray:
    """Density porosity (fraction): ``(ρ_matrix − ρ_bulk) / (ρ_matrix − ρ_fluid)``."""
    rhob_arr = np.asarray(rhob, dtype=float)
    return (matrix_density - rhob_arr) / (matrix_density - fluid_density)


def impute_porosity(table: pd.DataFrame) -> pd.DataFrame:
    """Add ``porosity_final`` (%) and ``porosity_source`` to the reservoir table."""
    out = table.copy()
    observed = np.asarray(out["porosity_obs"], dtype=float)
    phi_density_pct = density_porosity(np.asarray(out["log_rhob"], dtype=float)) * 100.0

    calibratable = np.isfinite(observed) & np.isfinite(phi_density_pct)
    slope, intercept = np.polyfit(phi_density_pct[calibratable], observed[calibratable], 1)
    predicted = np.clip(slope * phi_density_pct + intercept, *_POROSITY_RANGE_PCT)

    final = np.where(np.isfinite(observed), observed, predicted)
    final = _fill_residual_gaps(final, predicted, np.asarray(out["well_id"], dtype=object))

    out["porosity_final"] = final
    out["porosity_source"] = np.where(np.isfinite(observed), "observed", "imputed")
    return out


def add_permeability(table: pd.DataFrame) -> pd.DataFrame:
    """Add ``permeability_md`` from porosity via a log-linear poro-perm trend."""
    out = table.copy()
    intercept, slope = _fit_poro_perm_log10()
    porosity = np.asarray(out["porosity_final"], dtype=float)
    out["permeability_md"] = np.power(10.0, intercept + slope * porosity)
    return out


def porosity_cross_well_skill() -> dict[str, dict[str, float]]:
    """Leave-one-well-out skill for the porosity model (for reporting/validation).

    Calibrates on one porosity-bearing well and predicts the other, reporting R² and
    RMSE — the honest proxy for how well EVD-01/JUT-01 are imputed.
    """
    from geothermal.petrophysics.reservoir import build_reservoir_table

    table = build_reservoir_table()
    have_poro = [w for w, g in table.groupby("well_id") if bool(g["porosity_obs"].notna().any())]
    out: dict[str, dict[str, float]] = {}
    for held in have_poro:
        train = table[(table["well_id"] != held) & table["porosity_obs"].notna()]
        test = table[table["well_id"] == held]
        phi_train = density_porosity(np.asarray(train["log_rhob"], dtype=float)) * 100.0
        slope, intercept = np.polyfit(phi_train, np.asarray(train["porosity_obs"], dtype=float), 1)
        phi_test = density_porosity(np.asarray(test["log_rhob"], dtype=float)) * 100.0
        pred = slope * phi_test + intercept
        truth = np.asarray(test["porosity_obs"], dtype=float)
        out[str(held)] = {"r2": _r2(truth, pred), "rmse": _rmse(truth, pred)}
    return out


def porosity_log_quality() -> dict[str, dict[str, float]]:
    """Per-well agreement of density porosity with measured porosity (where it exists).

    Exposes that the relation is excellent in clean sandstone (BLT-01) and weak in the
    deep, shaly, tight well (PKP-01) — honest context for the imputation's confidence.
    """
    from geothermal.petrophysics.reservoir import build_reservoir_table

    table = build_reservoir_table()
    cored = table[table["porosity_obs"].notna() & table["log_rhob"].notna()]
    out: dict[str, dict[str, float]] = {}
    for well, g in cored.groupby("well_id"):
        obs = np.asarray(g["porosity_obs"], dtype=float)
        phi = density_porosity(np.asarray(g["log_rhob"], dtype=float)) * 100.0
        out[str(well)] = {
            "corr": float(np.corrcoef(obs, phi)[0, 1]),
            "r2_raw": _r2(obs, phi),
            "n": float(len(g)),
        }
    return out


def imputed_vs_thermogis(table: pd.DataFrame) -> pd.DataFrame:
    """Validate per-well mean porosity against the independent ThermoGIS estimate.

    ThermoGIS is a regional model built without our well logs, so for EVD-01/JUT-01
    it is a genuine out-of-sample check on the imputation.
    """
    thermogis = load_thermogis()
    records = [
        {
            "well": str(well),
            "source": str(g["porosity_source"].iloc[0]),
            "porosity_pipeline": float(np.asarray(g["porosity_final"], dtype=float).mean()),
            "porosity_thermogis": float(thermogis[str(well)].value("Porosity")),
        }
        for well, g in table.groupby("well_id")
    ]
    out = pd.DataFrame(records)
    out["difference"] = out["porosity_pipeline"] - out["porosity_thermogis"]
    return out


def _fit_poro_perm_log10() -> tuple[float, float]:
    """Fit ``log10(perm_mD) = intercept + slope · porosity_pct`` on ThermoGIS P50s."""
    thermogis = load_thermogis()
    porosity = np.array([thermogis[w].value("Porosity") for w in config.WELL_IDS])
    perm = np.clip(
        np.array([thermogis[w].value("Permeability") for w in config.WELL_IDS]), _MIN_PERM_MD, None
    )
    slope, intercept = np.polyfit(porosity, np.log10(perm), 1)
    return float(intercept), float(slope)


def _fill_residual_gaps(
    final: FloatArray, predicted: FloatArray, well: npt.NDArray[np.object_]
) -> FloatArray:
    """Replace any remaining NaN (e.g. a density-log gap) with the well's mean prediction."""
    if np.isfinite(final).all():
        return final
    filled = final.copy()
    for well_id in config.WELL_IDS:
        mask = well == well_id
        gap = mask & ~np.isfinite(filled)
        if not gap.any():
            continue
        well_pred = predicted[mask]
        fill_value = (
            np.nanmean(well_pred) if np.isfinite(well_pred).any() else np.nanmean(predicted)
        )
        filled[gap] = fill_value
    return filled


def _r2(truth: FloatArray, pred: FloatArray) -> float:
    ss_res = float(np.sum((truth - pred) ** 2))
    ss_tot = float(np.sum((truth - truth.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0


def _rmse(truth: FloatArray, pred: FloatArray) -> float:
    return float(np.sqrt(np.mean((truth - pred) ** 2)))
