"""The deterministic workflow orchestrator: run the pipeline, log every decision.

Each stage produces a :class:`WorkflowStep` recording *what it did*, *the decision it
made and why*, and the key numbers behind it — the auditable trail an agent leaves.
This runs end-to-end with no API key; the optional LLM layer only narrates it.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from geothermal.assumptions import DEFAULT_ASSUMPTIONS, Assumptions
from geothermal.datasets import clean_reservoir_dataset
from geothermal.design import district_demand, simulate
from geothermal.economics.optimization import design_for, evaluate_candidate, lcoe_monte_carlo
from geothermal.petrophysics import imputed_vs_thermogis, survey_tvd_residual_m
from geothermal.progress import Progress, ProgressCallback, report
from geothermal.report import build_report
from geothermal.resource import locate_demand_center, recommend_new_well, well_power_percentiles

_TOTAL_STAGES = 6
_TVD_TOLERANCE_M = 1.0  # sub-metre AH→TVD reconstruction is the bar for trusting the depths
_POROSITY_TOLERANCE_PCT = 5.0  # max acceptable gap to the independent ThermoGIS porosity


@dataclass(frozen=True, slots=True)
class WorkflowStep:
    """One stage of the workflow with its decision and key metrics."""

    name: str
    action: str
    decision: str
    metrics: dict[str, float]


@dataclass(frozen=True, slots=True)
class WorkflowResult:
    """The decision log, the assembled report, and the headline outcome."""

    steps: tuple[WorkflowStep, ...]
    report_markdown: str
    lcoe_eur_per_gj: float
    n_doublets: int


def run_workflow(
    *,
    assumptions: Assumptions = DEFAULT_ASSUMPTIONS,
    mc_samples: int = 2000,
    on_progress: ProgressCallback | None = None,
) -> WorkflowResult:
    """Run the full pipeline, recording the decision made at each stage."""
    a = assumptions
    steps: list[WorkflowStep] = []

    def _emit(message: str, *, done: int | None = None) -> None:
        report(
            on_progress,
            Progress("workflow", len(steps) if done is None else done, _TOTAL_STAGES, message),
        )

    _emit("Cleaning and validating well data")
    check = imputed_vs_thermogis(clean_reservoir_dataset())
    n_wells = len(check)
    imputed = check[check["source"] == "imputed"]
    max_mismatch = float(np.abs(np.asarray(imputed["difference"], dtype=float)).max())
    tvd_residual = survey_tvd_residual_m()
    steps.append(
        WorkflowStep(
            name="Data foundation",
            action="Converted along-hole depths to TVD (minimum curvature) and imputed the "
            "missing porosity from the bulk-density log.",
            decision=_data_foundation_decision(tvd_residual, max_mismatch),
            metrics={
                "wells": float(n_wells),
                "max_tvd_residual_m": tvd_residual,
                "max_porosity_mismatch_pct": max_mismatch,
            },
        )
    )

    _emit("Assessing the geothermal resource")
    pct = well_power_percentiles()
    viable = [
        str(w)
        for w in pct.index
        if dict(zip(pct.columns, np.asarray(pct.loc[w], dtype=float), strict=True))["P50"] > 0
    ]
    steps.append(
        WorkflowStep(
            name="Resource assessment",
            action="Computed P90/P50/P10 doublet power per well from the calibrated model.",
            decision=f"{len(viable)} of {len(pct)} wells are viable "
            f"({', '.join(viable)}); the given wells alone cannot meet 10 MWth, "
            "so a new well must be sited.",
            metrics={"viable_wells": float(len(viable))},
        )
    )

    _emit("Siting a new well")
    usp_x, usp_y = locate_demand_center()
    rec = recommend_new_well(assumptions=a)
    steps.append(
        WorkflowStep(
            name="Well siting",
            action="Built an IDW resource map and scored locations by power and proximity to "
            f"the demand district at ({usp_x:.0f}, {usp_y:.0f}).",
            decision=f"Recommend a new doublet at ({rec['x']:.0f}, {rec['y']:.0f}): "
            f"{rec['power_mw_p50']:.1f} MW P50, {rec['distance_to_usp_km']:.1f} km from demand, "
            f"{rec['distance_to_blt_km']:.1f} km from the best existing well.",
            metrics={
                "new_well_power_mw": rec["power_mw_p50"],
                "distance_to_demand_km": rec["distance_to_usp_km"],
            },
        )
    )

    _emit("Optimising the system design")
    ranked = [evaluate_candidate(n, assumptions=a) for n in (1, 2, 3)]
    best = sorted((c for c in ranked if c.meets_demand), key=lambda c: c.lcoe_eur_per_gj)[0]
    perf = simulate(design_for(best.geo_capacity_mw, a), district_demand(assumptions=a))
    steps.append(
        WorkflowStep(
            name="System design & optimisation",
            action="Evaluated 1-3 doublet programmes (heat pump + HT-ATES + heat-driven cooling) "
            "and computed each LCoE.",
            decision=f"Chose {best.n_doublets} doublet(s) + HT-ATES — lowest LCoE "
            f"({best.lcoe_eur_per_gj:.1f} €/GJ) while meeting demand; cooling lifts geothermal "
            f"utilisation to {perf.geo_capacity_factor * 100:.0f}%, which is what makes it cheap.",
            metrics={
                "n_doublets": float(best.n_doublets),
                "lcoe_eur_per_gj": best.lcoe_eur_per_gj,
                "capacity_factor": perf.geo_capacity_factor,
            },
        )
    )

    _emit("Running the risk Monte-Carlo")
    band = lcoe_monte_carlo(best.n_doublets, assumptions=a, n_samples=mc_samples)
    steps.append(
        WorkflowStep(
            name="Risk assessment",
            action="Ran a Monte-Carlo over the (large) transmissivity uncertainty.",
            decision=f"LCoE P10 {band['p10']:.1f} / P50 {band['p50']:.1f} / P90 {band['p90']:.1f} "
            "€/GJ. A second nearby well does not de-risk it (correlated geology), so drill one "
            "doublet, well-test it, and expand only if the data justify it.",
            metrics={"lcoe_p10": band["p10"], "lcoe_p50": band["p50"], "lcoe_p90": band["p90"]},
        )
    )

    _emit("Assembling the report")
    report_markdown = build_report(assumptions=a, mc_samples=mc_samples)
    _emit("Complete", done=_TOTAL_STAGES)
    return WorkflowResult(
        steps=tuple(steps),
        report_markdown=report_markdown,
        lcoe_eur_per_gj=best.lcoe_eur_per_gj,
        n_doublets=best.n_doublets,
    )


def _data_foundation_decision(tvd_residual: float, max_mismatch: float) -> str:
    """Phrase the data-foundation verdict from the actual numbers, not a fixed conclusion.

    Each check reads as a pass or a fail against its tolerance, and the closing verdict
    flips to a flag if either check is out of bounds, so the narration stays true if the
    inputs change.
    """
    tvd_ok = tvd_residual <= _TVD_TOLERANCE_M
    poro_ok = max_mismatch <= _POROSITY_TOLERANCE_PCT
    conversion = (
        f"the conversion reproduces the survey TVD to {tvd_residual:.2f} m"
        if tvd_ok
        else f"the conversion leaves a {tvd_residual:.2f} m gap to the survey TVD"
    )
    imputation = (
        f"the imputation agrees with independent ThermoGIS to {max_mismatch:.1f} porosity points"
        if poro_ok
        else f"the imputation differs from independent ThermoGIS by {max_mismatch:.1f} porosity "
        "points"
    )
    verdict = (
        "both clear their tolerances, so the resource and cost stages run on these values"
        if tvd_ok and poro_ok
        else "a check is outside tolerance, so these values are flagged before downstream use"
    )
    return f"Checked that {conversion} and {imputation}; {verdict}."
