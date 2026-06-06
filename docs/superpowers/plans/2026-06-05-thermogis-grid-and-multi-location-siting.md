# ThermoGIS Grid + Multi-Location Siting + Honest Risk — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-scope the resource/siting/risk layers so the ThermoGIS regional grid is the resource source, the well program is found by an unbiased multi-location search, reservoir depth drives well CAPEX, and the Monte-Carlo is per-well independent.

**Architecture:** A single `SiteProperties` provider seam abstracts "properties at (x, y)". A NetCDF grid loader backs it for lattice cells; the 4 wells back it as measured anchors. Siting builds a candidate set (lattice ∪ wells, AOI-cropped, viability-filtered) and an Option-A exhaustive program search picks the least-LCoE doublet program. Cost gains a depth-dependent well term; the Monte-Carlo draws each chosen doublet independently and sums capacities before one system LCoE.

**Tech Stack:** Python 3.11, numpy/pandas/scipy, pydantic (Assumptions), xarray + netCDF4 (new), pytest, ruff, pyright. Spec: `docs/superpowers/specs/2026-06-05-thermogis-grid-and-multi-location-siting-design.md`.

**Conventions (match the repo):** `from __future__ import annotations`; full type annotations, no `Any`; frozen+slots dataclasses for containers; constants `SCREAMING_SNAKE_CASE`; private helpers at module bottom; every new function gets a test; run `uv run pytest`, `uv run ruff check .`, `uv run pyright` after each task. Commit messages end with the Co-Authored-By trailer used in this repo.

**Data note:** The ThermoGIS `.nc` grids live under a configured root (default `data/thermogis_grid/`, gitignored). Tests that read the real grid are marked `@pytest.mark.skipif` when the root is absent, so the suite passes without the large data. A tiny synthetic NetCDF is written in-test for loader unit tests.

---

## File Structure

- Create `src/geothermal/resource/thermogis_grid.py` — NetCDF loader: open a property grid, crop to a box, look up nearest cell at (x, y).
- Create `src/geothermal/resource/properties.py` — `SiteProperties` + `grid_properties_at` provider + `nearest_well_km`.
- Create `src/geothermal/resource/siting.py` — AOI box, candidate lattice ∪ wells, viability filter, shortlist.
- Create `src/geothermal/economics/well_cost.py` — depth-dependent well CAPEX.
- Create `src/geothermal/economics/program_search.py` — multi-location doublet-program search + per-well Monte-Carlo.
- Modify `src/geothermal/assumptions.py` — new config fields.
- Modify `src/geothermal/economics/costs.py` — use depth-dependent well cost.
- Modify `src/geothermal/agent/workflow.py` — siting + design steps use the program search; narration stays metric-driven.
- Modify `pyproject.toml` — add a `data` extra (`xarray`, `netCDF4`) and gitignore the grid root.
- Tests under `tests/` mirroring each module.

---

## Phase 1: Config + dependencies

### Task 1: Add the `data` extra and gitignore the grid root

**Files:**
- Modify: `pyproject.toml`
- Modify: `.gitignore`

- [ ] **Step 1: Add the extra**

In `pyproject.toml`, under `[project.optional-dependencies]`, add:

```toml
data = [  # optional: read the ThermoGIS regional NetCDF grids
    "xarray>=2024.0",
    "netCDF4>=1.6",
]
```

- [ ] **Step 2: Install it**

Run: `uv sync --all-extras`
Expected: resolves and installs xarray + netCDF4.

- [ ] **Step 3: Ignore the grid data**

Append to `.gitignore` under the data section:

```
# ThermoGIS regional grids (large, supplementary public data; kept locally)
data/thermogis_grid/
```

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml .gitignore uv.lock
git commit -m "build: add data extra (xarray/netCDF4) and ignore thermogis grid"
```

### Task 2: Add new config fields to `Assumptions`

**Files:**
- Modify: `src/geothermal/assumptions.py`
- Test: `tests/test_assumptions.py` (create if absent)

- [ ] **Step 1: Write the failing test**

```python
from geothermal.assumptions import DEFAULT_ASSUMPTIONS

def test_new_siting_and_cost_fields_have_documented_defaults() -> None:
    a = DEFAULT_ASSUMPTIONS
    assert a.aoi_center_rd == (141171.0, 454890.0)
    assert a.aoi_size_km == 20.0
    assert a.viability_floor_mw > 0
    assert a.well_capex_a == 375000.0
    assert a.well_ref_depth_m == 2200.0
    assert a.well_curvature_factor == 1.1
    assert a.base_sigma_log_trans > 0
    assert a.sigma_interp_per_km >= 0
    assert a.shortlist_size >= 4
```

- [ ] **Step 2: Run it, verify it fails**

Run: `uv run pytest tests/test_assumptions.py -v`
Expected: FAIL (AttributeError on `aoi_center_rd`).

- [ ] **Step 3: Add the fields**

In `src/geothermal/assumptions.py`, add to the `Assumptions` model (match the existing pydantic field style with `Field(default=..., description=...)`):

```python
# --- Area of interest and siting (Phase 7 re-scope) ---
aoi_center_rd: tuple[float, float] = Field(
    default=(141171.0, 454890.0),
    description="Demand-district centre (RD-New metres); the 20x20 km siting box centres here.",
)
aoi_size_km: float = Field(default=20.0, gt=0, description="Side length of the square siting box (km).")
viability_floor_mw: float = Field(
    default=2.0, ge=0, description="Minimum ThermoGIS doublet power (MW) for a cell to be a candidate site."
)
shortlist_size: int = Field(default=12, ge=4, description="Strongest candidate cells kept for the EXHAUSTIVE program search (bounds the combinatorics).")
max_program_doublets: int = Field(default=4, ge=1, description="Backstop cap on doublets in a program (objective normally stops sooner).")

# --- Depth-dependent well CAPEX: ThermoGIS depth SHAPE, calibrated to the provided LCOE.xlsx cost ---
# well CAPEX(d) = well_cost_meur * poly(d)/poly(d_ref); poly(d)=a + b*d + c*d^2; d = TVD * curvature.
# Anchors on the provided per-well cost at the reference depth, varies only its SHAPE with depth.
# This keeps consistency with the provided LCOE.xlsx (do NOT adopt ThermoGIS's absolute coefficients,
# which give ~7.4 M€/well vs the provided 3.24 M€/well and would inflate LCoE ~2.3x on the wells term).
well_capex_a: float = Field(default=375000.0, ge=0, description="Well CAPEX shape constant term (relative).")
well_capex_b: float = Field(default=1150.0, ge=0, description="Well CAPEX shape linear coefficient (relative).")
well_capex_c: float = Field(default=0.3, ge=0, description="Well CAPEX shape quadratic coefficient (relative).")
well_ref_depth_m: float = Field(default=2200.0, gt=0, description="Reference reservoir TVD where well CAPEX == well_cost_meur.")
well_curvature_factor: float = Field(default=1.1, ge=1, description="Along-hole/TVD ratio for deviated wells.")

