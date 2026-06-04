"""Phase 3 — Integrated heating + cooling system design (Challenge 2A).

The signature design: geothermal doublets + central heat pump + seasonal HT-ATES +
heat-driven (absorption) cooling. Quantifies the thesis that summer cooling lifts
geothermal utilisation. Emits the dispatch and capacity-factor figures.

Run:  uv run python notebooks/phase3_system_design.py
"""

# %% Imports
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from geothermal import config
from geothermal.design import SystemDesign, district_demand, simulate

FIG_DIR = config.OUTPUTS_DIR / "figures" / "phase3"
FIG_DIR.mkdir(parents=True, exist_ok=True)

demand = district_demand()
design = SystemDesign()  # 2-doublet programme: 10 MW geothermal + heat pump
perf = simulate(design, demand)
m = perf.monthly

# %% Section 1 — capacities and annual energy
print("=" * 78)
print("SECTION 1 — INTEGRATED SYSTEM (2 doublets, 10 MW geothermal + heat pump)")
print("=" * 78)
print(f"  heating capacity (geo + heat pump): {perf.heating_capacity_mw:.1f} MWth  (target 10)")
print("  cooling: absorption chiller on spare summer geothermal + free cooling + backup")
print(f"  heat delivered : {perf.heat_delivered_gj / 3600:5.0f} GWh/yr")
print(f"  cool delivered : {perf.cool_delivered_gj / 3600:5.0f} GWh/yr "
      f"({perf.absorption_cool_gj / perf.cool_delivered_gj * 100:.0f}% from heat-driven absorption)")
print(f"  heat-pump power: {perf.heat_pump_mwh_e / 1000:5.1f} GWh_e/yr")
print(f"  backup heat    : {perf.backup_heat_gj / 3600:5.1f} GWh/yr")

# %% Section 2 — the capacity-factor thesis
print("\n" + "=" * 78)
print("SECTION 2 — WHY HEATING + COOLING TOGETHER IS CHEAPER")
print("=" * 78)
cf_h = perf.geo_capacity_factor_heating_only
cf_b = perf.geo_capacity_factor
print(f"  geothermal capacity factor, heating only      : {cf_h * 100:.0f}%")
print(f"  geothermal capacity factor, heating + cooling : {cf_b * 100:.0f}%")
print(f"  → {(cf_b / cf_h - 1) * 100:.0f}% more useful output from the SAME wells,")
print("    so the fixed well cost is spread over more delivered energy → lower LCoE.")

# %% Figure 1 — monthly dispatch (heating + cooling)
months = np.arange(1, 13)
fig, (axh, axc) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)

geohp = m["geo_heat_mw"].to_numpy() + m["hp_elec_mw"].to_numpy()  # delivered by geo+HP
axh.bar(months, geohp, label="geothermal + heat pump", color="tab:red")
axh.bar(months, m["ates_discharge_mw"], bottom=geohp, label="HT-ATES discharge", color="tab:orange")
axh.bar(months, m["backup_mw"], bottom=geohp + m["ates_discharge_mw"].to_numpy(),
        label="backup", color="tab:gray")
axh.plot(months, m["heating_mw"], "k--o", ms=4, label="heating demand")
axh.set_ylabel("Heating (MWth)")
axh.set_title("Monthly heating dispatch")
axh.legend(fontsize=8, ncol=2)

axc.bar(months, m["abs_cool_mw"], label="absorption (geothermal-driven)", color="tab:blue")
axc.bar(months, m["free_cool_mw"], bottom=m["abs_cool_mw"], label="free cooling (ATES)", color="tab:cyan")
axc.bar(months, m["comp_cool_mw"], bottom=m["abs_cool_mw"].to_numpy() + m["free_cool_mw"].to_numpy(),
        label="compression chiller", color="tab:gray")
axc.plot(months, m["cooling_mw"], "k--o", ms=4, label="cooling demand")
axc.set_ylabel("Cooling (MWth)")
axc.set_xlabel("Month")
axc.set_title("Monthly cooling dispatch")
axc.legend(fontsize=8, ncol=2)
fig.tight_layout()
fig.savefig(FIG_DIR / "monthly_dispatch.png", dpi=130)

# %% Figure 2 — capacity-factor uplift
fig, ax = plt.subplots(figsize=(5, 4))
ax.bar(["heating\nonly", "heating +\ncooling"], [cf_h * 100, cf_b * 100],
       color=["tab:gray", "tab:green"])
ax.set_ylabel("Geothermal capacity factor (%)")
ax.set_title("Cooling monetises idle geothermal capacity")
for i, v in enumerate([cf_h * 100, cf_b * 100]):
    ax.text(i, v + 1, f"{v:.0f}%", ha="center")
fig.tight_layout()
fig.savefig(FIG_DIR / "capacity_factor_uplift.png", dpi=130)

print(f"\nFigures written to {FIG_DIR}")
