"""Tests for the district heating/cooling demand profiles (Phase 3)."""

from __future__ import annotations

import numpy as np
import pytest

from geothermal.design.demand import annual_energy_gj, district_demand, full_load_hours


def test_peaks_match_the_targets() -> None:
    profile = district_demand()
    assert float(np.max(profile.heating_mw)) == pytest.approx(10.0)
    assert float(np.max(profile.cooling_mw)) == pytest.approx(5.0)


def test_heating_peaks_in_winter_cooling_in_summer() -> None:
    profile = district_demand()
    assert int(np.argmax(profile.heating_mw)) in (0, 1, 11)  # Jan/Feb/Dec
    assert int(np.argmax(profile.cooling_mw)) in (5, 6, 7)  # Jun/Jul/Aug


def test_seasons_are_complementary() -> None:
    # Heating dominates when cooling is near zero and vice versa — this is what makes
    # seasonal storage and summer cooling worthwhile.
    profile = district_demand()
    assert float(profile.cooling_mw[0]) < 1.0  # January: little cooling
    assert float(profile.heating_mw[6]) < 2.0  # July: little heating


def test_annual_energy_and_full_load_hours_are_realistic() -> None:
    profile = district_demand()
    heat_gj, cold_gj = annual_energy_gj(profile)
    heat_flh, cool_flh = full_load_hours(profile)
    assert 3500 < heat_flh < 5200, f"district-heating FLH out of range ({heat_flh:.0f})"
    assert 1500 < cool_flh < 3000, f"cooling FLH out of range ({cool_flh:.0f})"
    # Heat energy = peak (MW) · FLH (h) · 3.6 GJ/MWh.
    assert heat_gj == pytest.approx(10.0 * heat_flh * 3.6, rel=1e-6)
    assert cold_gj > 0
