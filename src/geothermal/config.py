"""Project paths, the four-well registry, and shared physical constants.

All subsurface coordinates are in the Dutch national grid **RD New (Amersfoort),
EPSG:28992**, with units of metres. Depths in the source data are a mix of
along-hole (measured) and true-vertical; the petrophysics module reconciles them.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DIR: Path = DATA_DIR / "raw"
DOCS_DIR: Path = PROJECT_ROOT / "docs"
OUTPUTS_DIR: Path = PROJECT_ROOT / "outputs"

LAS_FILES: dict[str, Path] = {
    "BLT-01": RAW_DIR / "BLT-01.las",
    "EVD-01": RAW_DIR / "EVD-01.las",
    "JUT-01": RAW_DIR / "JUT-01.las",
    "PKP-01": RAW_DIR / "PKP-01.las",
}
WELL_PATH_XLSX: Path = DATA_DIR / "Well Path Data.xlsx"
LITHOSTRAT_XLSX: Path = DATA_DIR / "Lithostratigraphic Data.xlsx"
THERMOGIS_XLSX: Path = DATA_DIR / "ThermoGIS Data.xlsx"
LCOE_XLSX: Path = DATA_DIR / "LCOE.xlsx"
TARGET_LITHOLOGIES_CSV: Path = DATA_DIR / "target_lithologies.csv"

CRS_RD_NEW: str = "EPSG:28992"  # Amersfoort / RD New — Dutch national grid (metres)


# --------------------------------------------------------------------------- #
# Well registry
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class Well:
    """A provided well, with surface/header coordinates in RD New (metres)."""

    well_id: str
    full_name: str
    x: float  # RD New easting (m)
    y: float  # RD New northing (m)


# Header coordinates taken from the LAS headers / ThermoGIS sheets.
# NOTE: the ThermoGIS sheet named "BLT-01" mislabels its Well Name cell as
# "PKP-01"; its coordinates (141577.55, 456881.76) are in fact BLT-01's, so we
# key wells by the trustworthy sheet name + coordinates, never that inner label.
WELLS: dict[str, Well] = {
    "BLT-01": Well("BLT-01", "BLT-01", 141577.55, 456881.76),
    "EVD-01": Well("EVD-01", "EVERDINGEN-01", 136997.00, 441189.00),
    "JUT-01": Well("JUT-01", "JUT-01", 134098.00, 451726.00),
    "PKP-01": Well("PKP-01", "PAPEKOP-01", 118503.09, 453402.51),
}
WELL_IDS: list[str] = list(WELLS)

# The demand district. `target_lithologies.csv` records `distance_to_usp_km` for
# every well; "USP" = Utrecht Science Park, the district to be heated/cooled. Its
# precise location is trilaterated from those distances in the resource module.
TARGET_DISTRICT_NAME: str = "Utrecht Science Park (USP)"

# Demand to satisfy (challenge hard constraints).
HEATING_DEMAND_MWTH: float = 10.0
COOLING_DEMAND_MWTH: float = 5.0


# --------------------------------------------------------------------------- #
# Physical constants (aligned with the provided LCOE.xlsx so our numbers tie out)
# --------------------------------------------------------------------------- #
CP_WATER: float = 4250.0  # J/(kg·K) — reservoir brine, per LCOE sheet
RHO_WATER: float = 1078.0  # kg/m³ — reservoir brine, per LCOE sheet
CP_ROCK: float = 1000.0  # J/(kg·K)
RHO_ROCK: float = 2700.0  # kg/m³
SECONDS_PER_YEAR: float = 31_557_600.0
SURFACE_TEMPERATURE_C: float = 10.0  # average yearly surface temp (NL), per LCOE sheet

# Volumetric heat capacity of the produced brine [J/(m³·K)] — the constant in
# P_th = Q · (ρ·cp) · ΔT  when Q is in m³/s and ΔT in K.
RHO_CP_WATER: float = RHO_WATER * CP_WATER
