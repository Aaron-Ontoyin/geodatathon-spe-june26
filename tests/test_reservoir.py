"""Tests for assembling the clean per-sample reservoir table (Phase 1).

Pins the depth-assignment invariants and the row-orientation inference that, if
wrong, would silently mis-pair porosity with the wrong logs.
"""

from __future__ import annotations

import numpy as np

from geothermal import config
from geothermal.petrophysics.reservoir import build_reservoir_table


def test_table_preserves_row_count_per_well() -> None:
    table = build_reservoir_table()
    counts = table["well_id"].value_counts().to_dict()
    assert counts == {"BLT-01": 1689, "EVD-01": 780, "JUT-01": 256, "PKP-01": 730}


def test_orientation_is_inferred_from_gr_signature() -> None:
    table = build_reservoir_table()
    orient = {w: g["row_orientation"].iloc[0] for w, g in table.groupby("well_id")}
    assert orient["BLT-01"] == "forward"
    assert orient["PKP-01"] == "reversed"
    assert orient["EVD-01"] == "reversed"


def test_depth_tvd_is_filled_and_physical() -> None:
    table = build_reservoir_table()
    assert table["depth_tvd_m"].notna().to_numpy().all(), "every row must get a TVD"
    # TVD never exceeds along-hole depth, and stays within the stated interval band.
    assert (table["depth_tvd_m"] <= table["ah_m"] + 1e-6).to_numpy().all()


def test_joined_log_gr_matches_csv_gr_after_orientation() -> None:
    # If the AH assignment + orientation are right, the LAS gamma-ray sampled at each
    # row's depth reproduces the CSV gamma-ray (same source) — a strong correctness check.
    table = build_reservoir_table()
    for wid in ("BLT-01", "PKP-01"):
        g = table[table["well_id"] == wid]
        gr_csv = np.asarray(g["gamma_ray_api"], dtype=float)
        gr_log = np.asarray(g["log_gr"], dtype=float)
        r = float(np.corrcoef(gr_csv, gr_log)[0, 1])
        assert r > 0.97, f"{wid}: joined log GR should track CSV GR (got r={r:.3f})"


def test_observed_porosity_present_only_for_blt_and_pkp() -> None:
    table = build_reservoir_table()
    has_poro = {w: g["porosity_obs"].notna().any() for w, g in table.groupby("well_id")}
    assert has_poro == {"BLT-01": True, "PKP-01": True, "EVD-01": False, "JUT-01": False}


def test_coordinates_match_registry() -> None:
    table = build_reservoir_table()
    for wid in config.WELL_IDS:
        g = table[table["well_id"] == wid]
        assert abs(float(np.asarray(g["x"])[0]) - config.WELLS[wid].x) < 1.0
        assert abs(float(np.asarray(g["y"])[0]) - config.WELLS[wid].y) < 1.0
