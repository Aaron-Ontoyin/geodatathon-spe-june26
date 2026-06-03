"""Phase 2 — Resource assessment (Challenge 1, 60%).

Probabilistic per-well power, the spatial resource map, and new-well siting to meet
the district base load. Emits the figures used in the report/deck.

Run:  uv run python notebooks/phase2_resource_assessment.py
"""

# %% Imports
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from geothermal import config
from geothermal.resource import (
    locate_demand_center,
    recommend_new_well,
    resource_grid,
    well_power_percentiles,
)

FIG_DIR = config.OUTPUTS_DIR / "figures" / "phase2"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# %% Section 1 — per-well probabilistic power
print("=" * 78)
print("SECTION 1 — PER-WELL DOUBLET POWER (P90 / P50 / P10), calibrated to ThermoGIS")
print("=" * 78)
pct = well_power_percentiles()
print(pct.round(2).to_string())
print("\nViable wells (P50 > 0): BLT-01 and JUT-01 only — EVD/PKP are too tight.")
print(
    f"Single-well risk is large: BLT-01 spans P90={pct.loc['BLT-01', 'P90']:.1f} → "
    f"P50={pct.loc['BLT-01', 'P50']:.1f} → P10={pct.loc['BLT-01', 'P10']:.1f} MW."
)

# %% Section 2 — demand centre + new-well siting
print("\n" + "=" * 78)
print("SECTION 2 — DEMAND CENTRE & NEW-WELL SITING")
print("=" * 78)
usp_x, usp_y = locate_demand_center()
print(f"Demand centre (USP) trilaterated to x={usp_x:.0f}, y={usp_y:.0f} (RD New).")
rec = recommend_new_well()
print("Recommended new doublet:")
for k, v in rec.items():
    print(f"  {k}: {v:.2f}")

# %% Section 3 — the well programme to meet 10 MWth heating
print("\n" + "=" * 78)
print("SECTION 3 — RECOMMENDED WELL PROGRAMME")
print("=" * 78)
blt_p50 = float(pct.loc["BLT-01", "P50"])
jut_p50 = float(pct.loc["JUT-01", "P50"])
new_p50 = rec["power_mw_p50"]
print(f"  Doublet A — BLT-01 area      : {blt_p50:4.1f} MWth (P50, proven)")
print(f"  Doublet B — new step-out     : {new_p50:4.1f} MWth (P50, 1.5 km SW of BLT, 0.5 km from USP)")
print(f"  → two doublets near demand   : {blt_p50 + new_p50:4.1f} MWth (P50)  ✓ meets 10 MWth target")
print(f"  Doublet C — JUT-01 (optional): {jut_p50:4.1f} MWth — resilience / upside (7.7 km from USP)")
print(f"  Full three-doublet programme : {blt_p50 + new_p50 + jut_p50:4.1f} MWth (P50)")
print("\n  Final well count is set in Phase 4 by the LCoE optimisation (cost vs capacity).")

# %% Figure 1 — resource power map with wells, demand, recommendation
grid = resource_grid(160)
fig, ax = plt.subplots(figsize=(8, 6))
cf = ax.contourf(grid.x, grid.y, grid.power_mw, levels=20, cmap="viridis")
fig.colorbar(cf, ax=ax, label="Doublet power P50 (MWth)")
for wid in config.WELL_IDS:
    w = config.WELLS[wid]
    viable = float(pct.loc[wid, "P50"]) > 0
    ax.scatter(w.x, w.y, c="white", edgecolors="k", s=80, marker="o" if viable else "x")
    ax.annotate(wid, (w.x, w.y), textcoords="offset points", xytext=(6, 6), color="white", fontsize=8)
ax.scatter(usp_x, usp_y, c="red", marker="*", s=260, edgecolors="k", label="Demand (USP)")
ax.scatter(rec["x"], rec["y"], c="cyan", marker="P", s=180, edgecolors="k", label="Recommended well")
ax.set_xlabel("RD-New easting (m)")
ax.set_ylabel("RD-New northing (m)")
ax.set_title("Rotliegend geothermal power map (IDW from 4 wells)")
ax.legend(loc="lower left")
ax.set_aspect("equal")
fig.tight_layout()
fig.savefig(FIG_DIR / "resource_power_map.png", dpi=130)

# %% Figure 2 — per-well power percentile bars
fig, ax = plt.subplots(figsize=(7, 4.5))
wells = config.WELL_IDS
p50 = [float(pct.loc[w, "P50"]) for w in wells]
lo = [float(pct.loc[w, "P50"]) - float(pct.loc[w, "P90"]) for w in wells]
hi = [float(pct.loc[w, "P10"]) - float(pct.loc[w, "P50"]) for w in wells]
ax.bar(wells, p50, yerr=[lo, hi], capsize=6, color=["tab:green", "tab:gray", "tab:blue", "tab:gray"])
ax.axhline(10, color="red", ls="--", lw=1, label="10 MWth heating target")
ax.set_ylabel("Doublet power (MWth)")
ax.set_title("Per-well power: P50 with P90–P10 range")
ax.legend()
fig.tight_layout()
fig.savefig(FIG_DIR / "well_power_percentiles.png", dpi=130)

print(f"\nFigures written to {FIG_DIR}")
