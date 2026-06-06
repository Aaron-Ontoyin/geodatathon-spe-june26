"""Tests for the well-cost formula ported from LCOE.xlsx (cell D12)."""

from __future__ import annotations

import pytest

from geothermal.economics.well_cost import well_capex_meur


def test_reproduces_lcoe_xlsx_worked_example_at_1800m() -> None:
    # LCOE.xlsx D12 at 1800 m along-hole reads 3.237 M€; our port must match.
    assert well_capex_meur(1800.0) == pytest.approx(3.237, abs=1e-3)


def test_well_capex_increases_with_depth() -> None:
    # Our Utrecht wells (~2281 m) cost more than the spreadsheet's 1800 m example.
    assert well_capex_meur(2281.0) > well_capex_meur(1800.0)
    assert well_capex_meur(2281.0) == pytest.approx(4.331, abs=1e-2)
