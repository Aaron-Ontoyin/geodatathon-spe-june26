from __future__ import annotations

from pathlib import Path

import numpy as np
import xarray as xr

from geothermal.resource.thermogis_grid import crop_box, grid_path, value_at


def _write_grid(path: Path) -> None:
    xs = np.arange(140000.0, 143001.0, 1000.0)  # 4 cells
    ys = np.arange(454000.0, 456001.0, 1000.0)  # 3 cells
    data = np.arange(12, dtype=float).reshape(len(ys), len(xs))
    xr.Dataset({"data": (("y", "x"), data)}, coords={"x": xs, "y": ys}).to_netcdf(path)


def test_value_at_returns_nearest_cell(tmp_path: Path) -> None:
    p = tmp_path / "g.nc"
    _write_grid(p)
    assert value_at(p, 140100.0, 454100.0) == 0.0
    assert value_at(p, 143000.0, 456000.0) == 11.0


def test_crop_box_limits_extent(tmp_path: Path) -> None:
    p = tmp_path / "g.nc"
    _write_grid(p)
    xs, ys, vals = crop_box(p, center=(141500.0, 455000.0), size_m=2000.0)
    assert xs.min() >= 140000.0 and xs.max() <= 143000.0
    assert vals.shape == (ys.size, xs.size)


def test_grid_path_builds_scenario_filename(tmp_path: Path) -> None:
    root = tmp_path
    p = grid_path(root, scenario="heat_pump", prop="power_p50")
    assert p.name == "RO_STACKED_power_p50_HP.nc"
    assert "Heat Pump" in str(p)
    base = grid_path(root, scenario="basecase", prop="temperature")
    assert base.name == "RO_STACKED_temperature.nc"
    assert "BaseCase" in str(base)
