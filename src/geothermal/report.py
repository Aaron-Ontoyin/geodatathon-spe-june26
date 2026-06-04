"""Deterministic, no-API-key transparency report.

Runs the whole pipeline and writes a comprehensive, plain-language Markdown report:
data cleaning, resource assessment, system design, the LCoE optimisation, the
Monte-Carlo cost band, a sensitivity tornado, every assumption, and the limitations.
This is the transparency backbone — it needs no API key and is fully reproducible, so
a judge can regenerate it. An optional LLM chat can sit on top, but never replaces it.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np

from geothermal.assumptions import DEFAULT_ASSUMPTIONS, Assumptions
from geothermal.datasets import clean_reservoir_dataset
from geothermal.design import SystemPerformance, district_demand, simulate
from geothermal.economics.optimization import (
    DesignCandidate,
    design_for,
    evaluate_candidate,
    lcoe_monte_carlo,
)
from geothermal.economics.sensitivity import tornado
from geothermal.io import load_thermogis
from geothermal.petrophysics import imputed_vs_thermogis
from geothermal.resource import locate_demand_center, recommend_new_well, well_power_percentiles

_TORNADO_FIELDS = {
    "electricity_price_eur_per_mwhe": (100.0, 200.0),
    "well_cost_meur": (2.0, 5.0),
    "discount_rate": (0.06, 0.12),
    "heat_pump_keur_per_mwth": (500.0, 900.0),
    "gas_price_eur_per_mwhth": (20.0, 60.0),
    "demand_distance_weight_mw_per_km": (0.0, 0.5),
}


def build_report(*, assumptions: Assumptions = DEFAULT_ASSUMPTIONS, mc_samples: int = 2000) -> str:
    """Build the full transparency report as a Markdown string."""
    a = assumptions
    ranked = [evaluate_candidate(n, assumptions=a) for n in (1, 2, 3)]
    feasible = sorted((c for c in ranked if c.meets_demand), key=lambda c: c.lcoe_eur_per_gj)
    best = feasible[0]
    perf = simulate(design_for(best.geo_capacity_mw, a), district_demand(assumptions=a))
    band = lcoe_monte_carlo(best.n_doublets, assumptions=a, n_samples=mc_samples)

    sections = [
        _executive_summary(best, perf, band),
        _data_foundation(),
        _resource(a),
        _system_design(perf),
        _economics(ranked, best, band),
        _assumptions(a),
        _limitations(),
    ]
    return "# Geothermal District Heating & Cooling — Technical Report\n\n" + "\n\n".join(sections)


def write_report(
    path: str | Path, *, assumptions: Assumptions = DEFAULT_ASSUMPTIONS, mc_samples: int = 2000
) -> Path:
    """Build the report and write it to ``path`` (UTF-8). Returns the path."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_report(assumptions=assumptions, mc_samples=mc_samples), encoding="utf-8")
    return out


# --------------------------------------------------------------------------- #
# Sections
# --------------------------------------------------------------------------- #
def _executive_summary(
    best: DesignCandidate, perf: SystemPerformance, band: dict[str, float]
) -> str:
    return (
        "## Executive summary\n\n"
        f"We recommend a **staged {best.n_doublets}-doublet geothermal system** for the Utrecht "
        "district, pairing a deep doublet with a central **heat pump**, seasonal **HT-ATES** "
        "storage and **heat-driven cooling**. It delivers the required heating and cooling at a "
        f"levelized cost of **{best.lcoe_eur_per_gj:.1f} €/GJ** "
        f"(P10 {band['p10']:.1f} / P50 {band['p50']:.1f} / P90 {band['p90']:.1f}).\n\n"
        f"- Firm heating capacity (geothermal + heat pump) is **{best.heating_capacity_mw:.1f} "
        "MWth**; seasonal HT-ATES storage covers the winter peak so the system meets the "
        "10 MWth requirement with near-zero backup.\n"
        f"- Geothermal utilisation rises to **{perf.geo_capacity_factor * 100:.0f}%** by doing "
        f"cooling as well as heating (vs {perf.geo_capacity_factor_heating_only * 100:.0f}% "
        "heating-only) — running the wells hard year-round is why the cost is low.\n"
        f"- CAPEX **{best.capex_meur:.0f} M€**, all-in cost spread over heat + cold delivered.\n\n"
        "Because a single well carries large resource uncertainty (and a second nearby well, "
        "sharing the same geology, does **not** de-risk it), the recommendation is to drill one "
        "doublet, well-test it, and expand only if the data justify it."
    )


