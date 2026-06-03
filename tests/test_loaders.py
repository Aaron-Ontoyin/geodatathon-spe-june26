"""Smoke + regression tests for the data loaders.

These also pin the known data quirks so a future change that silently "fixes" or
re-breaks them fails loudly.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from geothermal import config
from geothermal.io import (
    load_all_las,
    load_lcoe_input_output,
    load_lithostratigraphy,
    load_target_lithologies,
    load_thermogis,
    load_well_paths,
)


def test_las_loads_all_four_wells() -> None:
    las = load_all_las()
    assert set(las) == set(config.WELL_IDS)
    for wid, data in las.items():
        assert not data.logs.empty, f"{wid} has no log rows"
        assert "GR" in data.curve_names, f"{wid} missing gamma ray"


def test_jut01_depth_unit_collision_is_resolved() -> None:
    # Naive reads index JUT-01 in feet and report ~11 220 "m"; normalised must be sane.
    jut = load_all_las()["JUT-01"]
    depths = np.asarray(jut.logs.index, dtype=float)
    assert depths.max() < 4000, "JUT-01 depth still in feet (unit collision unresolved)"
    assert any("depth" in n.lower() for n in jut.notes)


def test_blt01_is_log_rich() -> None:
    blt = load_all_las()["BLT-01"]
    for curve in ("GR", "RHOB", "NPHI", "DTC"):
        assert curve in blt.curve_names


def test_well_paths_have_six_columns_and_are_sorted() -> None:
    paths = load_well_paths()
    assert set(paths) == set(config.WELL_IDS)
    for wid, df in paths.items():
        assert list(df.columns)[:4] == ["md_m", "inclination_deg", "azimuth_deg", "tvd_m"]
        assert df["md_m"].is_monotonic_increasing, f"{wid} survey not sorted by MD"
        # TVD never exceeds MD for a real wellbore.
        assert (df["tvd_m"] <= df["md_m"] + 1e-6).all()


def test_lithostratigraphy_has_tops_for_each_well() -> None:
    tops = load_lithostratigraphy()
    assert set(tops) == set(config.WELL_IDS)
    for wid, df in tops.items():
        assert {"unit", "top_m", "bottom_m"}.issubset(df.columns)
        assert (df["bottom_m"] >= df["top_m"]).all(), f"{wid} inverted tops"


def test_thermogis_sheet_mislabel_is_documented() -> None:
    tg = load_thermogis()
    assert set(tg) == set(config.WELL_IDS)
    # The BLT-01 sheet's inner Well Name cell is wrong, but coordinates are BLT-01's.
    blt = tg["BLT-01"]
    assert blt.inner_label == "PKP-01"
    assert abs(blt.x - config.WELLS["BLT-01"].x) < 1.0
    # Key reservoir properties are present and ordered P90 <= P10.
    assert blt.value("Permeability", "P90") <= blt.value("Permeability", "P10")


def test_target_lithologies_quirks() -> None:
    df = load_target_lithologies()
    assert len(df) == 3455
    assert df["depth_tvd_m"].isna().to_numpy().all(), "depth_tvd_m should be entirely missing"
    assert df["porosity_pct"].isna().to_numpy().any(), "porosity gaps expected"
    assert (df["flag"] == "check").to_numpy().all()


def test_lcoe_input_output_loads() -> None:
    raw = load_lcoe_input_output()
    assert isinstance(raw, pd.DataFrame)
    assert raw.shape[0] > 20
