"""Tests for the self-validating TOML input spec (Pydantic) and template (Phase 6)."""

from __future__ import annotations

import tomllib

import pytest
from pydantic import ValidationError

from geothermal.assumptions import DEFAULT_ASSUMPTIONS
from geothermal.inputs import default_template, parse_input_data


def test_template_is_valid_toml_and_parses_to_defaults() -> None:
    spec = parse_input_data(tomllib.loads(default_template()))
    assert spec.assumptions == DEFAULT_ASSUMPTIONS  # everything commented → all defaults
    assert spec.search.ranges == {}
    assert spec.search.objective == "min_lcoe"


def test_template_includes_field_descriptions() -> None:
    text = default_template()
    assert "Peak district heating demand" in text  # description carried from the model


def test_assumption_overrides_apply_and_keep_other_defaults() -> None:
    spec = parse_input_data({"assumptions": {"electricity_price_eur_per_mwhe": 250.0}})
    assert spec.assumptions.electricity_price_eur_per_mwhe == 250.0
    assert spec.assumptions.heating_peak_mw == DEFAULT_ASSUMPTIONS.heating_peak_mw


def test_unknown_assumption_key_is_rejected() -> None:
    with pytest.raises(ValidationError):
        parse_input_data({"assumptions": {"not_a_real_field": 1.0}})


def test_out_of_range_value_is_rejected() -> None:
    # heat_pump_cop must be > 1 (COP/(COP-1) needs it); validation catches a bad value.
    with pytest.raises(ValidationError):
        parse_input_data({"assumptions": {"heat_pump_cop": 0.5}})


def test_search_section_is_parsed() -> None:
    spec = parse_input_data(
        {
            "search": {
                "ranges": {"injection_temp_c": [25.0, 40.0]},
                "constraints": {"max_capex_meur": 25.0},
                "objective": "max_capacity",
            }
        }
    )
    assert spec.search.ranges["injection_temp_c"] == (25.0, 40.0)
    assert spec.search.constraints.max_capex_meur == 25.0
    assert spec.search.objective == "max_capacity"


def test_unknown_range_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        parse_input_data({"search": {"ranges": {"not_a_field": [1.0, 2.0]}}})


def test_bad_objective_is_rejected() -> None:
    with pytest.raises(ValidationError):
        parse_input_data({"search": {"objective": "make_it_cheap_somehow"}})
