"""Tests for the standalone CLI (Phase 6) — key-free, file-driven."""

from __future__ import annotations

import tomllib
from pathlib import Path

from geothermal.cli import main


def test_template_command_writes_parseable_toml(tmp_path: Path) -> None:
    out = tmp_path / "inputs.toml"
    assert main(["template", "--out", str(out)]) == 0
    assert out.exists()
    tomllib.loads(out.read_text(encoding="utf-8"))  # valid TOML


def test_report_command_writes_markdown(tmp_path: Path) -> None:
    inp = tmp_path / "in.toml"
    inp.write_text("[assumptions]\nelectricity_price_eur_per_mwhe = 150.0\n", encoding="utf-8")
    out = tmp_path / "report.md"
    assert main(["report", "--input", str(inp), "--out", str(out), "--mc-samples", "200"]) == 0
    assert "Executive summary" in out.read_text(encoding="utf-8")


def test_report_command_honours_search_section(tmp_path: Path) -> None:
    inp = tmp_path / "in.toml"
    inp.write_text(
        '[search.ranges]\ninjection_temp_c = [25.0, 40.0]\n\n[search]\nobjective = "min_lcoe"\n',
        encoding="utf-8",
    )
    out = tmp_path / "r.md"
    assert main(["report", "--input", str(inp), "--out", str(out), "--mc-samples", "200"]) == 0
    assert out.exists()


def test_workflow_command_prints_decision_log(tmp_path: Path, capsys) -> None:
    assert main(["workflow", "--mc-samples", "200"]) == 0
    out = capsys.readouterr().out
    assert "decision log" in out.lower()
