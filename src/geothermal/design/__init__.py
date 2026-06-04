"""Phase 3 — integrated heating + cooling system design (Challenge 2A).

Couples the geothermal doublet(s) to a central heat pump, seasonal HT-ATES, and
heat-driven cooling so that summer demand monetises capacity that a heating-only
system would leave idle. Produces the annual energy balance the LCoE needs.
"""

from geothermal.design.demand import (
    DemandProfile,
    annual_energy_gj,
    district_demand,
    full_load_hours,
)
from geothermal.design.system import (
    SystemDesign,
    SystemPerformance,
    heating_capacity_mw,
    simulate,
)

__all__ = [
    "DemandProfile",
    "SystemDesign",
    "SystemPerformance",
    "annual_energy_gj",
    "district_demand",
    "full_load_hours",
    "heating_capacity_mw",
    "simulate",
]