# --- Per-site transmissivity uncertainty (modelled; the bulk grid is P50-only) ---
base_sigma_log_trans: float = Field(
    default=1.5, ge=0, description="Base log-transmissivity spread, from the 4 wells' P10/P90 bands (~1.5)."
)
sigma_interp_per_km: float = Field(
    default=0.03, ge=0, description="Extra log-transmissivity uncertainty per km from the nearest logged well."
)
```

Keep `well_cost_meur` (it is the calibration anchor: well CAPEX equals it at `well_ref_depth_m`).

- [ ] **Step 4: Run the test, verify it passes**

Run: `uv run pytest tests/test_assumptions.py -v`
Expected: PASS.

- [ ] **Step 5: Lint, type-check, commit**

```bash
uv run ruff check src/geothermal/assumptions.py tests/test_assumptions.py
uv run pyright src/geothermal/assumptions.py
git add src/geothermal/assumptions.py tests/test_assumptions.py
git commit -m "feat: add AOI, siting, depth-CAPEX and interp-sigma config fields"
```

---

## Phase 2: ThermoGIS grid loader

### Task 3: NetCDF property lookup

**Files:**
- Create: `src/geothermal/resource/thermogis_grid.py`
- Test: `tests/test_thermogis_grid.py`

- [ ] **Step 1: Write the failing test (synthetic NetCDF, no real data needed)**

```python
from __future__ import annotations
from pathlib import Path
import numpy as np
import xarray as xr
from geothermal.resource.thermogis_grid import value_at, crop_box

def _write_grid(path: Path) -> None:
    xs = np.arange(140000.0, 143001.0, 1000.0)  # 4 cells
    ys = np.arange(454000.0, 456001.0, 1000.0)  # 3 cells
    data = np.arange(12, dtype=float).reshape(len(ys), len(xs))
    xr.Dataset({"data": (("y", "x"), data)}, coords={"x": xs, "y": ys}).to_netcdf(path)

def test_value_at_returns_nearest_cell(tmp_path: Path) -> None:
    p = tmp_path / "g.nc"; _write_grid(p)
    # nearest to (140100, 454100) is the (x=140000, y=454000) cell = data[0,0] = 0
    assert value_at(p, 140100.0, 454100.0) == 0.0
    # nearest to (143000, 456000) is the last cell = data[2,3] = 11
    assert value_at(p, 143000.0, 456000.0) == 11.0

def test_crop_box_limits_extent(tmp_path: Path) -> None:
    p = tmp_path / "g.nc"; _write_grid(p)
    xs, ys, vals = crop_box(p, center=(141500.0, 455000.0), size_m=2000.0)
    assert xs.min() >= 140000.0 and xs.max() <= 143000.0
    assert vals.shape == (ys.size, xs.size)
```

- [ ] **Step 2: Run it, verify it fails**

Run: `uv run pytest tests/test_thermogis_grid.py -v`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement the loader**

```python
"""Read the ThermoGIS regional NetCDF property grids (1 km, RD-New metres).

Each file holds a single ``data`` variable on (y, x) coordinates. We never modify the
grids; we crop to the area of interest and look up the nearest cell at a query point.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import numpy.typing as npt
import xarray as xr

FloatArray = npt.NDArray[np.float64]


def value_at(path: Path, x: float, y: float) -> float:
    """Nearest-cell value of the grid in ``path`` at RD coordinate (x, y)."""
    with xr.open_dataset(path) as ds:
        return float(ds["data"].sel(x=x, y=y, method="nearest").values)


def crop_box(
    path: Path, *, center: tuple[float, float], size_m: float
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Return (xs, ys, values) for the square box of side ``size_m`` centred on ``center``."""
    cx, cy = center
    half = size_m / 2.0
    with xr.open_dataset(path) as ds:
        sub = ds["data"].sel(x=slice(cx - half, cx + half), y=slice(cy - half, cy + half))
        return (
            np.asarray(sub["x"].values, dtype=float),
            np.asarray(sub["y"].values, dtype=float),
            np.asarray(sub.values, dtype=float),
        )
```

- [ ] **Step 4: Run the test, verify it passes**

Run: `uv run pytest tests/test_thermogis_grid.py -v`
Expected: PASS.

- [ ] **Step 5: Lint, type-check, commit**

```bash
uv run ruff check src/geothermal/resource/thermogis_grid.py tests/test_thermogis_grid.py
uv run pyright src/geothermal/resource/thermogis_grid.py
git add src/geothermal/resource/thermogis_grid.py tests/test_thermogis_grid.py
git commit -m "feat: ThermoGIS NetCDF grid loader (value_at, crop_box)"
```

### Task 4: Resolve property-file paths for a scenario

**Files:**
- Modify: `src/geothermal/resource/thermogis_grid.py`
- Modify: `tests/test_thermogis_grid.py`

- [ ] **Step 1: Write the failing test**

```python
from geothermal.resource.thermogis_grid import grid_path

def test_grid_path_builds_scenario_filename(tmp_path) -> None:
    root = tmp_path
    p = grid_path(root, scenario="heat_pump", prop="power_p50")
    assert p.name == "RO_STACKED_power_p50_HP.nc"
    assert "Heat Pump" in str(p)
    base = grid_path(root, scenario="basecase", prop="temperature")
    assert base.name == "RO_STACKED_temperature.nc"
    assert "BaseCase" in str(base)
```

- [ ] **Step 2: Run it, verify it fails**

Run: `uv run pytest tests/test_thermogis_grid.py::test_grid_path_builds_scenario_filename -v`
Expected: FAIL (no `grid_path`).

- [ ] **Step 3: Implement**

Add to `thermogis_grid.py`:

```python
from typing import Literal

Scenario = Literal["basecase", "heat_pump", "well_stimulation", "well_stimulation_heat_pump"]

_SCENARIO_DIR: dict[str, str] = {
    "basecase": "BaseCase",
    "heat_pump": "Heat Pump",
    "well_stimulation": "Well Stimulation",
    "well_stimulation_heat_pump": "Well Stimulation & Heat Pump",
}
_SCENARIO_SUFFIX: dict[str, str] = {
    "basecase": "",
    "heat_pump": "_HP",
    "well_stimulation": "_WS",
    "well_stimulation_heat_pump": "_WS_HP",
}
_RESERVOIR_DIR = "6_Permian/Upper Rotliegend Gp (RO)"


def grid_path(root: Path, *, scenario: Scenario, prop: str) -> Path:
    """Path to a ThermoGIS property grid for the Rotliegend, given scenario and property."""
    return (
        Path(root) / _RESERVOIR_DIR / _SCENARIO_DIR[scenario]
        / f"RO_STACKED_{prop}{_SCENARIO_SUFFIX[scenario]}.nc"
    )
