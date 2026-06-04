"""FastAPI backend for the demo app.

Thin endpoints over the pipeline that reuse the Pydantic input models directly (so
validation and OpenAPI docs come for free). Long operations stream progress over SSE;
the chat streams tokens. The deterministic core stays synchronous — the streaming
endpoints run it in a worker thread and forward its progress callback to the client.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable

import numpy as np
import numpy.typing as npt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from geothermal import config
from geothermal.agent.llm import astream_chat
from geothermal.agent.workflow import WorkflowResult, run_workflow
from geothermal.assumptions import DEFAULT_ASSUMPTIONS, Assumptions
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
from geothermal.progress import Progress
from geothermal.report import build_report
from geothermal.resource import (
    locate_demand_center,
    recommend_new_well,
    resource_grid,
    well_power_percentiles,
)

_API_MC_SAMPLES = 1500
_TORNADO_FIELDS = {
    "electricity_price_eur_per_mwhe": (100.0, 200.0),
    "well_cost_meur": (2.0, 5.0),
    "discount_rate": (0.06, 0.12),
    "heat_pump_keur_per_mwth": (500.0, 900.0),
    "gas_price_eur_per_mwhth": (20.0, 60.0),
}

app = FastAPI(title="Geothermal Datathon API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """A grounded chat turn: the question, prior turns, and the report to ground on."""

    question: str
    history: list[tuple[str, str]] = Field(default_factory=list)
    context: str = Field("", description="The report markdown to ground answers in.")
    api_key: str | None = None


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/config")
def get_config() -> dict[str, object]:
    """Field metadata (defaults + descriptions) so the UI can build the form."""
    fields = [
        {"name": name, "default": info.default, "description": info.description}
        for name, info in Assumptions.model_fields.items()
    ]
    return {"defaults": DEFAULT_ASSUMPTIONS.model_dump(), "fields": fields}


@app.post("/analyze")
def analyze(spec: InputSpec) -> dict[str, object]:
    """Full dashboard payload (numbers + chart data) for the resolved design."""
    assumptions, _ = _resolve(spec)
    return _dashboard(assumptions)


@app.post("/report")
def report(spec: InputSpec) -> dict[str, str]:
    """The full transparent report as Markdown (served lazily for the Report tab)."""
    assumptions, _ = _resolve(spec)
    return {"markdown": build_report(assumptions=assumptions, mc_samples=_API_MC_SAMPLES)}


@app.post("/optimize/stream")
async def optimize_stream(spec: InputSpec) -> EventSourceResponse:
    """Run the design search, streaming progress then the best + feasible designs."""

    def run(on_progress: Callable[[Progress], None]) -> dict[str, object]:
        result = search_designs(
            base=spec.assumptions,
            ranges=spec.search.ranges,
            constraints=spec.search.constraints,
            objective=spec.search.objective,
            on_progress=on_progress,
        )
        return _search_dict(result)

    return EventSourceResponse(_stream_with_progress(run))


@app.post("/workflow/stream")
async def workflow_stream(spec: InputSpec) -> EventSourceResponse:
    """Run the agentic workflow, streaming stage progress then the decision log."""
    assumptions, _ = _resolve(spec)

    def run(on_progress: Callable[[Progress], None]) -> dict[str, object]:
        result = run_workflow(
            assumptions=assumptions, mc_samples=_API_MC_SAMPLES, on_progress=on_progress
        )
        return _workflow_dict(result)

    return EventSourceResponse(_stream_with_progress(run))


@app.post("/chat")
async def chat_stream(request: ChatRequest) -> EventSourceResponse:
    """Stream a grounded chat answer token-by-token over SSE."""

    async def events() -> AsyncIterator[dict[str, str]]:
        async for token in astream_chat(
            request.question,
            context=request.context,
            history=request.history,
            api_key=request.api_key,
        ):
            yield {"event": "token", "data": token}
        yield {"event": "done", "data": ""}

    return EventSourceResponse(events())


# --------------------------------------------------------------------------- #
# Streaming bridge: run sync work in a thread, forward its progress over SSE
# --------------------------------------------------------------------------- #
async def _stream_with_progress(
    run: Callable[[Callable[[Progress], None]], dict[str, object]],
) -> AsyncIterator[dict[str, str]]:
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[tuple[str, object]] = asyncio.Queue()

    def on_progress(progress: Progress) -> None:
        loop.call_soon_threadsafe(
            queue.put_nowait,
            (
                "progress",
                {
                    "stage": progress.stage,
                    "done": progress.done,
                    "total": progress.total,
                    "fraction": progress.fraction,
                    "message": progress.message,
                },
            ),
        )

    async def worker() -> None:
        result = await asyncio.to_thread(run, on_progress)
        loop.call_soon_threadsafe(queue.put_nowait, ("result", result))

    task = asyncio.ensure_future(worker())
    try:
        while True:
            kind, payload = await queue.get()
            yield {"event": kind, "data": json.dumps(payload)}
            if kind == "result":
                break
    finally:
        await task


# --------------------------------------------------------------------------- #
# Serialisation
# --------------------------------------------------------------------------- #
def _resolve(spec: InputSpec) -> tuple[Assumptions, SearchResult | None]:
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


def _candidate_dict(candidate: DesignCandidate) -> dict[str, object]:
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


def _search_dict(result: SearchResult) -> dict[str, object]:
    return {
        "best": _candidate_dict(result.best) if result.best else None,
        "feasible": [_candidate_dict(c) for c in result.feasible],
        "n_evaluated": result.n_evaluated,
        "objective": result.objective,
    }


def _workflow_dict(result: WorkflowResult) -> dict[str, object]:
    return {
        "steps": [
            {"name": s.name, "action": s.action, "decision": s.decision, "metrics": s.metrics}
            for s in result.steps
        ],
        "report_markdown": result.report_markdown,
        "lcoe_eur_per_gj": result.lcoe_eur_per_gj,
        "n_doublets": result.n_doublets,
    }


def _dashboard(assumptions: Assumptions) -> dict[str, object]:
    a = assumptions
    candidates = [evaluate_candidate(n, assumptions=a) for n in (1, 2, 3)]
    feasible = sorted((c for c in candidates if c.meets_demand), key=lambda c: c.lcoe_eur_per_gj)
    best = feasible[0] if feasible else min(candidates, key=lambda c: c.lcoe_eur_per_gj)

    perf = simulate(design_for(best.geo_capacity_mw, a), district_demand(assumptions=a))
    band = lcoe_monte_carlo(best.n_doublets, assumptions=a, n_samples=_API_MC_SAMPLES)
    samples = monte_carlo_lcoe_samples(best.n_doublets, assumptions=a, n_samples=_API_MC_SAMPLES)
    counts, edges = np.histogram(samples, bins=40)

    return {
        "assumptions": a.model_dump(),
        "best": _candidate_dict(best),
        "comparison": [_candidate_dict(c) for c in candidates],
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
        "resource_map": _resource_map_dict(a),
        "percentiles": _percentiles_list(),
        "monte_carlo": {
            **band,
            "hist_counts": counts.tolist(),
            "hist_edges": edges.tolist(),
        },
        "tornado": _tornado_list(a),
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


def _resource_map_dict(a: Assumptions) -> dict[str, object]:
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


def _percentiles_list() -> list[dict[str, object]]:
    pct = well_power_percentiles()
    rows = []
    for wid in pct.index:
        cols = dict(zip(pct.columns, np.asarray(pct.loc[wid], dtype=float), strict=True))
        rows.append({"well": str(wid), "p90": cols["P90"], "p50": cols["P50"], "p10": cols["P10"]})
    return rows


def _tornado_list(a: Assumptions) -> list[dict[str, object]]:
    table = tornado(_TORNADO_FIELDS, base=a)
    return [
        {
            "field": str(r["field"]),
            "low": _scalar(r["lcoe_low"]),
            "high": _scalar(r["lcoe_high"]),
            "swing": _scalar(r["swing"]),
        }
        for _, r in table.iterrows()
    ]


def _scalar(value: object) -> float:
    return float(np.asarray(value, dtype=float))


def _floats(values: npt.ArrayLike) -> list[float]:
    return [float(v) for v in np.asarray(values, dtype=float)]
