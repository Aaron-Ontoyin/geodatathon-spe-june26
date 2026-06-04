"""Tests for the FastAPI backend (Phase 6b). Skipped if the `web` extra is absent."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sse_starlette")

from fastapi.testclient import TestClient

from geothermal.api import app

client = TestClient(app)


def test_healthz() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_config_lists_fields_with_descriptions() -> None:
    data = client.get("/config").json()
    assert data["defaults"]["heating_peak_mw"] == 10.0
    names = [f["name"] for f in data["fields"]]
    assert "heat_pump_cop" in names
    assert any(f["description"] for f in data["fields"])


def test_analyze_returns_full_dashboard() -> None:
    data = client.post("/analyze", json={}).json()
    assert data["headline"]["n_doublets"] >= 1
    assert data["resource_map"]["power"]  # non-empty grid
    assert len(data["percentiles"]) == 4
    mc = data["monte_carlo"]
    assert mc["p10"] <= mc["p50"] <= mc["p90"]
    assert data["tornado"]


def test_analyze_rejects_invalid_input() -> None:
    response = client.post("/analyze", json={"assumptions": {"heat_pump_cop": 0.5}})
    assert response.status_code == 422  # Pydantic validation surfaced by FastAPI


def test_report_returns_markdown() -> None:
    data = client.post("/report", json={}).json()
    assert "Executive summary" in data["markdown"]


def test_optimize_stream_emits_progress_then_result() -> None:
    body = {"search": {"ranges": {"injection_temp_c": [25.0, 40.0]}}}
    with client.stream("POST", "/optimize/stream", json=body) as response:
        assert response.status_code == 200
        text = "".join(response.iter_text())
    assert "progress" in text
    assert "result" in text


def test_chat_stream_without_key_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with client.stream("POST", "/chat", json={"question": "why?", "context": "ctx"}) as response:
        text = "".join(response.iter_text())
    assert "unavailable" in text.lower()
