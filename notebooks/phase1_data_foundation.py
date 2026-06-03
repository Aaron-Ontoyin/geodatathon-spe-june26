"""Phase 1 — Data foundation: depth reconciliation + property imputation.

Runnable analysis script (jupytext `# %%` cells). Documents how we turn the raw,
flagged data into a clean, TVD-correct, gap-filled reservoir dataset, and emits the
QC figures used in the report/deck.

Run:  uv run python notebooks/phase1_data_foundation.py
"""

# %% Imports & setup
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from geothermal import config
from geothermal.datasets import clean_reservoir_dataset
from geothermal.io import load_target_lithologies, load_thermogis
from geothermal.petrophysics import (
    density_porosity,
    imputed_vs_thermogis,
    porosity_cross_well_skill,
    porosity_log_quality,
)

FIG_DIR = config.OUTPUTS_DIR / "figures" / "phase1"
FIG_DIR.mkdir(parents=True, exist_ok=True)

raw = load_target_lithologies()
clean = clean_reservoir_dataset(refresh=True)
thermogis = load_thermogis()

# %% Section 1 — the depth trap, resolved
print("=" * 78)
print("SECTION 1 — DEPTH RECONCILIATION (along-hole → TVD)")
print("=" * 78)
print(f"raw depth_tvd_m missing : {raw['depth_tvd_m'].isna().mean():.0%} (all rows flagged 'check')")
print(f"clean depth_tvd_m filled: {clean['depth_tvd_m'].notna().mean():.0%}")
for wid, g in clean.groupby("well_id"):
    ah = g["formation_thickness_ah_m"].iloc[0]
    tvd = g["formation_thickness_tvd_m"].iloc[0]
    print(f"  {wid}: reservoir AH {ah:6.1f} m → TVD {tvd:6.1f} m  ({100 * (1 - tvd / ah):4.1f}% thinner)")

# %% Section 2 — row orientation inferred from the GR signature
print("\n" + "=" * 78)
print("SECTION 2 — ROW ORIENTATION (inferred from gamma-ray cross-correlation)")
print("=" * 78)
for wid, g in clean.groupby("well_id"):
    orient = g["row_orientation"].iloc[0]
    conf = g["orientation_confidence"].iloc[0]
    print(f"  {wid}: {orient:8s} (confidence {conf:.2f})")

# %% Section 3 — porosity imputation: physics + cross-well validation
print("\n" + "=" * 78)
print("SECTION 3 — POROSITY IMPUTATION (density porosity, calibrated)")
print("=" * 78)
print("Per-well density-porosity vs measured (where measured exists):")
for well, m in porosity_log_quality().items():
    print(f"  {well}: corr={m['corr']:.2f}  R²(raw)={m['r2_raw']:+.2f}  (n={int(m['n'])})")
print("\nLeave-one-well-out is pessimistic with only two cored wells of unequal quality:")
for well, m in porosity_cross_well_skill().items():
    print(f"  predict {well}: R²={m['r2']:+.2f}  RMSE={m['rmse']:.2f} %")
print("\nOut-of-sample check vs independent ThermoGIS regional porosity:")
check = imputed_vs_thermogis(clean)
for _, r in check.iterrows():
    print(
        f"  {r['well']}: pipeline {r['porosity_pipeline']:5.1f}%  vs ThermoGIS "
        f"{r['porosity_thermogis']:5.1f}%  (Δ {r['difference']:+.1f}, {r['source']})"
    )

# Crossplot: density porosity vs observed, on the wells that have measured porosity.
obs = clean[clean["porosity_source"] == "observed"]
phi_d = density_porosity(np.asarray(obs["log_rhob"], dtype=float)) * 100.0
fig, ax = plt.subplots(figsize=(5, 5))
for wid, g in obs.groupby("well_id"):
    pd_g = density_porosity(np.asarray(g["log_rhob"], dtype=float)) * 100.0
    ax.scatter(pd_g, g["porosity_obs"], s=6, alpha=0.4, label=str(wid))
lims = [0, 30]
ax.plot(lims, lims, "k--", lw=1, label="1:1")
ax.set_xlabel("Density porosity (%)")
ax.set_ylabel("Observed porosity (%)")
ax.set_title("Porosity imputation calibration")
ax.legend()
ax.set_xlim(lims)
ax.set_ylim(lims)
fig.tight_layout()
fig.savefig(FIG_DIR / "porosity_calibration.png", dpi=130)

# %% Section 4 — poro-perm trend
print("\n" + "=" * 78)
print("SECTION 4 — PORO-PERM TREND + RESERVOIR SUMMARY")
print("=" * 78)
header = f"{'well':8s}{'TVD top':>9s}{'net TVD':>9s}{'poro%':>7s}{'perm mD':>9s}{'T°C':>6s}{'P50 MW':>8s}"
print(header)
for wid, g in clean.groupby("well_id"):
    print(
        f"{wid:8s}{g['formation_top_tvd_m'].iloc[0]:9.0f}{g['formation_thickness_tvd_m'].iloc[0]:9.0f}"
        f"{g['porosity_final'].mean():7.1f}{g['permeability_md'].mean():9.1f}"
        f"{thermogis[wid].value('Temperature'):6.0f}{thermogis[wid].value('Power'):8.1f}"
    )

# Porosity-depth profiles per well (observed vs imputed).
fig, axes = plt.subplots(1, 4, figsize=(12, 5), sharey=False)
for ax, wid in zip(axes, config.WELL_IDS, strict=True):
    g = clean[clean["well_id"] == wid].sort_values("depth_tvd_m")
    color = "tab:blue" if g["porosity_source"].iloc[0] == "observed" else "tab:orange"
    ax.plot(g["porosity_final"], g["depth_tvd_m"], color=color, lw=0.6)
    ax.invert_yaxis()
    ax.set_title(f"{wid}\n({g['porosity_source'].iloc[0]})")
    ax.set_xlabel("porosity %")
    ax.set_xlim(0, 30)
axes[0].set_ylabel("TVD (m)")
fig.suptitle("Rotliegend porosity vs depth (blue=measured, orange=imputed)")
fig.tight_layout()
fig.savefig(FIG_DIR / "porosity_profiles.png", dpi=130)

print(f"\nFigures written to {FIG_DIR}")
print(f"Clean dataset cached to {config.OUTPUTS_DIR / 'clean_reservoir.parquet'}")
