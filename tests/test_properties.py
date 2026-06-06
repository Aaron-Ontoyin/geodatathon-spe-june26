from __future__ import annotations

from pathlib import Path

import numpy as np
import xarray as xr

from geothermal import config
from geothermal.resource.properties import SiteProperties, grid_properties_at, nearest_well_km


def _grid(path: Path, const: float) -> None:
    xs = np.arange(140000.0, 143001.0, 1000.0)
    ys = np.arange(454000.0, 456001.0, 1000.0)
    data = np.full((ys.size, xs.size), const, dtype=float)
    xr.Dataset({"data": (("y", "x"), data)}, coords={"x": xs, "y": ys}).to_netcdf(path)


def _scenario_root(tmp: Path) -> Path:
    d = tmp / "6_Permian" / "Upper Rotliegend Gp (RO)" / "Heat Pump"
    d.mkdir(parents=True)
    consts = {
        "power_p50": 5.0,
        "temperature": 77.0,
        "depth": 2200.0,
        "permeability_p50": 80.0,
        "thickness_p50": 100.0,
        "net_to_gross": 0.9,
    }
    for p, c in consts.items():
        _grid(d / f"RO_STACKED_{p}_HP.nc", c)
    return tmp


def test_grid_properties_at_assembles_site(tmp_path: Path) -> None:
    root = _scenario_root(tmp_path)
    sp = grid_properties_at(
        root,
        141000.0,
        455000.0,
        scenario="heat_pump",
        min_dist_km=4.0,
        base_sigma_log_trans=1.5,
        sigma_interp_per_km=0.03,
    )
    assert isinstance(sp, SiteProperties)
    assert sp.power_mw_p50 == 5.0
    assert sp.temperature_c == 77.0
    assert sp.depth_m == 2200.0
    assert abs(sp.transmissivity_dm - 7.2) < 1e-6  # 80*100*0.9/1000
    assert sp.source == "thermogis_grid"
    assert sp.sigma_log_trans > 1.5  # base + interp term at 4 km


def test_nearest_well_km_zero_at_a_well() -> None:
    blt = config.WELLS["BLT-01"]
    assert nearest_well_km(blt.x, blt.y) < 1e-6


def test_nearest_well_km_positive_away_from_wells() -> None:
    assert nearest_well_km(150000.0, 460000.0) > 1.0
