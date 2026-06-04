"""Tests for the least-LCoE design optimisation and Monte-Carlo bands (Phase 4)."""

from __future__ import annotations

from geothermal.economics.optimization import (
    doublet_capacity_mw,
    evaluate_candidate,
    lcoe_monte_carlo,
    optimize,
)


def test_lower_injection_temperature_yields_more_capacity() -> None:
    # A heat pump injecting colder deepens ΔT, extracting more geothermal power.
    assert doublet_capacity_mw(25.0) > doublet_capacity_mw(39.0)


def test_two_doublets_meet_demand() -> None:
    candidate = evaluate_candidate(2)
    assert candidate.meets_demand
    assert candidate.heating_capacity_mw >= 10.0


def test_optimize_returns_feasible_designs_sorted_by_lcoe() -> None:
    ranked = optimize()
    assert len(ranked) >= 1
    assert all(c.meets_demand for c in ranked)
    lcoes = [c.lcoe_eur_per_gj for c in ranked]
    assert lcoes == sorted(lcoes)


def test_monte_carlo_bands_are_ordered_and_finite() -> None:
    band = lcoe_monte_carlo(2, n_samples=400, seed=7)
    assert band["p10"] <= band["p50"] <= band["p90"]
    assert band["p50"] > 0
    assert all(v == v for v in band.values())  # no NaNs


def test_monte_carlo_is_reproducible() -> None:
    a = lcoe_monte_carlo(2, n_samples=300, seed=11)
    b = lcoe_monte_carlo(2, n_samples=300, seed=11)
    assert a["p50"] == b["p50"]