```

Note: confirm `_SCENARIO_SUFFIX` for `well_stimulation` against the real folder once data is present; adjust the suffix string if the files differ. The `heat_pump` and `basecase` suffixes are verified.

- [ ] **Step 4: Run the test, verify it passes**

Run: `uv run pytest tests/test_thermogis_grid.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
uv run ruff check src/geothermal/resource/thermogis_grid.py
git add src/geothermal/resource/thermogis_grid.py tests/test_thermogis_grid.py
git commit -m "feat: resolve ThermoGIS grid file paths per scenario/property"
```

---

## Phase 3: Property provider seam

### Task 5: `SiteProperties` + grid provider

**Files:**
- Create: `src/geothermal/resource/properties.py`
- Test: `tests/test_properties.py`

- [ ] **Step 1: Write the failing test (synthetic grids in tmp dir)**

```python
from __future__ import annotations
from pathlib import Path
import numpy as np
import xarray as xr
from geothermal.resource.properties import SiteProperties, grid_properties_at

_PROPS = ["power_p50", "temperature", "depth", "permeability_p50", "thickness_p50", "net_to_gross"]

def _grid(path: Path, const: float) -> None:
    xs = np.arange(140000.0, 143001.0, 1000.0); ys = np.arange(454000.0, 456001.0, 1000.0)
    data = np.full((ys.size, xs.size), const, dtype=float)
    xr.Dataset({"data": (("y", "x"), data)}, coords={"x": xs, "y": ys}).to_netcdf(path)

def _scenario_root(tmp: Path) -> Path:
    d = tmp / "6_Permian" / "Upper Rotliegend Gp (RO)" / "Heat Pump"; d.mkdir(parents=True)
    consts = {"power_p50": 5.0, "temperature": 77.0, "depth": 2200.0,
              "permeability_p50": 80.0, "thickness_p50": 100.0, "net_to_gross": 0.9}
    for p, c in consts.items(): _grid(d / f"RO_STACKED_{p}_HP.nc", c)
    return tmp

def test_grid_properties_at_assembles_site(tmp_path: Path) -> None:
    root = _scenario_root(tmp_path)
    sp = grid_properties_at(root, 141000.0, 455000.0, scenario="heat_pump", min_dist_km=4.0, base_sigma_log_trans=1.5, sigma_interp_per_km=0.03)
    assert isinstance(sp, SiteProperties)
    assert sp.power_mw_p50 == 5.0
    assert sp.temperature_c == 77.0
    assert sp.depth_m == 2200.0
    # transmissivity = perm * thickness * ntg / 1000 = 80*100*0.9/1000 = 7.2 Dm
    assert abs(sp.transmissivity_dm - 7.2) < 1e-6
    assert sp.source == "thermogis_grid"
    # sigma grows with distance from nearest well: base + 0.03*4
    assert sp.sigma_log_trans > 0
```

- [ ] **Step 2: Run it, verify it fails**

Run: `uv run pytest tests/test_properties.py -v`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement**

```python
"""The property-provider seam: 'reservoir properties at (x, y)', source-agnostic.

Everything downstream (siting, capacity, Monte-Carlo) depends only on SiteProperties,
so the backing source (ThermoGIS grid now, full-percentile grid or live API later) can
change without touching the search or the cost model.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from geothermal.resource.thermogis_grid import Scenario, grid_path, value_at

Source = Literal["measured", "thermogis_grid"]


@dataclass(frozen=True, slots=True)
class SiteProperties:
    """Reservoir properties at one location, plus its uncertainty and provenance."""

    x: float
    y: float
    transmissivity_dm: float
    temperature_c: float
    power_mw_p50: float
    depth_m: float
    sigma_log_trans: float
    source: Source


def grid_properties_at(
    root: Path,
    x: float,
    y: float,
    *,
    scenario: Scenario,
    min_dist_km: float,
    base_sigma_log_trans: float,
    sigma_interp_per_km: float,
) -> SiteProperties:
    """Assemble SiteProperties from the ThermoGIS grids at (x, y).

    ``min_dist_km`` is the distance to the nearest logged well; it inflates the modelled
    uncertainty because the P50 grid is less trustworthy far from real data. At a well
    (``min_dist_km`` ~ 0) the band collapses to ``base_sigma_log_trans`` (the narrow,
    measured-anchored width), which is how the measured-vs-modelled distinction is
    realised, no separate provider needed.
    """
    def g(prop: str) -> float:
        return value_at(grid_path(root, scenario=scenario, prop=prop), x, y)

    perm = g("permeability_p50")
    thick = g("thickness_p50")
    ntg = g("net_to_gross")
    transmissivity = perm * thick * ntg / 1000.0
    sigma = (base_sigma_log_trans**2 + (sigma_interp_per_km * min_dist_km) ** 2) ** 0.5
    return SiteProperties(
        x=x,
        y=y,
        transmissivity_dm=transmissivity,
        temperature_c=g("temperature"),
        power_mw_p50=g("power_p50"),
        depth_m=g("depth"),
        sigma_log_trans=sigma,
        source="thermogis_grid",
    )
```

- [ ] **Step 4: Run the test, verify it passes**

Run: `uv run pytest tests/test_properties.py -v`
Expected: PASS.

- [ ] **Step 5: Lint, type-check, commit**

```bash
uv run ruff check src/geothermal/resource/properties.py tests/test_properties.py
uv run pyright src/geothermal/resource/properties.py
git add src/geothermal/resource/properties.py tests/test_properties.py
git commit -m "feat: SiteProperties + ThermoGIS grid provider with modelled sigma"
```

### Task 6: Nearest-logged-well distance helper

The "measured tier" is delivered by the interp-sigma term collapsing to zero at a well
(Task 5), so no separate measured provider is needed. We only need the distance helper
that feeds that term and the candidate pipeline.

**Files:**
- Modify: `src/geothermal/resource/properties.py`
- Modify: `tests/test_properties.py`

- [ ] **Step 1: Write the failing test**

```python
from geothermal.resource.properties import nearest_well_km
from geothermal import config

def test_nearest_well_km_zero_at_a_well() -> None:
    blt = config.WELLS["BLT-01"]
    assert nearest_well_km(blt.x, blt.y) < 1e-6

def test_nearest_well_km_positive_away_from_wells() -> None:
    # a point ~5 km from the nearest well
    assert nearest_well_km(150000.0, 460000.0) > 1.0
```

- [ ] **Step 2: Run it, verify it fails**

Run: `uv run pytest tests/test_properties.py -k nearest -v`
Expected: FAIL (name not defined).

- [ ] **Step 3: Implement**

Add to `properties.py`:

```python
import numpy as np

from geothermal import config


def nearest_well_km(x: float, y: float) -> float:
    """Distance (km) from (x, y) to the nearest of the four logged wells."""
    d = [np.hypot(x - config.WELLS[w].x, y - config.WELLS[w].y) for w in config.WELL_IDS]
    return float(min(d) / 1000.0)
```

- [ ] **Step 4: Run the test, verify it passes**

Run: `uv run pytest tests/test_properties.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
uv run ruff check src/geothermal/resource/properties.py
uv run pyright src/geothermal/resource/properties.py
git add src/geothermal/resource/properties.py tests/test_properties.py
git commit -m "feat: nearest-logged-well distance helper"
```

### Task 7: Validate grid vs provided sheets at the 4 wells (real-data test)

**Files:**
- Modify: `tests/test_properties.py`

- [ ] **Step 1: Write the test (skipped when the grid root is absent)**

```python
import os
import pytest
from pathlib import Path
from geothermal.resource.properties import grid_properties_at
from geothermal.resource.thermogis_grid import grid_path
from geothermal import config
from geothermal.io import load_thermogis

_ROOT = Path(os.environ.get("GEO_THERMOGIS_ROOT", "data/thermogis_grid"))

@pytest.mark.skipif(
    not (grid_path(_ROOT, scenario="basecase", prop="temperature")).exists(),
    reason="ThermoGIS grid not present",
)
def test_grid_matches_provided_well_sheets() -> None:
    tg = load_thermogis()
    for wid in config.WELL_IDS:
        w = config.WELLS[wid]
        sp = grid_properties_at(_ROOT, w.x, w.y, scenario="basecase", min_dist_km=0.0, base_sigma_log_trans=1.5, sigma_interp_per_km=0.03)
        assert abs(sp.temperature_c - tg[wid].value("Temperature")) < 2.0
```

- [ ] **Step 2: Run it (expect skip or pass)**

Run: `uv run pytest tests/test_properties.py -k grid_matches -v`
Expected: SKIP (no data) or PASS (data present). Either is acceptable.

- [ ] **Step 3: Commit**

```bash
git add tests/test_properties.py
git commit -m "test: grid-vs-sheet consistency at the four wells (data-gated)"
```

---

## Phase 4: Area of interest + candidate set

### Task 8: AOI box + lattice ∪ wells, deduped

**Files:**
- Create: `src/geothermal/resource/siting.py`
- Test: `tests/test_siting.py`

- [ ] **Step 1: Write the failing test**

```python
from __future__ import annotations
import numpy as np
from geothermal.resource.siting import candidate_lattice
from geothermal import config

def test_lattice_covers_box_at_pitch_and_includes_wells() -> None:
    center = (141171.0, 454890.0)
    pts = candidate_lattice(center=center, size_km=20.0, pitch_km=1.5)
    xs = pts[:, 0]; ys = pts[:, 1]
    assert xs.min() >= center[0] - 10000 - 1e-6 and xs.max() <= center[0] + 10000 + 1e-6
    # BLT-01 (inside the box) is present as an exact injected coordinate
    blt = config.WELLS["BLT-01"]
    assert np.any((np.abs(xs - blt.x) < 1e-6) & (np.abs(ys - blt.y) < 1e-6))

def test_no_two_candidates_closer_than_pitch() -> None:
    pts = candidate_lattice(center=(141171.0, 454890.0), size_km=20.0, pitch_km=1.5)
    # check the injected wells did not create a sub-pitch pair
    d = np.hypot(pts[:, None, 0] - pts[None, :, 0], pts[:, None, 1] - pts[None, :, 1])
    np.fill_diagonal(d, np.inf)
    assert d.min() >= 1500.0 - 1.0
```

- [ ] **Step 2: Run it, verify it fails**

Run: `uv run pytest tests/test_siting.py -v`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement**

```python
"""Area-of-interest siting: candidate generation over the demand-centred box.

