"""Tests for the deterministic, no-API-key transparency report (Phase 5f)."""

from __future__ import annotations

from pathlib import Path

from geothermal.report import build_report, write_report


def test_report_covers_all_sections_and_key_numbers() -> None:
    md = build_report(mc_samples=300)
    lowered = md.lower()
    for section in (
        "executive summary",
        "data foundation",
        "resource",
        "system design",
        "economics",
        "assumptions",
        "limitations",
    ):
        assert section in lowered, f"missing section: {section}"
    assert "lcoe" in lowered
    assert "p10" in lowered and "p50" in lowered and "p90" in lowered
    assert "capacity factor" in lowered
    assert len(md) > 2000


def test_report_is_deterministic() -> None:
    assert build_report(mc_samples=300) == build_report(mc_samples=300)


def test_write_report_creates_markdown_file(tmp_path: Path) -> None:
    path = write_report(tmp_path / "report.md", mc_samples=200)
    assert path.exists()
    assert path.read_text(encoding="utf-8").lstrip().startswith("#")
