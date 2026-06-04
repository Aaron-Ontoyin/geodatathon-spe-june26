"""Tests for one-way sensitivity analysis (Phase 5d).

Confirms the critical economic drivers move LCoE the right way, and that the soft
siting assumptions (demand weight, well spacing) do NOT change the recommendation —
the robustness claim we make in the report.
"""

from __future__ import annotations

import numpy as np

from geothermal.assumptions import DEFAULT_ASSUMPTIONS
from geothermal.economics.sensitivity import lcoe_sensitivity, tornado
from geothermal.resource.spatial import recommend_new_well


def test_lcoe_increases_with_electricity_price() -> None:
    df = lcoe_sensitivity("electricity_price_eur_per_mwhe", [100.0, 150.0, 200.0, 300.0])
    lcoes = np.asarray(df["lcoe_eur_per_gj"], dtype=float)
    assert np.all(np.diff(lcoes) > 0)


def test_lcoe_increases_with_well_cost() -> None:
    df = lcoe_sensitivity("well_cost_meur", [2.0, 3.0, 4.0, 5.0])
    lcoes = np.asarray(df["lcoe_eur_per_gj"], dtype=float)
    assert np.all(np.diff(lcoes) > 0)


def test_tornado_ranks_drivers_by_swing() -> None:
    df = tornado(
        {
            "electricity_price_eur_per_mwhe": (100.0, 200.0),
            "well_cost_meur": (2.0, 5.0),
            "fixed_om_rate": (0.005, 0.02),
        }
    )
    assert len(df) == 3
    swing = np.asarray(df["swing"], dtype=float)
    assert np.all(swing >= 0)
    assert np.all(np.diff(swing) <= 1e-9)  # sorted by impact, descending


def test_recommendation_robust_to_demand_weight() -> None:
    for weight in (0.0, 0.1, 0.5):
        rec = recommend_new_well(
            assumptions=DEFAULT_ASSUMPTIONS.model_copy(
                update={"demand_distance_weight_mw_per_km": weight}
            )
        )
        assert rec["distance_to_blt_km"] < 3.0  # always steps out by the proven hotspot


def test_recommendation_robust_to_well_spacing() -> None:
    for spacing in (1.0, 1.5, 2.0):
        rec = recommend_new_well(
            assumptions=DEFAULT_ASSUMPTIONS.model_copy(update={"min_well_spacing_km": spacing})
        )
        assert rec["power_mw_p50"] > 1.0
        assert rec["distance_to_usp_km"] < 6.0
