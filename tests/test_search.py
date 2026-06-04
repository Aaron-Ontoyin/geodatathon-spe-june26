"""Tests for the generalized design optimiser — ranges + constraints + objective (5c)."""

from __future__ import annotations

import pytest

from geothermal.economics.search import DesignConstraints, search_designs


def test_no_ranges_reduces_to_doublet_sweep() -> None:
    result = search_designs()
    assert result.best is not None
    assert result.best.n_doublets == 1
    assert result.best.lcoe_eur_per_gj == pytest.approx(20.9, abs=1.0)
    assert result.n_evaluated == 3  # 3 doublet options, no ranges


def test_searching_a_range_is_a_grid_sorted_by_lcoe() -> None:
    result = search_designs(ranges={"injection_temp_c": (25.0, 40.0)}, samples=4)
    assert result.n_evaluated == 3 * 4  # doublets × grid points
    assert len(result.feasible) >= 1
    lcoes = [c.lcoe_eur_per_gj for c in result.feasible]
    assert lcoes == sorted(lcoes)
    assert result.best is result.feasible[0]


def test_capex_budget_constraint_filters_designs() -> None:
    result = search_designs(constraints=DesignConstraints(max_capex_meur=20.0))
    assert result.best is not None
    assert all(c.capex_meur <= 20.0 for c in result.feasible)


def test_impossible_constraint_yields_no_solution() -> None:
    result = search_designs(constraints=DesignConstraints(max_lcoe_eur_per_gj=1.0))
    assert result.best is None
    assert result.feasible == []


def test_max_capacity_objective_prefers_more_power() -> None:
    result = search_designs(
        objective="max_capacity", constraints=DesignConstraints(max_lcoe_eur_per_gj=100.0)
    )
    assert result.best is not None
    assert result.best.heating_capacity_mw == max(c.heating_capacity_mw for c in result.feasible)


def test_high_dimensional_search_samples_randomly_and_reproducibly() -> None:
    ranges = {
        "injection_temp_c": (25.0, 40.0),
        "heat_pump_cop": (3.5, 5.5),
        "well_cost_meur": (2.0, 5.0),
    }
    kwargs = {"ranges": ranges, "samples": 20, "max_evaluations": 200, "seed": 3}
    r1 = search_designs(**kwargs)
    r2 = search_designs(**kwargs)
    assert r1.n_evaluated == 3 * 200  # grid 20^3 > 200 → random 200 combos
    best1 = r1.best.lcoe_eur_per_gj if r1.best else None
    best2 = r2.best.lcoe_eur_per_gj if r2.best else None
    assert best1 == best2
