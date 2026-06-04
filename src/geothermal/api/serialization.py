"""Turn domain objects into JSON-friendly dashboard payloads for the API."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

from geothermal import config
from geothermal.assumptions import Assumptions
from geothermal.design import SystemPerformance, district_demand, simulate
from geothermal.economics.optimization import (
    DesignCandidate,
    design_for,
    evaluate_candidate,
    lcoe_monte_carlo,
    monte_carlo_lcoe_samples,
)
from geothermal.economics.search import SearchResult, search_designs
from geothermal.economics.sensitivity import tornado
from geothermal.inputs import InputSpec
from geothermal.resource import (
    locate_demand_center,
    recommend_new_well,
    resource_grid,
    well_power_percentiles,
)

API_MC_SAMPLES = 1500
TORNADO_FIELDS = {
    "electricity_price_eur_per_mwhe": (100.0, 200.0),
    "well_cost_meur": (2.0, 5.0),
    "discount_rate": (0.06, 0.12),
    "heat_pump_keur_per_mwth": (500.0, 900.0),
    "gas_price_eur_per_mwhth": (20.0, 60.0),
}


def resolve(spec: InputSpec) -> tuple[Assumptions, SearchResult | None]:
    """Resolve the assumptions to analyse; if a search was requested, use the winner."""
    if not spec.search.ranges:
        return spec.assumptions, None
    result = search_designs(
        base=spec.assumptions,
        ranges=spec.search.ranges,
        constraints=spec.search.constraints,
        objective=spec.search.objective,
    )
    best = result.best.assumptions if result.best is not None else spec.assumptions
    return best, result


def candidate_dict(candidate: DesignCandidate) -> dict[str, object]:
    return {
        "n_doublets": candidate.n_doublets,
        "geo_capacity_mw": candidate.geo_capacity_mw,
        "heating_capacity_mw": candidate.heating_capacity_mw,
        "lcoe_eur_per_gj": candidate.lcoe_eur_per_gj,
        "lcoe_heat_only_eur_per_gj": candidate.costs.lcoe_heat_only_eur_per_gj,
        "capex_meur": candidate.capex_meur,
        "backup_fraction": candidate.backup_fraction,
        "meets_demand": candidate.meets_demand,
        "capex_breakdown": candidate.costs.capex_breakdown,
    }


def search_dict(result: SearchResult) -> dict[str, object]:
    return {
        "best": candidate_dict(result.best) if result.best else None,
        "feasible": [candidate_dict(c) for c in result.feasible],
        "n_evaluated": result.n_evaluated,
        "objective": result.objective,
    }


def dashboard(assumptions: Assumptions) -> dict[str, object]:
    """The full dashboard payload (numbers + chart data) for one set of assumptions."""
    a = assumptions
    candidates = [evaluate_candidate(n, assumptions=a) for n in (1, 2, 3)]
    feasible = sorted((c for c in candidates if c.meets_demand), key=lambda c: c.lcoe_eur_per_gj)
    best = feasible[0] if feasible else min(candidates, key=lambda c: c.lcoe_eur_per_gj)

    perf = simulate(design_for(best.geo_capacity_mw, a), district_demand(assumptions=a))
    band = lcoe_monte_carlo(best.n_doublets, assumptions=a, n_samples=API_MC_SAMPLES)
    samples = monte_carlo_lcoe_samples(best.n_doublets, assumptions=a, n_samples=API_MC_SAMPLES)
    counts, edges = np.histogram(samples, bins=40)

    return {
        "assumptions": a.model_dump(),
        "best": candidate_dict(best),
        "comparison": [candidate_dict(c) for c in candidates],
        "headline": {
            "lcoe_p10": band["p10"],
            "lcoe_p50": band["p50"],
            "lcoe_p90": band["p90"],
            "n_doublets": best.n_doublets,
            "heating_capacity_mw": best.heating_capacity_mw,
            "capex_meur": best.capex_meur,
            "capacity_factor": perf.geo_capacity_factor,
        },
        "design": _design_dict(perf),
        "resource_map": _resource_map(a),
        "percentiles": _percentiles(),
        "monte_carlo": {**band, "hist_counts": counts.tolist(), "hist_edges": edges.tolist()},
        "tornado": _tornado_rows(a),
    }


def _design_dict(perf: SystemPerformance) -> dict[str, object]:
    m = perf.monthly
    return {
        "months": _floats(m["month"]),
        "heating_mw": _floats(m["heating_mw"]),
        "cooling_mw": _floats(m["cooling_mw"]),
        "geo_heat_mw": _floats(m["geo_heat_mw"]),
        "abs_cool_mw": _floats(m["abs_cool_mw"]),
        "backup_mw": _floats(m["backup_mw"]),
        "capacity_factor": perf.geo_capacity_factor,
        "capacity_factor_heating_only": perf.geo_capacity_factor_heating_only,
        "heat_gwh": perf.heat_delivered_gj / 3600.0,
        "cool_gwh": perf.cool_delivered_gj / 3600.0,
    }


def _resource_map(a: Assumptions) -> dict[str, object]:
    grid = resource_grid(50)
    usp_x, usp_y = locate_demand_center()
    pct = well_power_percentiles()
    wells = [
        {
            "id": wid,
            "x": config.WELLS[wid].x,
            "y": config.WELLS[wid].y,
            "p50": float(np.asarray(pct.loc[wid], dtype=float)[1]),
        }
        for wid in config.WELL_IDS
    ]
    return {
        "x": grid.x[0].tolist(),
        "y": grid.y[:, 0].tolist(),
        "power": grid.power_mw.tolist(),
        "wells": wells,
        "demand": {"x": usp_x, "y": usp_y},
        "recommended": recommend_new_well(assumptions=a),
    }


def _percentiles() -> list[dict[str, object]]:
    pct = well_power_percentiles()
    rows: list[dict[str, object]] = []
    for wid in pct.index:
        cols = dict(zip(pct.columns, np.asarray(pct.loc[wid], dtype=float), strict=True))
        rows.append({"well": str(wid), "p90": cols["P90"], "p50": cols["P50"], "p10": cols["P10"]})
    return rows


def _tornado_rows(a: Assumptions) -> list[dict[str, object]]:
    table = tornado(TORNADO_FIELDS, base=a)
    return [
        {
            "field": str(r["field"]),
            "low": _scalar(r["lcoe_low"]),
            "high": _scalar(r["lcoe_high"]),
            "swing": _scalar(r["swing"]),
        }
        for _, r in table.iterrows()
    ]


def _floats(values: npt.ArrayLike) -> list[float]:
    return [float(v) for v in np.asarray(values, dtype=float)]


def _scalar(value: object) -> float:
    return float(np.asarray(value, dtype=float))