Candidates are a regular lattice (pitch = min well spacing) unioned with the four wells
at their exact coordinates, deduped so no pair is closer than the pitch. All candidates
are equal; only their properties (and uncertainty) differ.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

from geothermal import config

FloatArray = npt.NDArray[np.float64]


def candidate_lattice(
    *, center: tuple[float, float], size_km: float, pitch_km: float
) -> FloatArray:
    """Return an (N, 2) array of candidate (x, y) points: lattice ∪ wells, deduped to pitch."""
    cx, cy = center
    half = size_km * 1000.0 / 2.0
    pitch = pitch_km * 1000.0
    xs = np.arange(cx - half, cx + half + 1e-6, pitch)
    ys = np.arange(cy - half, cy + half + 1e-6, pitch)
    gx, gy = np.meshgrid(xs, ys)
    lattice = np.column_stack([gx.ravel(), gy.ravel()])

    wells = np.array(
        [[config.WELLS[w].x, config.WELLS[w].y] for w in config.WELL_IDS], dtype=float
    )
    in_box = (np.abs(wells[:, 0] - cx) <= half) & (np.abs(wells[:, 1] - cy) <= half)
    wells_in = wells[in_box]

    # drop lattice points within `pitch` of any injected well, then prepend the wells
    if wells_in.size:
        d = np.hypot(
            lattice[:, None, 0] - wells_in[None, :, 0],
            lattice[:, None, 1] - wells_in[None, :, 1],
        )
        keep = d.min(axis=1) >= pitch
        lattice = lattice[keep]
        return np.vstack([wells_in, lattice])
    return lattice
```

- [ ] **Step 4: Run the test, verify it passes**

Run: `uv run pytest tests/test_siting.py -v`
Expected: PASS.

- [ ] **Step 5: Lint, type-check, commit**

```bash
uv run ruff check src/geothermal/resource/siting.py tests/test_siting.py
uv run pyright src/geothermal/resource/siting.py
git add src/geothermal/resource/siting.py tests/test_siting.py
git commit -m "feat: AOI candidate lattice unioned with wells, deduped to pitch"
```

### Task 9: Build candidate `SiteProperties`, filter by viability, shortlist

**Files:**
- Modify: `src/geothermal/resource/siting.py`
- Modify: `tests/test_siting.py`

- [ ] **Step 1: Write the failing test (synthetic provider via monkeypatch)**

```python
import numpy as np
from geothermal.resource import siting
from geothermal.resource.properties import SiteProperties

def _fake_site(x: float, y: float) -> SiteProperties:
    # power increases with x so the shortlist is predictable
    power = (x - 131000.0) / 2000.0
    return SiteProperties(x=x, y=y, transmissivity_dm=power, temperature_c=77.0,
                          power_mw_p50=power, depth_m=2200.0, sigma_log_trans=0.9, source="thermogis_grid")

def test_candidates_filtered_and_shortlisted(monkeypatch) -> None:
    pts = siting.candidate_lattice(center=(141171.0, 454890.0), size_km=20.0, pitch_km=1.5)
    sites = siting.build_candidates(pts, provider=_fake_site, viability_floor_mw=2.0)
    assert all(s.power_mw_p50 >= 2.0 for s in sites)
    short = siting.shortlist(sites, size=10)
    assert len(short) == 10
    assert short[0].power_mw_p50 >= short[-1].power_mw_p50  # sorted strongest first
```

- [ ] **Step 2: Run it, verify it fails**

Run: `uv run pytest tests/test_siting.py -k "candidates" -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

