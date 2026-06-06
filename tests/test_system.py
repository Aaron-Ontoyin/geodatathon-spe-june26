"""Tests for the integrated heating + cooling system model (Phase 3)."""

from __future__ import annotations

import pytest

from geothermal.design.demand import annual_energy_gj, district_demand
from geothermal.design.system import SystemDesign, heating_capacity_mw, simulate


def test_heat_pump_boosts_heating_capacity_above_raw_geothermal() -> None:
    design = SystemDesign(geo_capacity_mw=8.0, heat_pump_cop=4.5)
    # Delivered heat = geothermal · COP/(COP−1): the HP upgrades the brine to supply temp.
    assert heating_capacity_mw(design) == pytest.approx(8.0 * 4.5 / 3.5)


def test_all_heating_and_cooling_demand_is_met() -> None:
    demand = district_demand()
    perf = simulate(SystemDesign(), demand)
    heat_gj, cold_gj = annual_energy_gj(demand)
    assert perf.heat_delivered_gj == pytest.approx(heat_gj, rel=0.02)
    assert perf.cool_delivered_gj == pytest.approx(cold_gj, rel=0.02)


def test_cooling_integration_raises_geothermal_capacity_factor() -> None:
    # The whole economic thesis: summer cooling uses idle geothermal capacity.
    perf = simulate(SystemDesign(), district_demand())
    assert perf.geo_capacity_factor > perf.geo_capacity_factor_heating_only
    assert 0.0 < perf.geo_capacity_factor <= 1.0


def test_electricity_and_backup_are_physical() -> None:
    perf = simulate(SystemDesign(), district_demand())
    assert perf.heat_pump_mwh_e > 0.0
    assert perf.compression_mwh_e >= 0.0
    assert perf.backup_heat_gj >= 0.0


def test_heating_energy_balance_closes() -> None:
    perf = simulate(SystemDesign(), district_demand())
    parts = perf.geo_hp_heat_gj + perf.ates_discharge_gj + perf.backup_heat_gj
    assert perf.heat_delivered_gj == pytest.approx(parts, rel=0.02)


def test_undersized_geothermal_activates_storage_and_backup() -> None:
    # One doublet (5 MW) cannot meet the 10 MW heating peak alone → ATES and/or backup.
    perf = simulate(SystemDesign(geo_capacity_mw=5.0), district_demand())
    assert perf.ates_discharge_gj + perf.backup_heat_gj > 0.0


def test_ates_discharge_respects_storage_capacity_and_round_trip() -> None:
    # Stored energy is bounded by the store capacity, so discharge <= capacity * round_trip.
    design = SystemDesign(geo_capacity_mw=6.14, ates_capacity_gj=1000.0, ates_round_trip=0.75)
    perf = simulate(design, district_demand())
    assert perf.ates_discharge_gj <= 1000.0 * 0.75 + 1e-6
