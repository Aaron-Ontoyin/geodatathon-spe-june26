"""Loaders for the four provided Excel workbooks.

* Well Path Data       — directional surveys (one sheet per well)
* Lithostratigraphic   — formation tops/bottoms (one sheet per well)
* ThermoGIS Data       — Rotliegend P10/P50/P90 reservoir properties (one sheet per well)
* LCOE                 — TNO/ECN levelised-cost model (ported to Python in Phase 4)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from geothermal import config

# --------------------------------------------------------------------------- #
# Well Path Data (directional surveys)
# --------------------------------------------------------------------------- #
_SURVEY_COLUMNS = [
    "md_m",
    "inclination_deg",
    "azimuth_deg",
    "tvd_m",
    "x_offset_m",
    "y_offset_m",
]


def load_well_paths(path: str | Path = config.WELL_PATH_XLSX) -> dict[str, pd.DataFrame]:
    """Return ``{well_id: survey}`` with normalised numeric columns, sorted by MD.

    Columns: md_m, inclination_deg, azimuth_deg, tvd_m, x_offset_m, y_offset_m.
    """
    sheets = pd.read_excel(path, sheet_name=None, header=0)
    out: dict[str, pd.DataFrame] = {}
    for name, raw in sheets.items():
        df = raw.iloc[:, : len(_SURVEY_COLUMNS)].copy()
        df.columns = _SURVEY_COLUMNS
        df = df.apply(pd.to_numeric, errors="coerce").dropna(how="all")
        out[name.strip()] = df.sort_values("md_m").reset_index(drop=True)
    return out


# --------------------------------------------------------------------------- #
# Lithostratigraphy (formation tops)
# --------------------------------------------------------------------------- #
def load_lithostratigraphy(
    path: str | Path = config.LITHOSTRAT_XLSX,
) -> dict[str, pd.DataFrame]:
    """Return ``{well_id: tops}`` with columns unit, top_m, bottom_m, anomaly_code.

    Depths here are as-drilled (measured) and are reconciled to TVD in petrophysics.
    """
    sheets = pd.read_excel(path, sheet_name=None, header=0)
    out: dict[str, pd.DataFrame] = {}
    for name, raw in sheets.items():
        # Layout: col0 = unit, col1 = (blank), col2 = Top, col3 = Bottom, col4 = Anomaly.
        df = pd.DataFrame(
            {
                "unit": raw.iloc[:, 0].astype("string").str.strip(),
                "top_m": pd.to_numeric(raw.iloc[:, 2], errors="coerce"),
                "bottom_m": pd.to_numeric(raw.iloc[:, 3], errors="coerce"),
                "anomaly_code": (
                    raw.iloc[:, 4].astype("string").str.strip()
                    if raw.shape[1] > 4
                    else pd.Series([pd.NA] * len(raw), dtype="string")
                ),
            }
        )
        df = df.dropna(subset=["unit", "top_m"]).reset_index(drop=True)
        out[name.strip()] = df
    return out


# --------------------------------------------------------------------------- #
# ThermoGIS reservoir properties
# --------------------------------------------------------------------------- #
_THERMOGIS_PERCENTILES = ["P90", "P50", "P10"]


@dataclass(frozen=True, slots=True)
class ThermoGisWell:
    """ThermoGIS Rotliegend properties for one well.

    ``well_id`` is taken from the (trustworthy) sheet name; ``inner_label`` keeps the
    file's own "Well Name" cell, which is mislabeled for the BLT-01 sheet.
    """

    well_id: str
    inner_label: str
    x: float
    y: float
    properties: pd.DataFrame  # index = property, columns = [unit, P90, P50, P10]

    def value(self, prop: str, percentile: str = "P50") -> float:
        return float(np.asarray(self.properties.loc[prop, percentile], dtype=float))


def _find_row(col: pd.Series, key: str) -> int | None:
    matches = col.astype("string").str.strip().str.lower() == key.lower()
    idx = matches[matches].index
    return int(idx[0]) if len(idx) else None


def load_thermogis(path: str | Path = config.THERMOGIS_XLSX) -> dict[str, ThermoGisWell]:
    """Return ``{well_id: ThermoGisWell}`` keyed by sheet name (coords trusted over label)."""
    sheets = pd.read_excel(path, sheet_name=None, header=None)
    out: dict[str, ThermoGisWell] = {}
    for name, raw in sheets.items():
        well_id = name.strip()
        col0 = raw.iloc[:, 0]
        inner_row = _find_row(col0, "Well Name")
        x_row = _find_row(col0, "x")
        y_row = _find_row(col0, "Y")
        header_row = _find_row(col0, "Property")
        if header_row is None or x_row is None or y_row is None:
            raise ValueError(f"ThermoGIS sheet '{name}' missing expected layout")

        inner_label = str(raw.iloc[inner_row, 1]) if inner_row is not None else ""
        x = float(raw.iloc[x_row, 1])
        y = float(raw.iloc[y_row, 1])

        body = raw.iloc[header_row + 1 :, 0:5].copy()
        body.columns = ["property", "unit", *_THERMOGIS_PERCENTILES]
        body["property"] = body["property"].astype("string").str.strip()
        body = body.dropna(subset=["property"])
        for pct in _THERMOGIS_PERCENTILES:
            body[pct] = pd.to_numeric(body[pct], errors="coerce")
        props = body.set_index("property")

        out[well_id] = ThermoGisWell(
            well_id=well_id, inner_label=inner_label, x=x, y=y, properties=props
        )
    return out


def thermogis_tidy(wells: dict[str, ThermoGisWell]) -> pd.DataFrame:
    """Flatten ThermoGIS wells into one long DataFrame for plotting/joins."""
    frames: list[pd.DataFrame] = []
    for w in wells.values():
        df = w.properties.reset_index()
        df.insert(0, "well_id", w.well_id)
        df.insert(1, "x", w.x)
        df.insert(2, "y", w.y)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


# --------------------------------------------------------------------------- #
# LCOE workbook (raw; parsed in Phase 4)
# --------------------------------------------------------------------------- #
def load_lcoe_input_output(path: str | Path = config.LCOE_XLSX) -> pd.DataFrame:
    """Return the LCOE 'Input_Output' sheet as a raw, header-less DataFrame.

    The sheet interleaves labels, values, units and side calculations; Phase 4
    extracts the specific cells we need and reimplements the cash-flow logic.
    """
    return pd.read_excel(path, sheet_name="Input_Output", header=None)