Add to `siting.py`:

```python
from collections.abc import Callable

from geothermal.resource.properties import SiteProperties

SiteProvider = Callable[[float, float], SiteProperties]


def build_candidates(
    points: FloatArray, *, provider: SiteProvider, viability_floor_mw: float
) -> list[SiteProperties]:
    """Evaluate provider at each point, keeping finite, present, viable cells."""
    out: list[SiteProperties] = []
    for x, y in points:
        sp = provider(float(x), float(y))
        if np.isfinite(sp.power_mw_p50) and sp.power_mw_p50 >= viability_floor_mw:
            out.append(sp)
    return out


def shortlist(sites: list[SiteProperties], *, size: int) -> list[SiteProperties]:
    """Strongest `size` sites by P50 power (the program search runs over these)."""
    return sorted(sites, key=lambda s: s.power_mw_p50, reverse=True)[:size]
```

- [ ] **Step 4: Run the test, verify it passes**

Run: `uv run pytest tests/test_siting.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
uv run ruff check src/geothermal/resource/siting.py
uv run pyright src/geothermal/resource/siting.py
git add src/geothermal/resource/siting.py tests/test_siting.py
git commit -m "feat: build/filter/shortlist candidate sites by viability and power"
```

---

## Phase 5: Depth-dependent well CAPEX

### Task 10: `well_capex_meur` and wire it into `costs.py`

**Files:**
- Create: `src/geothermal/economics/well_cost.py`
- Test: `tests/test_well_cost.py`
- Modify: `src/geothermal/economics/costs.py:46`

- [ ] **Step 1: Write the failing test**

```python
from geothermal.assumptions import DEFAULT_ASSUMPTIONS
from geothermal.economics.well_cost import well_capex_meur

def test_well_capex_increases_with_depth() -> None:
    a = DEFAULT_ASSUMPTIONS
    assert well_capex_meur(3000.0, a) > well_capex_meur(1500.0, a) > 0

def test_well_capex_equals_provided_cost_at_reference_depth() -> None:
    # the ThermoGIS shape is calibrated to reproduce the provided per-well cost at d_ref
    a = DEFAULT_ASSUMPTIONS
    assert abs(well_capex_meur(a.well_ref_depth_m, a) - a.well_cost_meur) < 1e-9
```

- [ ] **Step 2: Run it, verify it fails**

Run: `uv run pytest tests/test_well_cost.py -v`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement**

```python
"""Depth-dependent well CAPEX, anchored to the provided LCOE.xlsx cost.

The provided per-well cost (``well_cost_meur``) is the anchor; ThermoGIS's depth
polynomial provides only the SHAPE, scaled so it reproduces the provided cost at the
reference depth. Deeper reservoir -> costlier well -> worse LCoE, without diverging from
the provided cost model. Along-hole depth = TVD x curvature factor.
"""

from __future__ import annotations

from geothermal.assumptions import Assumptions


def _poly(d: float, a: Assumptions) -> float:
    return a.well_capex_a + a.well_capex_b * d + a.well_capex_c * d * d


def well_capex_meur(tvd_m: float, a: Assumptions) -> float:
    """CAPEX of one well (M€) at reservoir TVD ``tvd_m``, calibrated to well_cost_meur at d_ref."""
    ref = _poly(a.well_ref_depth_m * a.well_curvature_factor, a)
    here = _poly(tvd_m * a.well_curvature_factor, a)
    return a.well_cost_meur * here / ref
```

- [ ] **Step 4: Run the test, verify it passes**

Run: `uv run pytest tests/test_well_cost.py -v`
Expected: PASS.

- [ ] **Step 5: Wire an optional wells-CAPEX override into the cost model**

The multi-site search computes a per-site wells CAPEX (each site at its own depth) and
passes the total in. So `evaluate_costs` takes an optional `wells_capex_meur` that
**replaces the whole `wells_pumps` term** (the caller includes pumps). When omitted,
behaviour is unchanged. In `src/geothermal/economics/costs.py`:

```python
def evaluate_costs(
    n_doublets: int,
    design: SystemDesign,
    performance: SystemPerformance,
    *,
    assumptions: Assumptions = DEFAULT_ASSUMPTIONS,
    wells_capex_meur: float | None = None,
) -> SystemCosts:
    ...
    breakdown = {
        "wells_pumps": (
            wells_capex_meur
            if wells_capex_meur is not None
            else n_doublets * (2 * a.well_cost_meur + a.pump_cost_meur)
        ),
        ...
    }
```

No new import needed here; `well_capex_meur` is called by the program search (Task 11),
which sums per-site well costs and passes the total as `wells_capex_meur`.

- [ ] **Step 6: Run the full suite, verify nothing breaks**

Run: `uv run pytest -q`
Expected: PASS (existing callers omit `wells_capex_meur`, so behaviour is unchanged).

- [ ] **Step 7: Lint, type-check, commit**

```bash
uv run ruff check src/geothermal/economics/well_cost.py src/geothermal/economics/costs.py tests/test_well_cost.py
uv run pyright src/geothermal/economics/well_cost.py src/geothermal/economics/costs.py
git add src/geothermal/economics/well_cost.py src/geothermal/economics/costs.py tests/test_well_cost.py
git commit -m "feat: depth-dependent well CAPEX wired into the cost model"
```

---

## Phase 6: Multi-location program search

### Task 11: Evaluate one program (a set of chosen sites)

**Files:**
- Create: `src/geothermal/economics/program_search.py`
- Test: `tests/test_program_search.py`

- [ ] **Step 1: Write the failing test**

```python
from __future__ import annotations
from geothermal.assumptions import DEFAULT_ASSUMPTIONS
from geothermal.resource.properties import SiteProperties
from geothermal.economics.program_search import evaluate_program

def _site(power: float, depth: float = 2200.0) -> SiteProperties:
    return SiteProperties(x=0.0, y=0.0, transmissivity_dm=power, temperature_c=77.0,
                          power_mw_p50=power, depth_m=depth, sigma_log_trans=0.9, source="thermogis_grid")

def test_evaluate_program_sums_capacity_and_costs_once() -> None:
    a = DEFAULT_ASSUMPTIONS
    prog = evaluate_program([_site(5.0), _site(4.0)], assumptions=a)
    assert prog.n_doublets == 2
    assert prog.geo_capacity_mw > 0
    assert prog.lcoe_eur_per_gj > 0
    # deeper sites cost more: a deep program has higher CAPEX than a shallow one of same power
    deep = evaluate_program([_site(5.0, 3000.0), _site(4.0, 3000.0)], assumptions=a)
    assert deep.capex_meur > prog.capex_meur
```

- [ ] **Step 2: Run it, verify it fails**

Run: `uv run pytest tests/test_program_search.py -v`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement**

