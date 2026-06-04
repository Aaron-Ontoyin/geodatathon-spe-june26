"""Tests for the agentic workflow (Phase 5g) — deterministic, no API key needed."""

from __future__ import annotations

import pytest

from geothermal.agent import narrate, run_workflow


def test_workflow_runs_all_pipeline_stages() -> None:
    result = run_workflow(mc_samples=300)
    names = " ".join(s.name.lower() for s in result.steps)
    assert "data" in names
    assert "resource" in names
    assert "siting" in names or "well" in names
    assert "design" in names or "optim" in names
    assert "risk" in names or "monte" in names
    assert len(result.steps) >= 5


def test_each_step_records_action_decision_and_metrics() -> None:
    result = run_workflow(mc_samples=300)
    for step in result.steps:
        assert step.action.strip()
        assert step.decision.strip()
        assert isinstance(step.metrics, dict)


def test_workflow_includes_report_and_headline() -> None:
    result = run_workflow(mc_samples=300)
    assert "Executive summary" in result.report_markdown
    assert result.lcoe_eur_per_gj > 0
    assert result.n_doublets >= 1


def test_workflow_is_deterministic() -> None:
    a = run_workflow(mc_samples=300)
    b = run_workflow(mc_samples=300)
    assert [s.decision for s in a.steps] == [s.decision for s in b.steps]
    assert a.lcoe_eur_per_gj == b.lcoe_eur_per_gj


def test_deterministic_narration_needs_no_key() -> None:
    result = run_workflow(mc_samples=300)
    text = narrate(result, use_llm=False)
    assert len(text) > 500
    assert "lcoe" in text.lower()


def test_llm_narration_falls_back_gracefully_without_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # use_llm requested but no key available → deterministic fallback, never crashes.
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    result = run_workflow(mc_samples=300)
    text = narrate(result, use_llm=True, api_key=None)
    assert text == narrate(result, use_llm=False)
