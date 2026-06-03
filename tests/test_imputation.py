"""Tests for porosity imputation and the porosity→permeability transform (Phase 1).

The honest test of an imputation method is cross-well generalisation: train where
porosity is observed (BLT, PKP) and check it predicts a held-out well. We also pin
the density-porosity physics and the monotonic poro-perm trend.
"""

from __future__ import annotations

import numpy as np

from geothermal.petrophysics.imputation import (
    add_permeability,
    density_porosity,
    impute_porosity,
    imputed_vs_thermogis,
)
from geothermal.petrophysics.reservoir import build_reservoir_table


def test_density_porosity_endpoints() -> None:
    # φ = (ρ_ma − ρ_b) / (ρ_ma − ρ_fl): zero at matrix density, 0.5 at the midpoint.
    assert float(density_porosity(2.65, matrix_density=2.65, fluid_density=1.0)) == 0.0
    assert float(density_porosity(1.825, matrix_density=2.65, fluid_density=1.0)) == 0.5


def test_density_porosity_is_vectorised() -> None:
    out = density_porosity(np.array([2.65, 1.825]), matrix_density=2.65, fluid_density=1.0)
    np.testing.assert_allclose(out, [0.0, 0.5])


def test_density_porosity_tracks_observed_porosity() -> None:
    # Where porosity is measured (BLT, PKP), density-derived porosity must correlate
    # strongly — the physical basis for imputing the wells that lack it.
    table = build_reservoir_table()
    g = table[table["porosity_obs"].notna() & table["log_rhob"].notna()]
    phi_d = density_porosity(np.asarray(g["log_rhob"], dtype=float)) * 100.0
    r = float(np.corrcoef(np.asarray(g["porosity_obs"], dtype=float), phi_d)[0, 1])
    assert r > 0.6, f"density porosity should track observed (got r={r:.3f})"


def test_impute_fills_every_row_within_physical_range() -> None:
    table = impute_porosity(build_reservoir_table())
    poro = np.asarray(table["porosity_final"], dtype=float)
    assert np.isfinite(poro).all(), "no porosity may remain missing"
    assert (poro >= 0).all() and (poro <= 40).all(), "porosity must be physical (0–40%)"
    # Observed values are preserved exactly where present.
    obs = table[table["porosity_obs"].notna()]
    np.testing.assert_allclose(
        np.asarray(obs["porosity_final"], dtype=float),
        np.asarray(obs["porosity_obs"], dtype=float),
    )


def test_imputed_wells_get_a_source_label() -> None:
    table = impute_porosity(build_reservoir_table())
    sources = {w: set(g["porosity_source"]) for w, g in table.groupby("well_id")}
    assert sources["BLT-01"] == {"observed"}
    assert sources["EVD-01"] == {"imputed"}
    assert sources["JUT-01"] == {"imputed"}


def test_imputed_porosity_agrees_with_independent_thermogis() -> None:
    # Observed wells must match the regional estimate closely; imputed wells (EVD/JUT)
    # should land in the right ballpark — an out-of-sample check that beats a 2-well LOO.
    table = add_permeability(impute_porosity(build_reservoir_table()))
    check = imputed_vs_thermogis(table)
    observed = check[check["source"] == "observed"]
    imputed = check[check["source"] == "imputed"]
    assert bool((np.abs(np.asarray(observed["difference"], dtype=float)) < 2.0).all())
    assert bool((np.abs(np.asarray(imputed["difference"], dtype=float)) < 4.0).all())


def test_permeability_is_positive_and_increases_with_porosity() -> None:
    table = add_permeability(impute_porosity(build_reservoir_table()))
    perm = np.asarray(table["permeability_md"], dtype=float)
    poro = np.asarray(table["porosity_final"], dtype=float)
    assert (perm > 0).all(), "permeability must be positive"
    # Poro-perm transform is monotonic: rank correlation ≈ 1.
    order = np.argsort(poro)
    assert np.all(np.diff(perm[order]) >= -1e-9)