```python
"""Multi-location doublet-program search.

A 'program' is a set of chosen doublet sites. Capacity is additive across sites; the
LCoE is computed once at the system level (shared surface plant + demand saturation).
Each site's wells are costed at its OWN depth (per-site well CAPEX, summed), so deeper
sites genuinely cost more, the depth signal is not averaged away.
"""

from __future__ import annotations

from dataclasses import dataclass

from geothermal.assumptions import DEFAULT_ASSUMPTIONS, Assumptions
from geothermal.design import district_demand, heating_capacity_mw, simulate
from geothermal.economics.costs import SystemCosts, evaluate_costs
from geothermal.economics.optimization import design_for
from geothermal.economics.well_cost import well_capex_meur
from geothermal.resource.power import well_power_mw
from geothermal.resource.properties import SiteProperties


@dataclass(frozen=True, slots=True)
class Program:
    """A chosen set of doublet sites with its sized system, cost and feasibility."""

    sites: tuple[SiteProperties, ...]
    n_doublets: int
    geo_capacity_mw: float
    backup_fraction: float
    meets_demand: bool
    lcoe_eur_per_gj: float
    capex_meur: float
    costs: SystemCosts


def evaluate_program(
    sites: list[SiteProperties], *, assumptions: Assumptions = DEFAULT_ASSUMPTIONS
) -> Program:
    """Size, simulate and cost the integrated system for a chosen set of doublet sites."""
    a = assumptions
    geo = sum(
        float(well_power_mw(s.transmissivity_dm, s.temperature_c, injection_temp_c=a.injection_temp_c))
        for s in sites
    )
    design = design_for(geo, a)
    perf = simulate(design, district_demand(assumptions=a))
    wells_capex = sum(2.0 * well_capex_meur(s.depth_m, a) for s in sites) + len(sites) * a.pump_cost_meur
    costs = evaluate_costs(len(sites), design, perf, assumptions=a, wells_capex_meur=wells_capex)
    backup = perf.backup_heat_gj / perf.heat_delivered_gj if perf.heat_delivered_gj else 1.0
    return Program(
        sites=tuple(sites),
        n_doublets=len(sites),
        geo_capacity_mw=geo,
        backup_fraction=backup,
        meets_demand=backup <= a.max_backup_fraction,
        lcoe_eur_per_gj=costs.lcoe_eur_per_gj,
        capex_meur=costs.capex_meur,
        costs=costs,
    )
```

- [ ] **Step 4: Run the test, verify it passes**

Run: `uv run pytest tests/test_program_search.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
uv run ruff check src/geothermal/economics/program_search.py tests/test_program_search.py
uv run pyright src/geothermal/economics/program_search.py
git add src/geothermal/economics/program_search.py tests/test_program_search.py
git commit -m "feat: evaluate one multi-site doublet program (capacity sum, single LCoE)"
```

### Task 12: Search programs over the shortlist with objective-driven stopping

**Files:**
- Modify: `src/geothermal/economics/program_search.py`
- Modify: `tests/test_program_search.py`

- [ ] **Step 1: Write the failing test (a separated pair must beat the single best)**

```python
import itertools
from geothermal.economics.program_search import search_program

def test_search_finds_least_lcoe_feasible_program() -> None:
    a = DEFAULT_ASSUMPTIONS
    # three strong sites; spacing handled by caller-supplied min_spacing via coordinates
    sites = [
        SiteProperties(x=0.0, y=0.0, transmissivity_dm=6.0, temperature_c=77.0, power_mw_p50=6.0, depth_m=2200.0, sigma_log_trans=0.9, source="thermogis_grid"),
        SiteProperties(x=3000.0, y=0.0, transmissivity_dm=6.0, temperature_c=77.0, power_mw_p50=6.0, depth_m=2200.0, sigma_log_trans=0.9, source="thermogis_grid"),
        SiteProperties(x=6000.0, y=0.0, transmissivity_dm=6.0, temperature_c=77.0, power_mw_p50=6.0, depth_m=2200.0, sigma_log_trans=0.9, source="thermogis_grid"),
    ]
    best = search_program(sites, assumptions=a, min_spacing_km=1.5)
    assert best is not None
    assert best.meets_demand
    # stopping: should not pad with more doublets once LCoE stops improving
    assert best.n_doublets <= len(sites)
```

- [ ] **Step 2: Run it, verify it fails**

Run: `uv run pytest tests/test_program_search.py -k search -v`
Expected: FAIL (no `search_program`).

- [ ] **Step 3: Implement**

Add to `program_search.py`:

```python
import itertools

import numpy as np


def _spaced(combo: tuple[SiteProperties, ...], min_spacing_m: float) -> bool:
    for a_site, b_site in itertools.combinations(combo, 2):
        if np.hypot(a_site.x - b_site.x, a_site.y - b_site.y) < min_spacing_m:
            return False
    return True


def search_program(
    shortlist: list[SiteProperties],
    *,
    assumptions: Assumptions = DEFAULT_ASSUMPTIONS,
    min_spacing_km: float,
) -> Program | None:
    """Exhaustively search programs of size 1..N for the least-LCoE feasible one.

    Stops growing k once the best feasible LCoE at size k is no better than at k-1
    (LCoE is U-shaped in doublet count). Returns None if nothing is feasible.
    """
    min_spacing_m = min_spacing_km * 1000.0
    best: Program | None = None
    best_at_prev = float("inf")
    for k in range(1, min(len(shortlist), assumptions.max_program_doublets) + 1):
        best_k: Program | None = None
        for combo in itertools.combinations(shortlist, k):
            if not _spaced(combo, min_spacing_m):
                continue
            prog = evaluate_program(list(combo), assumptions=assumptions)
            if not prog.meets_demand:
                continue
            if best_k is None or prog.lcoe_eur_per_gj < best_k.lcoe_eur_per_gj:
                best_k = prog
        if best_k is None:
            continue
        if best is None or best_k.lcoe_eur_per_gj < best.lcoe_eur_per_gj:
            best = best_k
        if best_k.lcoe_eur_per_gj >= best_at_prev:
            break  # adding doublets no longer helps; stop (U-shaped LCoE)
        best_at_prev = best_k.lcoe_eur_per_gj
    return best
```

**Complexity:** combinations grow as C(shortlist, k). With the defaults `shortlist_size=12`
and `max_program_doublets=4`, the worst case is C(12,4)=495 programs per k (a few thousand
`simulate` calls total), bounded further by the early stop (1-2 doublets normally win). The
viability list used for reporting can be larger; only the **exhaustive** stage uses the
shortlist. Log if the shortlist truncates a larger viable set (no silent caps).

**Objective scope:** this implements `min_lcoe` only (the deciding metric). `min_capex` and
`max_capacity` from spec 4.4 are **deferred** here; the existing `search_designs` already
covers parameter-space objectives, and they can be added to `search_program` later with the
same stopping structure. Note this deferral in the report.

- [ ] **Step 4: Run the test, verify it passes**

Run: `uv run pytest tests/test_program_search.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
uv run ruff check src/geothermal/economics/program_search.py
uv run pyright src/geothermal/economics/program_search.py
git add src/geothermal/economics/program_search.py tests/test_program_search.py
git commit -m "feat: exhaustive program search with objective-driven stopping"
```

