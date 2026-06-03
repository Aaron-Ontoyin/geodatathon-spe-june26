"""Tests for the spatial resource map and new-well siting (Phase 2)."""

from __future__ import annotations

import numpy as np
import pytest

from geothermal import config
from geothermal.io import load_thermogis
from geothermal.resource.spatial import interpolate_resource, recommend_new_well, resource_grid


def test_interpolation_recovers_well_values() -> None:
    tg = load_thermogis()
    for wid in config.WELL_IDS:
        w = config.WELLS[wid]
        trans, temp = interpolate_resource(np.array([w.x]), np.array([w.y]))
        assert float(trans[0]) == pytest.approx(tg[wid].value("Transmissivity"), rel=0.1)
        assert float(temp[0]) == pytest.approx(tg[wid].value("Temperature"), abs=2.0)


def test_resource_power_peaks_near_blt() -> None:
    grid = resource_grid(n=60)
    idx = np.unravel_index(int(np.argmax(grid.power_mw)), grid.power_mw.shape)
    blt = config.WELLS["BLT-01"]
    assert float(np.hypot(grid.x[idx] - blt.x, grid.y[idx] - blt.y)) / 1000.0 < 4.0


def test_recommended_well_is_viable_spaced_and_near_demand() -> None:
    rec = recommend_new_well()
    assert rec["power_mw_p50"] > 1.0
    for wid in config.WELL_IDS:
        w = config.WELLS[wid]
        spacing_km = float(np.hypot(rec["x"] - w.x, rec["y"] - w.y)) / 1000.0
        assert spacing_km >= 1.4, f"too close to {wid}"
    assert rec["distance_to_usp_km"] < 6.0