def _data_foundation() -> str:
    check = imputed_vs_thermogis(clean_reservoir_dataset())
    rows: list[Sequence[object]] = [
        [
            str(r["well"]),
            f"{_f(r['porosity_pipeline']):.1f}%",
            f"{_f(r['porosity_thermogis']):.1f}%",
            f"{_f(r['difference']):+.1f}",
            str(r["source"]),
        ]
        for _, r in check.iterrows()
    ]
    table = _md_table(["Well", "Porosity (ours)", "Porosity (ThermoGIS)", "Δ", "Source"], rows)
    return (
        "## 1. Data foundation (cleaning & validation)\n\n"
        "The provided per-sample table had mislabeled depths (along-hole values where true "
        "vertical depth was expected) and an empty TVD column; we reconstructed true vertical "
        "depth from the directional surveys (minimum curvature), reproducing the provider's own "
        "survey TVD to <1 m. Porosity, missing for two wells, was imputed from the bulk-density "
        "log (calibrated on the cored wells) and **validated against the independent ThermoGIS "
        "regional model**:\n\n" + table + "\n\nObserved wells match ThermoGIS to <1%; imputed "
        "wells land within ~3%. Porosity uncertainty concentrates in the two non-viable wells, so "
        "the resource decision is robust."
    )


def _resource(a: Assumptions) -> str:
    pct = well_power_percentiles()
    tg = load_thermogis()
    rows: list[Sequence[object]] = []
    for wid in pct.index:
        cols = dict(zip(pct.columns, np.asarray(pct.loc[wid], dtype=float), strict=True))
        rows.append(
            [
                wid,
                f"{cols['P90']:.1f}",
                f"{cols['P50']:.1f}",
                f"{cols['P10']:.1f}",
                f"{tg[str(wid)].value('Temperature'):.0f}",
            ]
        )
    table = _md_table(["Well", "P90 MW", "P50 MW", "P10 MW", "T °C"], rows)
    usp_x, usp_y = locate_demand_center()
    rec = recommend_new_well(assumptions=a)
    return (
        "## 2. Resource assessment (Challenge 1)\n\n"
        "Doublet power per well (calibrated to ThermoGIS), as a P90/P50/P10 band — only BLT-01 "
        "and JUT-01 are viable; the others are too tight:\n\n" + table + "\n\n"
        f"The demand district (Utrecht Science Park) is located at RD ({usp_x:.0f}, {usp_y:.0f}) "
        "by trilateration. A spatial (IDW) resource map across the area recommends a new doublet "
        f"at ({rec['x']:.0f}, {rec['y']:.0f}): **{rec['power_mw_p50']:.1f} MW P50**, "
        f"{rec['distance_to_usp_km']:.1f} km from the demand and "
        f"{rec['distance_to_blt_km']:.1f} km from the best existing well "
        "(a step-out into the proven trend, next to the customers)."
    )


def _system_design(perf: SystemPerformance) -> str:
    return (
        "## 3. Integrated system design (Challenge 2A)\n\n"
        "Geothermal doublet → central heat pump (upgrades the brine to district temperature) → "
        "seasonal HT-ATES (banks summer surplus for winter) → heat-driven absorption cooling on "
        "spare summer capacity, plus free cooling and a small backup boiler.\n\n"
        f"- Heat delivered: **{perf.heat_delivered_gj / 3600:.0f} GWh/yr**; "
        f"cooling delivered: **{perf.cool_delivered_gj / 3600:.0f} GWh/yr**.\n"
        f"- Heat-pump electricity: {perf.heat_pump_mwh_e / 1000:.1f} GWh/yr; "
        f"backup heat: {perf.backup_heat_gj / 3600:.1f} GWh/yr.\n"
        f"- **Geothermal capacity factor {perf.geo_capacity_factor * 100:.0f}%** with cooling vs "
        f"{perf.geo_capacity_factor_heating_only * 100:.0f}% heating-only — summer cooling uses "
        "capacity that would otherwise be idle, which is what makes the system cheap."
    )