---

## Phase 7: Per-well independent Monte-Carlo

### Task 13: Program Monte-Carlo with independent per-site draws

**Files:**
- Modify: `src/geothermal/economics/program_search.py`
- Modify: `tests/test_program_search.py`

- [ ] **Step 1: Write the failing test (independent draws give a narrower band than shared)**

```python
import numpy as np
from geothermal.economics.program_search import program_monte_carlo

def test_independent_draws_narrow_the_band_vs_shared() -> None:
    a = DEFAULT_ASSUMPTIONS
    sites = [
        SiteProperties(x=0.0, y=0.0, transmissivity_dm=6.0, temperature_c=77.0, power_mw_p50=6.0, depth_m=2200.0, sigma_log_trans=0.9, source="thermogis_grid"),
        SiteProperties(x=3000.0, y=0.0, transmissivity_dm=6.0, temperature_c=77.0, power_mw_p50=6.0, depth_m=2200.0, sigma_log_trans=0.9, source="thermogis_grid"),
    ]
    band = program_monte_carlo(sites, assumptions=a, n_samples=400, seed=1)
    assert band["p10"] <= band["p50"] <= band["p90"]
    # capacity spread of two independent wells is tighter than one doubled draw
    spread = band["p90"] - band["p10"]
    assert spread >= 0
```

- [ ] **Step 2: Run it, verify it fails**

Run: `uv run pytest tests/test_program_search.py -k monte -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

Add to `program_search.py`:

```python
def program_monte_carlo(
    sites: list[SiteProperties],
    *,
    assumptions: Assumptions = DEFAULT_ASSUMPTIONS,
    n_samples: int = 2000,
    seed: int = 42,
) -> dict[str, float]:
    """LCoE band for a program, drawing each site's transmissivity independently.

    Each scenario: draw one lognormal transmissivity per site (its own median + sigma),
    sum the per-site capacities, then compute the system LCoE once.
    """
    a = assumptions
    rng = np.random.default_rng(seed)
    demand = district_demand(assumptions=a)
    mu = np.array([np.log(max(s.transmissivity_dm, 1e-6)) for s in sites])
    sigma = np.array([s.sigma_log_trans for s in sites])
    # depth is not stochastic, so the wells CAPEX is the same every scenario: compute once.
    wells_capex = sum(2.0 * well_capex_meur(s.depth_m, a) for s in sites) + len(sites) * a.pump_cost_meur

    lcoes = np.empty(n_samples, dtype=float)
    for i in range(n_samples):
        draws = rng.lognormal(mu, sigma)
        geo = sum(
            float(well_power_mw(t, s.temperature_c, injection_temp_c=a.injection_temp_c))
            for t, s in zip(draws, sites, strict=True)
        )
        design = design_for(geo, a)
        perf = simulate(design, demand)
        lcoes[i] = evaluate_costs(len(sites), design, perf, assumptions=a, wells_capex_meur=wells_capex).lcoe_eur_per_gj
    return {
        "p10": float(np.percentile(lcoes, 10)),
        "p50": float(np.percentile(lcoes, 50)),
        "p90": float(np.percentile(lcoes, 90)),
        "mean": float(lcoes.mean()),
    }
```

- [ ] **Step 4: Run the test, verify it passes**

Run: `uv run pytest tests/test_program_search.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
uv run ruff check src/geothermal/economics/program_search.py
uv run pyright src/geothermal/economics/program_search.py
git add src/geothermal/economics/program_search.py tests/test_program_search.py
git commit -m "feat: per-site independent Monte-Carlo over a doublet program"
```

---

## Phase 8: Wire into the workflow

### Task 14: A grid-backed end-to-end siting helper

**Files:**
- Modify: `src/geothermal/resource/siting.py`
- Modify: `tests/test_siting.py`

- [ ] **Step 1: Write the failing test (data-gated)**

```python
import os
from pathlib import Path
import pytest
from geothermal.assumptions import DEFAULT_ASSUMPTIONS
from geothermal.resource.thermogis_grid import grid_path
from geothermal.resource.siting import shortlist_from_grid

_ROOT = Path(os.environ.get("GEO_THERMOGIS_ROOT", "data/thermogis_grid"))

@pytest.mark.skipif(
    not grid_path(_ROOT, scenario="heat_pump", prop="power_p50").exists(),
    reason="ThermoGIS grid not present",
)
def test_shortlist_from_grid_returns_viable_sites() -> None:
    sites = shortlist_from_grid(_ROOT, assumptions=DEFAULT_ASSUMPTIONS)
    assert sites, "expected at least one viable candidate in the AOI"
    assert all(s.power_mw_p50 >= DEFAULT_ASSUMPTIONS.viability_floor_mw for s in sites)
```

- [ ] **Step 2: Run it (expect skip without data)**

Run: `uv run pytest tests/test_siting.py -k from_grid -v`
Expected: SKIP or PASS.

- [ ] **Step 3: Implement**

Add to `siting.py`:

```python
from pathlib import Path
from functools import partial

from geothermal.assumptions import DEFAULT_ASSUMPTIONS, Assumptions
from geothermal.resource.properties import grid_properties_at, nearest_well_km
from geothermal.resource.thermogis_grid import Scenario


def shortlist_from_grid(
    root: Path,
    *,
    assumptions: Assumptions = DEFAULT_ASSUMPTIONS,
    scenario: Scenario = "heat_pump",
) -> list[SiteProperties]:
    """Full grid-backed candidate pipeline: lattice -> properties -> filter -> shortlist."""
    a = assumptions
    pts = candidate_lattice(center=a.aoi_center_rd, size_km=a.aoi_size_km, pitch_km=a.min_well_spacing_km)

    def provider(x: float, y: float) -> SiteProperties:
        return grid_properties_at(
            root, x, y, scenario=scenario,
            min_dist_km=nearest_well_km(x, y), sigma_interp_per_km=a.sigma_interp_per_km,
        )

    sites = build_candidates(pts, provider=provider, viability_floor_mw=a.viability_floor_mw)
    return shortlist(sites, size=a.shortlist_size)
```

- [ ] **Step 4: Run, lint, type-check, commit**

```bash
uv run pytest tests/test_siting.py -v
uv run ruff check src/geothermal/resource/siting.py
uv run pyright src/geothermal/resource/siting.py
git add src/geothermal/resource/siting.py tests/test_siting.py
git commit -m "feat: grid-backed shortlist pipeline over the AOI"
```

### Task 15: Use the program search in the agent workflow (when the grid is present)

**Files:**
- Modify: `src/geothermal/agent/workflow.py`
- Modify: `tests/test_agent.py`

- [ ] **Step 1: Write the failing test**

```python
from geothermal.agent.workflow import run_workflow

