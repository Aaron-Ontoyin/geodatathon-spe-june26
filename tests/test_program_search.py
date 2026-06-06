from __future__ import annotations

from geothermal.assumptions import DEFAULT_ASSUMPTIONS
from geothermal.resource.properties import SiteProperties
from geothermal.economics.program_search import evaluate_program


def _site(power: float, depth: float = 2200.0) -> SiteProperties:
    return SiteProperties(x=0.0, y=0.0, transmissivity_dm=power, temperature_c=77.0,
                          power_mw_p50=power, depth_m=depth, sigma_log_trans=0.9, source="thermogis_grid")


def test_evaluate_program_sums_capacity_and_costs_once() -> None:
    a = DEFAULT_ASSUMPTIONS
    prog = evaluate_program([_site(5.0), _site(4.0)], assumptions=a)
    assert prog.n_doublets == 2
    assert prog.geo_capacity_mw > 0
    assert prog.lcoe_eur_per_gj > 0
    deep = evaluate_program([_site(5.0, 3000.0), _site(4.0, 3000.0)], assumptions=a)
    assert deep.capex_meur > prog.capex_meur
