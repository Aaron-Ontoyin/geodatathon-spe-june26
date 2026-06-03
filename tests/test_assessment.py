"""Tests for per-well probabilistic power and demand-centre location (Phase 2)."""

from __future__ import annotations

import numpy as np
import pytest

from geothermal import config
from geothermal.io import load_target_lithologies
from geothermal.resource.assessment import locate_demand_center, well_power_percentiles


def test_well_power_percentiles_are_ordered() -> None:
    df = well_power_percentiles()
    for wid in config.WELL_IDS:
        assert float(df.loc[wid, "P90"]) <= float(df.loc[wid, "P50"])
        assert float(df.loc[wid, "P50"]) <= float(df.loc[wid, "P10"])


def test_well_power_percentiles_track_thermogis_p50() -> None:
    df = well_power_percentiles()
    assert float(df.loc["BLT-01", "P50"]) == pytest.approx(5.1, abs=0.7)
    assert float(df.loc["JUT-01", "P50"]) == pytest.approx(2.3, abs=0.7)
    assert float(df.loc["EVD-01", "P50"]) == 0.0
    assert float(df.loc["PKP-01", "P50"]) == 0.0


def test_blt_has_large_p10_p90_spread() -> None:
    # BLT transmissivity is very uncertain (P10 66 Dm vs P90 1.3 Dm) → huge power spread.
    df = well_power_percentiles()
    assert float(df.loc["BLT-01", "P10"]) > 15.0
    assert float(df.loc["BLT-01", "P90"]) < 2.0


def test_demand_centre_reproduces_well_distances() -> None:
    x, y = locate_demand_center()
    csv = load_target_lithologies()
    for wid in config.WELL_IDS:
        g = csv[csv["well_id"] == wid]
        well_x = float(np.asarray(g["easting"])[0])
        well_y = float(np.asarray(g["northing"])[0])
        d_km = float(np.hypot(x - well_x, y - well_y)) / 1000.0
        expected = float(np.asarray(g["distance_to_usp_km"])[0])
        assert d_km == pytest.approx(expected, abs=1.5)


def test_demand_centre_is_near_blt() -> None:
    # BLT-01 is the closest well (~2 km) to the demand district.
    x, y = locate_demand_center()
    blt = config.WELLS["BLT-01"]
    assert float(np.hypot(x - blt.x, y - blt.y)) / 1000.0 < 3.0
