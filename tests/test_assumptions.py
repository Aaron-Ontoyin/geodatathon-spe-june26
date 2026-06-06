"""Tests that the typed Assumptions config flows through the whole pipeline (Phase 5a).

Defaults must reproduce the known results; changing a single field must move the
right downstream number — proof that every lever is a real, wired parameter.
"""

from __future__ import annotations

import numpy as np
import pytest

from geothermal import config
from geothermal.assumptions import DEFAULT_ASSUMPTIONS
from geothermal.design import district_demand
from geothermal.economics.optimization import evaluate_candidate, optimize
from geothermal.resource.spatial import recommend_new_well


def test_defaults_reproduce_known_optimum() -> None:
    best = optimize()[0]
    assert best.n_doublets == 1
    assert best.lcoe_eur_per_gj == pytest.approx(20.9, abs=1.0)


def test_higher_electricity_price_raises_lcoe() -> None:
    base = evaluate_candidate(1).lcoe_eur_per_gj
    pricey = evaluate_candidate(
        1,
        assumptions=DEFAULT_ASSUMPTIONS.model_copy(
            update={"electricity_price_eur_per_mwhe": 300.0}
        ),
    ).lcoe_eur_per_gj
    assert pricey > base


def test_cheaper_wells_lower_capex() -> None:
    base = evaluate_candidate(2).capex_meur
    cheap = evaluate_candidate(
        2, assumptions=DEFAULT_ASSUMPTIONS.model_copy(update={"well_cost_meur": 1.0})
    ).capex_meur
    assert cheap < base


def test_demand_peaks_flow_through() -> None:
    profile = district_demand(
        assumptions=DEFAULT_ASSUMPTIONS.model_copy(update={"heating_peak_mw": 20.0})
    )
    assert float(np.max(profile.heating_mw)) == pytest.approx(20.0)


def test_well_spacing_constraint_is_honoured() -> None:
    rec = recommend_new_well(
        assumptions=DEFAULT_ASSUMPTIONS.model_copy(update={"min_well_spacing_km": 3.0})
    )
    for wid in config.WELL_IDS:
        w = config.WELLS[wid]
        spacing_km = float(np.hypot(rec["x"] - w.x, rec["y"] - w.y)) / 1000.0
        assert spacing_km >= 2.9, f"spacing assumption not honoured near {wid}"


def test_new_siting_and_cost_fields_have_documented_defaults() -> None:
    a = DEFAULT_ASSUMPTIONS
    assert a.aoi_center_rd == (141171.0, 454890.0)
    assert a.aoi_size_km == 20.0
    assert a.viability_floor_mw > 0
    assert a.well_curvature_factor == 1.1
    assert a.base_sigma_log_trans > 0
    assert a.sigma_interp_per_km >= 0
    assert a.shortlist_size >= 4
