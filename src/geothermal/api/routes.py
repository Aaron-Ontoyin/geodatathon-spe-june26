"""API routes. Thin handlers that delegate to the serialization/streaming helpers."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from geothermal.agent.workflow import run_workflow
from geothermal.api import serialization as ser
from geothermal.api.schemas import ChatRequest
from geothermal.api.streaming import chat_events, stream_with_progress
from geothermal.assumptions import DEFAULT_ASSUMPTIONS, Assumptions
from geothermal.economics.search import search_designs
from geothermal.inputs import InputSpec
from geothermal.progress import Progress
from geothermal.report import build_report

router = APIRouter()


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/config")
def get_config() -> dict[str, object]:
    """Field metadata (defaults + descriptions) so the UI can build the form."""
    fields = [
        {"name": name, "default": info.default, "description": info.description}
        for name, info in Assumptions.model_fields.items()
    ]
    return {"defaults": DEFAULT_ASSUMPTIONS.model_dump(), "fields": fields}


@router.post("/analyze")
def analyze(spec: InputSpec) -> dict[str, object]:
    """Full dashboard payload (numbers + chart data) for the resolved design."""
    assumptions, _ = ser.resolve(spec)
    return ser.dashboard(assumptions)


@router.post("/report")
def report(spec: InputSpec) -> dict[str, str]:
    """The full transparent report as Markdown (served lazily for the Report tab)."""
    assumptions, _ = ser.resolve(spec)
    return {"markdown": build_report(assumptions=assumptions, mc_samples=ser.API_MC_SAMPLES)}


@router.post("/optimize/stream")
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
        return ser.search_dict(result)

    return EventSourceResponse(stream_with_progress(run))


@router.post("/workflow/stream")
async def workflow_stream(spec: InputSpec) -> EventSourceResponse:
    """Run the agentic workflow, streaming stage progress then the decision log."""
    assumptions, _ = ser.resolve(spec)

    def run(on_progress: Callable[[Progress], None]) -> dict[str, object]:
        result = run_workflow(
            assumptions=assumptions, mc_samples=ser.API_MC_SAMPLES, on_progress=on_progress
        )
        return {
            "steps": [
                {"name": s.name, "action": s.action, "decision": s.decision, "metrics": s.metrics}
                for s in result.steps
            ],
            "lcoe_eur_per_gj": result.lcoe_eur_per_gj,
            "n_doublets": result.n_doublets,
        }

    return EventSourceResponse(stream_with_progress(run))


@router.post("/chat")
async def chat(request: ChatRequest) -> EventSourceResponse:
    """Stream a grounded chat answer token-by-token over SSE."""
    return EventSourceResponse(chat_events(request))
