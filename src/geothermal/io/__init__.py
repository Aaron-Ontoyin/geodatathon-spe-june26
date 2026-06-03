"""Typed loaders for the provided datathon data sources.

Each loader returns tidy pandas structures (or small dataclasses wrapping them)
and isolates the quirks of the raw files so the rest of the pipeline never has to
think about sheet layouts, unit collisions, or mislabeled cells.
"""

from geothermal.io.excel_loader import (
    ThermoGisWell,
    load_lcoe_input_output,
    load_lithostratigraphy,
    load_thermogis,
    load_well_paths,
)
from geothermal.io.las_loader import LasData, load_all_las, load_las
from geothermal.io.lithology_loader import load_target_lithologies

__all__ = [
    "LasData",
    "ThermoGisWell",
    "load_all_las",
    "load_las",
    "load_lcoe_input_output",
    "load_lithostratigraphy",
    "load_target_lithologies",
    "load_thermogis",
    "load_well_paths",
]
