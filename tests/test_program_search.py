from __future__ import annotations

from geothermal.assumptions import DEFAULT_ASSUMPTIONS
from geothermal.economics.program_search import evaluate_program, search_program
from geothermal.resource.properties import SiteProperties


def _site(power: float, depth: float = 2200.0) -> SiteProperties:
    return SiteProperties(
        x=0.0, y=0.0, transmissivity_dm=power, temperature_c=77.0,
        power_mw_p50=power, depth_m=depth, sigma_log_trans=0.9, source="thermogis_grid",
    )


def test_evaluate_program_sums_capacity_and_costs_once() -> None:
    a = DEFAULT_ASSUMPTIONS
    prog = evaluate_program([_site(5.0), _site(4.0)], assumptions=a)
    assert prog.n_doublets == 2
    assert prog.geo_capacity_mw > 0
    assert prog.lcoe_eur_per_gj > 0
    deep = evaluate_program([_site(5.0, 3000.0), _site(4.0, 3000.0)], assumptions=a)
    assert deep.capex_meur > prog.capex_meur


def test_search_finds_least_lcoe_feasible_program() -> None:
    a = DEFAULT_ASSUMPTIONS
    sites = [
        SiteProperties(
            x=0.0, y=0.0, transmissivity_dm=6.0, temperature_c=77.0,
            power_mw_p50=6.0, depth_m=2200.0, sigma_log_trans=0.9, source="thermogis_grid",
        ),
        SiteProperties(
            x=3000.0, y=0.0, transmissivity_dm=6.0, temperature_c=77.0,
            power_mw_p50=6.0, depth_m=2200.0, sigma_log_trans=0.9, source="thermogis_grid",
        ),
        SiteProperties(
            x=6000.0, y=0.0, transmissivity_dm=6.0, temperature_c=77.0,
            power_mw_p50=6.0, depth_m=2200.0, sigma_log_trans=0.9, source="thermogis_grid",
        ),
    ]
    best = search_program(sites, assumptions=a, min_spacing_km=1.5)
    assert best is not None
    assert best.meets_demand
    assert best.n_doublets <= len(sites)
