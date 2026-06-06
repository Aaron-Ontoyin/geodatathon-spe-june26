"""Tests that long-running operations emit progress (the seam for the live UI)."""

from __future__ import annotations

from geothermal.agent.workflow import run_workflow
from geothermal.economics.search import search_designs
from geothermal.progress import Progress


def test_search_emits_monotonic_progress_to_completion() -> None:
    events: list[Progress] = []
    search_designs(ranges={"injection_temp_c": (25.0, 40.0)}, samples=4, on_progress=events.append)
    assert events
    assert all(isinstance(e, Progress) for e in events)
    assert [e.done for e in events] == sorted(e.done for e in events)
    assert events[-1].done == events[-1].total  # finishes at 100%


def test_workflow_emits_progress_through_all_stages() -> None:
    events: list[Progress] = []
    run_workflow(mc_samples=200, on_progress=events.append)
    assert events
    assert events[-1].done == events[-1].total == 7
    assert events[-1].fraction == 1.0
