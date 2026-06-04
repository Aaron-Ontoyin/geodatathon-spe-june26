"""Tests for the levelized-cost core (Phase 4), validated against LCOE.xlsx."""

from __future__ import annotations

import pytest

from geothermal.economics.lcoe import (
    capital_recovery_factor,
    levelized_cost_eur_per_gj,
    levelized_cost_eur_per_mwh,
)


def test_capital_recovery_factor_matches_textbook() -> None:
    # CRF(10%, 10 yr) = 0.162745 (standard annuity result).
    assert capital_recovery_factor(0.10, 10) == pytest.approx(0.162745, abs=1e-5)


def test_reproduces_provided_base_case_heat_lcoe() -> None:
    # Provided LCOE.xlsx base case: 2 wells, 8.791 M€ capex, 566 k€/yr opex,
    # 290,449 GJ/yr direct heat → 5.77 €/GJ. Our port must reproduce it.
    lcoe = levelized_cost_eur_per_gj(
        capex_eur=8_791_005, annual_opex_eur=566_433, annual_energy_gj=290_449
    )
    assert lcoe == pytest.approx(5.77, abs=0.15)


def test_mwh_and_gj_units_are_consistent() -> None:
    # 1 MWh = 3.6 GJ, so €/MWh = €/GJ × 3.6.
    per_gj = levelized_cost_eur_per_gj(
        capex_eur=8_791_005, annual_opex_eur=566_433, annual_energy_gj=290_449
    )
    per_mwh = levelized_cost_eur_per_mwh(
        capex_eur=8_791_005, annual_opex_eur=566_433, annual_energy_mwh=290_449 / 3.6
    )
    assert per_mwh == pytest.approx(per_gj * 3.6, rel=1e-9)


def test_more_energy_lowers_lcoe() -> None:
    base = levelized_cost_eur_per_gj(
        capex_eur=10e6, annual_opex_eur=500_000, annual_energy_gj=200_000
    )
    more = levelized_cost_eur_per_gj(
        capex_eur=10e6, annual_opex_eur=500_000, annual_energy_gj=300_000
    )
    assert more < base
