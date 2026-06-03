"""Tests for the geothermal doublet power model (Phase 2 resource assessment).

The model is calibrated to ThermoGIS (flow ≈ coeff·transmissivity above a viability
threshold; power = flow·ρcp·ΔT) and must reproduce ThermoGIS P50 at the four wells,
so we can trust it on interpolated transmissivity at *new* locations.
"""

from __future__ import annotations

import pytest

from geothermal.io import load_thermogis
from geothermal.resource.power import doublet_flow_m3_h, geothermal_power_mw, well_power_mw


def test_geothermal_power_matches_definition() -> None:
    # 105 m³/h at ΔT = 38 °C → ≈ 5.1 MWth (ThermoGIS BLT-01 P50 operating point).
    assert float(geothermal_power_mw(105.0, 38.0)) == pytest.approx(5.08, abs=0.1)


def test_geothermal_power_scales_with_flow_and_delta_t() -> None:
    assert float(geothermal_power_mw(200.0, 30.0)) == pytest.approx(
        2 * float(geothermal_power_mw(100.0, 30.0))
    )
    assert float(geothermal_power_mw(100.0, 40.0)) > float(geothermal_power_mw(100.0, 20.0))


def test_doublet_flow_is_linear_above_threshold_and_zero_below() -> None:
    assert float(doublet_flow_m3_h(9.3)) == pytest.approx(11.4 * 9.3, abs=2.0)
    assert float(doublet_flow_m3_h(0.4)) == 0.0  # below viability threshold


@pytest.mark.parametrize(("well", "expected_mw"), [("BLT-01", 5.1), ("JUT-01", 2.3)])
def test_well_power_reproduces_thermogis_p50(well: str, expected_mw: float) -> None:
    tg = load_thermogis()[well]
    power = float(well_power_mw(tg.value("Transmissivity"), tg.value("Temperature")))
    assert power == pytest.approx(expected_mw, abs=0.7)


@pytest.mark.parametrize(
    ("well", "pct", "expected_mw"),
    [
        ("BLT-01", "P90", 0.6),
        ("BLT-01", "P10", 23.7),  # capped pump rate keeps the optimistic tail realistic
        ("JUT-01", "P90", 1.0),
        ("JUT-01", "P10", 4.8),
    ],
)
def test_well_power_reproduces_thermogis_tails(well: str, pct: str, expected_mw: float) -> None:
    tg = load_thermogis()[well]
    power = float(well_power_mw(tg.value("Transmissivity", pct), tg.value("Temperature")))
    assert power == pytest.approx(expected_mw, rel=0.2, abs=0.5)


@pytest.mark.parametrize("well", ["EVD-01", "PKP-01"])
def test_tight_wells_are_non_viable(well: str) -> None:
    tg = load_thermogis()[well]
    assert float(well_power_mw(tg.value("Transmissivity"), tg.value("Temperature"))) == 0.0


def test_power_increases_with_transmissivity_and_temperature() -> None:
    assert float(well_power_mw(20.0, 80.0)) > float(well_power_mw(10.0, 80.0))
    assert float(well_power_mw(10.0, 90.0)) > float(well_power_mw(10.0, 70.0))
