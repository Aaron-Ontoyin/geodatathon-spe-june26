from __future__ import annotations

from geothermal.assumptions import DEFAULT_ASSUMPTIONS
from geothermal.economics.program_search import (
    evaluate_program,
    program_monte_carlo,
    search_program,
)
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


def test_independent_draws_produce_ordered_band() -> None:
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
    ]
    band = program_monte_carlo(sites, assumptions=a, n_samples=400, seed=1)
    assert band["p10"] <= band["p50"] <= band["p90"]
    assert band["p90"] - band["p10"] >= 0


def test_transmission_cost_penalises_distant_sites() -> None:
    from geothermal.economics.program_search import evaluate_program
    a = DEFAULT_ASSUMPTIONS
    cx, cy = a.aoi_center_rd
    near = SiteProperties(
        x=cx, y=cy, transmissivity_dm=9.0, temperature_c=77.0,
        power_mw_p50=6.0, depth_m=2280.0, sigma_log_trans=1.5, source="thermogis_grid",
    )
    far = SiteProperties(
        x=cx + 8000.0, y=cy, transmissivity_dm=9.0, temperature_c=77.0,
        power_mw_p50=6.0, depth_m=2280.0, sigma_log_trans=1.5, source="thermogis_grid",
    )
    near_prog = evaluate_program([near], assumptions=a)
    far_prog = evaluate_program([far], assumptions=a)
    # identical reservoir, but the far site carries 8 km of extra transmission main
    assert far_prog.capex_meur > near_prog.capex_meur
    assert far_prog.lcoe_eur_per_gj > near_prog.lcoe_eur_per_gj