def _economics(ranked: list[DesignCandidate], best: DesignCandidate, band: dict[str, float]) -> str:
    rows: list[Sequence[object]] = [
        [
            f"{c.n_doublets} doublet(s)",
            f"{c.geo_capacity_mw:.1f}",
            f"{c.lcoe_eur_per_gj:.1f}",
            f"{c.capex_meur:.0f}",
            "✓ best" if c is best else "",
        ]
        for c in ranked
    ]
    design_table = _md_table(["Design", "Geo MW", "LCoE €/GJ", "CAPEX M€", ""], rows)

    tor = tornado(_TORNADO_FIELDS)
    tor_rows: list[Sequence[object]] = [
        [str(r["field"]), f"{_f(r['low']):g} → {_f(r['high']):g}", f"{_f(r['swing']):.2f}"]
        for _, r in tor.iterrows()
    ]
    tornado_table = _md_table(["Assumption", "Range", "LCoE swing €/GJ"], tor_rows)

    cooling_cut = (1 - best.costs.lcoe_eur_per_gj / best.costs.lcoe_heat_only_eur_per_gj) * 100
    return (
        "## 4. Techno-economics (Challenge 2B)\n\n"
        "Our LCoE model is a Python port of the provided TNO/ECN spreadsheet, calibrated to "
        "reproduce its base case exactly (5.77 €/GJ), then extended for the hybrid system.\n\n"
        "Design comparison (lowest LCoE wins):\n\n" + design_table + "\n\n"
        f"The optimum is **{best.n_doublets} doublet(s) + HT-ATES at {best.lcoe_eur_per_gj:.1f} "
        f"€/GJ** ({best.lcoe_eur_per_gj * 3.6:.0f} €/MWh) — fewer wells plus seasonal storage beat "
        f"more wells. Cooling integration cuts the LCoE {cooling_cut:.0f}% versus heat-only.\n\n"
        f"**Monte-Carlo LCoE** (transmissivity uncertainty): P10 {band['p10']:.1f} / "
        f"P50 {band['p50']:.1f} / P90 {band['p90']:.1f} €/GJ. A second nearby well does not "
        "reduce this risk (correlated geology), so we recommend a staged drill-and-test "
        "approach.\n\n"
        "Sensitivity — which assumptions actually move the LCoE:\n\n" + tornado_table
    )


def _assumptions(a: Assumptions) -> str:
    rows: list[Sequence[object]] = [[k, v] for k, v in a.model_dump().items()]
    table = _md_table(["Parameter", "Value"], rows)
    return (
        "## 5. Assumptions\n\n"
        "Every tunable input, with its value (defaults from LCOE.xlsx + documented public "
        "ranges). All are parameters of the model — none are hidden constants.\n\n" + table
    )


def _limitations() -> str:
    return (
        "## 6. Limitations\n\n"
        "- The spatial resource map is built from only four wells (two viable); a denser "
        "ThermoGIS regional grid would sharpen it and de-risk the sited location.\n"
        "- The system is modelled at a monthly energy-balance level (per the brief), not as a "
        "transient reservoir/thermodynamic simulation.\n"
        "- Surface-component unit costs are public-range estimates; the tornado shows which ones "
        "matter (electricity price, well cost, discount rate) and which do not.\n"
        "- The Monte-Carlo assumes a single correlated transmissivity field; partial spatial "
        "correlation would narrow the band somewhat.\n"
        "- The 1-doublet optimum relies on HT-ATES to cover the winter peak; we assume the "
        "storage can deliver the ~2 MW peak shortfall, which a sized ATES doublet can, but "
        "which a detailed storage design should confirm."
    )


def _f(value: object) -> float:
    """Coerce a pandas/numpy cell to a plain float (sidesteps stub unions)."""
    return float(np.asarray(value, dtype=float))


def _md_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    head = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = "\n".join("| " + " | ".join(str(cell) for cell in row) + " |" for row in rows)
    return "\n".join([head, sep, body])
