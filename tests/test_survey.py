"""Tests for minimum-curvature directional-survey math (Phase 1 depth foundation).

Analytical cases pin the algorithm; the integration cases prove it reproduces the
TVD column the data provider already computed, validating our AH→TVD conversion.
"""

from __future__ import annotations

import numpy as np
import pytest

from geothermal.io import load_well_paths
from geothermal.petrophysics.survey import (
    DeviationSurvey,
    minimum_curvature,
    survey_tvd_residual_m,
)


def test_vertical_well_tvd_equals_md() -> None:
    md = np.array([0.0, 100.0, 200.0, 300.0])
    zeros = np.zeros(4)
    path = minimum_curvature(md, zeros, zeros)
    np.testing.assert_allclose(path.tvd, md)
    np.testing.assert_allclose(path.north, 0.0, atol=1e-9)
    np.testing.assert_allclose(path.east, 0.0, atol=1e-9)


def test_constant_inclination_tangent_section() -> None:
    # 30° hold due north over 100 m MD: TVD = MD·cos30, North = MD·sin30, East = 0.
    md = np.array([0.0, 100.0])
    inc = np.array([30.0, 30.0])
    azi = np.array([0.0, 0.0])
    path = minimum_curvature(md, inc, azi)
    assert path.tvd[1] == pytest.approx(100 * np.cos(np.radians(30)), abs=1e-6)
    assert path.north[1] == pytest.approx(100 * np.sin(np.radians(30)), abs=1e-6)
    assert path.east[1] == pytest.approx(0.0, abs=1e-9)


def test_build_section_uses_minimum_curvature_ratio_factor() -> None:
    # 0→90° build over 100 m MD, azimuth 0. Dogleg β=π/2 ⇒ RF=(2/β)tan(β/2)=4/π.
    md = np.array([0.0, 100.0])
    inc = np.array([0.0, 90.0])
    azi = np.array([0.0, 0.0])
    path = minimum_curvature(md, inc, azi)
    rf = 4.0 / np.pi
    assert path.tvd[1] == pytest.approx(50 * rf, abs=1e-6)
    assert path.north[1] == pytest.approx(50 * rf, abs=1e-6)
    assert path.east[1] == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("wid", ["BLT-01", "EVD-01", "JUT-01", "PKP-01"])
def test_reproduces_provided_tvd(wid: str) -> None:
    df = load_well_paths()[wid]
    path = minimum_curvature(
        df["md_m"].to_numpy(),
        df["inclination_deg"].to_numpy(),
        df["azimuth_deg"].to_numpy(),
    )
    provided = df["tvd_m"].to_numpy()
    assert np.nanmax(np.abs(path.tvd - provided)) < 1.0


def test_survey_tvd_residual_is_subdecimetre() -> None:
    # The depth conversion reproduces the provider's TVD to within a few centimetres
    # across all wells, so the reported accuracy is derived from data, not asserted.
    assert survey_tvd_residual_m() < 0.1


def test_tvd_never_exceeds_md_and_is_monotone() -> None:
    df = load_well_paths()["JUT-01"]
    survey = DeviationSurvey.from_frame(df)
    md = df["md_m"].to_numpy()
    tvd = survey.tvd_at(md)
    assert np.all(tvd <= md + 1e-6)
    assert np.all(np.diff(tvd) >= -1e-6)


def test_tvd_at_is_vertical_above_first_station() -> None:
    df = load_well_paths()["JUT-01"]  # first survey station at MD = 400 m
    survey = DeviationSurvey.from_frame(df)
    assert survey.tvd_at(np.array([100.0]))[0] == pytest.approx(100.0, abs=1e-6)


def test_tvd_at_matches_stations() -> None:
    df = load_well_paths()["BLT-01"]
    survey = DeviationSurvey.from_frame(df)
    tvd = survey.tvd_at(df["md_m"].to_numpy())
    assert np.nanmax(np.abs(tvd - df["tvd_m"].to_numpy())) < 1.0


def test_blt_reservoir_top_converts_toward_thermogis() -> None:
    # BLT-01 Rotliegend top is AH 1924 m; ThermoGIS's regional TVD is ≈ 1837 m.
    # Converting AH→TVD must (a) shorten the depth and (b) move it markedly closer
    # to the regional estimate. A residual gap (~25 m) is the real well-penetration-
    # vs-regional-model + datum (KB ≈ 8.6 m above NAP) difference, not a bug.
    ah_top, thermogis_tvd = 1924.0, 1837.0
    survey = DeviationSurvey.from_frame(load_well_paths()["BLT-01"])
    tvd_top = float(survey.tvd_at(np.array([ah_top]))[0])
    assert tvd_top < ah_top
    assert abs(tvd_top - thermogis_tvd) < abs(ah_top - thermogis_tvd)
    assert abs(tvd_top - thermogis_tvd) < 40.0
