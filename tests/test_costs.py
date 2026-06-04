"""Tests for the hybrid system cost model and its LCoE (Phase 4)."""

from __future__ import annotations

import pytest

from geothermal.design import SystemDesign, district_demand, simulate
from geothermal.economics.costs import evaluate_costs


def test_costs_positive_and_breakdown_reconciles() -> None:
    design = SystemDesign()
    perf = simulate(design, district_demand())
    costs = evaluate_costs(2, design, perf)
    assert costs.capex_meur > 0
    assert costs.annual_opex_meur > 0
    assert sum(costs.capex_breakdown.values()) == pytest.approx(costs.capex_meur, rel=1e-6)
    assert 5.0 < costs.lcoe_eur_per_gj < 60.0  # plausible band for a hybrid HP system


def test_cooling_integration_lowers_combined_lcoe() -> None:
    # Spreading fixed cost over heat + cold beats heat alone — the economic thesis.
    design = SystemDesign()
    perf = simulate(design, district_demand())
    costs = evaluate_costs(2, design, perf)
    assert costs.lcoe_eur_per_gj < costs.lcoe_heat_only_eur_per_gj


def test_more_doublets_increase_capex() -> None:
    demand = district_demand()
    one = evaluate_costs(1, d1 := SystemDesign(geo_capacity_mw=5.0), simulate(d1, demand))
    two = evaluate_costs(2, d2 := SystemDesign(geo_capacity_mw=10.0), simulate(d2, demand))
    assert two.capex_meur > one.capex_meur
