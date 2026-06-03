"""Phase 2 — geothermal resource assessment (Challenge 1).

Per-well probabilistic power from a calibrated doublet model, a spatial map of the
resource across the Utrecht box, and selection of new well locations to meet the
district base load.
"""

from geothermal.resource.assessment import (
    distance_km,
    locate_demand_center,
    well_power_percentiles,
)
from geothermal.resource.power import (
    doublet_flow_m3_h,
    geothermal_power_mw,
    well_power_mw,
)
from geothermal.resource.spatial import (
    ResourceGrid,
    interpolate_resource,
    recommend_new_well,
    resource_grid,
)

__all__ = [
    "ResourceGrid",
    "distance_km",
    "doublet_flow_m3_h",
    "geothermal_power_mw",
    "interpolate_resource",
    "locate_demand_center",
    "recommend_new_well",
    "resource_grid",
    "well_power_mw",
    "well_power_percentiles",
]