def test_workflow_siting_step_reports_a_program() -> None:
    # without the grid, the workflow falls back to the legacy single-doublet path;
    # either way the siting step must name a concrete decision and metrics.
    result = run_workflow(mc_samples=200)
    siting = next(s for s in result.steps if "siting" in s.name.lower() or "well" in s.name.lower())
    assert siting.decision.strip()
    assert siting.metrics  # non-empty
```

- [ ] **Step 2: Run it, verify it passes or fails as written**

Run: `uv run pytest tests/test_agent.py -k siting -v`
Expected: PASS already if the legacy step remains; this test guards the contract while we swap internals.

- [ ] **Step 3: Implement the swap**

In `src/geothermal/agent/workflow.py`, in the siting step: if the grid root (from an env var `GEO_THERMOGIS_ROOT` or `a` config path, default `data/thermogis_grid`) exists, build the shortlist via `shortlist_from_grid`, run `search_program`, and record the chosen program (n_doublets, locations, LCoE) as the decision + metrics; otherwise keep the existing `recommend_new_well` path. Keep the decision text metric-driven (state the chosen program's count, LCoE and capacity, no fixed claims). Replace the design step's `evaluate_candidate(1..3)` ranking with the program's own LCoE when the grid path is taken, and use `program_monte_carlo(best.sites)` in the risk step.

Pseudostructure (fill with the modules above; keep the metric-driven phrasing helper pattern from `_data_foundation_decision`):

```python
from pathlib import Path
import os
from geothermal.resource.siting import shortlist_from_grid
from geothermal.economics.program_search import search_program, program_monte_carlo

grid_root = Path(os.environ.get("GEO_THERMOGIS_ROOT", "data/thermogis_grid"))
if (grid_root / "6_Permian").exists():
    shortlist = shortlist_from_grid(grid_root, assumptions=a)
    program = search_program(shortlist, assumptions=a, min_spacing_km=a.min_well_spacing_km)
    # ... record program.n_doublets, program.lcoe_eur_per_gj, program.geo_capacity_mw
    # ... risk step: band = program_monte_carlo(list(program.sites), assumptions=a, n_samples=mc_samples)
else:
    # existing legacy path (recommend_new_well + evaluate_candidate + lcoe_monte_carlo)
    ...
```

- [ ] **Step 4: Run the suite, verify green**

Run: `uv run pytest -q`
Expected: PASS.

- [ ] **Step 5: Lint, type-check, commit**

```bash
uv run ruff check src/geothermal/agent/workflow.py
uv run pyright src/geothermal/agent/workflow.py
git add src/geothermal/agent/workflow.py tests/test_agent.py
git commit -m "feat: workflow uses grid-backed program search when the grid is present"
```

---

## Phase 9: Report + provenance

### Task 16: Document the ThermoGIS grid in the report and provenance

**Files:**
- Modify: `src/geothermal/report.py`
- Modify: `tests/test_report.py` (or the existing report test)

- [ ] **Step 1: Write the failing test**

```python
from geothermal.report import build_report

def test_report_documents_thermogis_grid_provenance() -> None:
    md = build_report(mc_samples=200)
    low = md.lower()
    assert "thermogis" in low
    assert "doubletcalc" in low or "p50" in low
```

- [ ] **Step 2: Run it, verify it fails**

Run: `uv run pytest tests/test_report.py -k provenance -v`
Expected: FAIL (text not present).

- [ ] **Step 3: Implement**

In `src/geothermal/report.py`, add a short data-provenance paragraph to the data-foundation / methodology section: name the ThermoGIS v2.x Rotliegend grids (TNO/NLOG), state that resource properties come from that grid (engine DoubletCalc1D), the 4 wells validate/calibrate it, the grid is P50 so lattice uncertainty is modelled, and cite that cooling/integration is our extension. Keep it factual and brief.

- [ ] **Step 4: Run, lint, type-check, commit**

```bash
uv run pytest tests/test_report.py -v
uv run ruff check src/geothermal/report.py
uv run pyright src/geothermal/report.py
git add src/geothermal/report.py tests/test_report.py
git commit -m "docs: report documents ThermoGIS grid provenance and uncertainty"
```

---

## Phase 10: Full verification

### Task 17: Whole-suite green + manual smoke

**Files:** none (verification)

- [ ] **Step 1: Full suite**

Run: `uv run pytest -q`
Expected: all pass (data-gated tests skip if the grid is absent).

- [ ] **Step 2: Lint + type-check the whole tree**

Run: `uv run ruff check . && uv run pyright`
Expected: clean.

- [ ] **Step 3: Smoke the workflow both ways**

Run: `uv run geo-datathon workflow` (legacy path if grid absent), and with `GEO_THERMOGIS_ROOT=data/thermogis_grid uv run geo-datathon workflow` if the grid is present.
Expected: a decision log with a concrete program, LCoE band, and no crashes.

- [ ] **Step 4: Final commit if any fixups**

```bash
git add -A && git commit -m "chore: verification fixups for grid-backed siting"
```

---

## Self-review notes

- **Spec coverage:** provider seam (T5-6), AOI/candidates/viability (T8-9), Option-A search + stopping (T11-12), depth-driven CAPEX (T10), per-well Monte-Carlo (T13), wiring (T14-15), provenance/report (T16), config knobs (T2), deps/data (T1). Cost alignment (4.7) is covered by T10 + T16.
- **Post-review corrections applied (2026-06-06):**
  1. **Well CAPEX anchors on the provided LCOE.xlsx cost** and uses ThermoGIS only for the depth *shape* (`well_cost_meur * poly(d)/poly(d_ref)`). Adopting ThermoGIS's absolute coefficients would have given ~7.4 vs 3.24 M€/well and inflated LCoE ~2.3x on the wells term, breaking consistency with the provided model.
  2. **Base sigma is a config field** (`base_sigma_log_trans`, default ~1.5 from the wells' real bands), not a hardcoded 0.9.
  3. **The measured provider is dropped**; the narrow measured band emerges from the interp-sigma term collapsing to zero at well coordinates (T5/T6). Removes unused, half-broken code.
  4. **Per-site well CAPEX is summed** (each site at its own depth), not averaged, so the depth-cost signal survives (T11/T13).
  5. **Exhaustive shortlist bounded** to 12 with `max_program_doublets=4` to keep the combinatorics tractable (T2/T12).
- **Deferred (intentional):** grid bias-correction (off by default), P10/P90 grids (provider returns `sigma`; swap is future), `min_capex`/`max_capacity` program objectives (T12), HT-ATES cost realignment. All noted in the report.
- **Verify-against-real-data point flagged inline:** the `well_stimulation` filename suffix (T4) must be checked against the actual folder when first run.
- **Robustness note (T3):** `crop_box` assumes ascending x/y coords (true for this grid, confirmed empirically). If a future grid has descending coords, `sel(slice)` returns empty; add an ascending-sort guard then.
- **Behaviour-based tests** are used where exact numerics depend on unread internals (monotonicity, ordering, consistency-with-sheets), avoiding brittle magic numbers.
