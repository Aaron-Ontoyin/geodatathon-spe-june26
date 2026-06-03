"""LAS wireline-log loader.

Normalises the four well logs into a depth-in-metres DataFrame regardless of the
quirks in each file. In particular it resolves the **JUT-01 unit collision**: that
file carries two depth channels (`DEPT` in feet *and* in metres), which makes a
naive read index the logs in feet and report a bogus ~11 220 "metre" total depth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import lasio
import numpy as np
import pandas as pd

from geothermal import config

_DEPTH_MNEMONICS = {"DEPT", "DEPTH", "MD"}
_METRE_UNITS = {"m", "meter", "metre", "meters", "metres"}
_FEET_UNITS = {"f", "ft", "feet", "foot"}
_FEET_TO_M = 0.3048


@dataclass(frozen=True, slots=True)
class LasData:
    """A normalised LAS log set for one well.

    Attributes:
        well_id: Canonical well id (e.g. ``"BLT-01"``).
        logs: Log curves indexed by ``depth_m`` (measured depth in metres);
            depth channels are removed from the columns.
        depth_unit_original: Unit of the file's primary depth channel as written.
        header: Well-information header items (mnemonic -> value, heterogeneous).
        notes: Human-readable QC observations made while normalising.
    """

    well_id: str
    logs: pd.DataFrame
    depth_unit_original: str
    header: dict[str, object]
    notes: list[str] = field(default_factory=list)

    @property
    def depth_m(self) -> pd.Index:
        return self.logs.index

    @property
    def curve_names(self) -> list[str]:
        return list(self.logs.columns)


def _dedupe(key: str, existing: dict[str, np.ndarray]) -> str:
    if key not in existing:
        return key
    n = 2
    while f"{key}.{n}" in existing:
        n += 1
    return f"{key}.{n}"


def load_las(path: str | Path, well_id: str | None = None) -> LasData:
    """Load and normalise a single LAS file to depth-in-metres."""
    path = Path(path)
    if well_id is None:
        well_id = path.stem.split(".")[0]

    las = lasio.read(str(path))
    notes: list[str] = []

    # Build columns by position so duplicate mnemonics (e.g. DEPT/DEPT) survive.
    columns: dict[str, np.ndarray] = {}
    depth_candidates: list[tuple[str, str]] = []  # (column_key, unit_lower)
    for curve in las.curves:
        key = _dedupe(curve.mnemonic, columns)
        columns[key] = curve.data
        # lasio disambiguates duplicate depth channels as ``DEPT:1`` / ``DEPT:2``
        # (JUT-01 has both a feet and a metre channel), so match the base mnemonic.
        base = curve.mnemonic.split(":")[0].strip().upper()
        if base in _DEPTH_MNEMONICS:
            depth_candidates.append((key, (curve.unit or "").strip().lower()))

    df = pd.DataFrame(columns)

    if not depth_candidates:
        raise ValueError(f"{well_id}: no depth/MD channel found in {path.name}")

    primary_key, primary_unit = depth_candidates[0]

    # Prefer an explicit metre channel; else convert feet; else assume metres.
    metre_key = next((k for k, u in depth_candidates if u in _METRE_UNITS), None)
    if metre_key is not None:
        depth_key, factor = metre_key, 1.0
        if len(depth_candidates) > 1:
            notes.append(
                f"{len(depth_candidates)} depth channels present; used metre channel "
                f"'{metre_key}' (primary written unit was '{primary_unit or '?'}')."
            )
    elif primary_unit in _FEET_UNITS:
        depth_key, factor = primary_key, _FEET_TO_M
        notes.append(f"Primary depth channel was feet ('{primary_unit}'); converted to metres.")
    else:
        depth_key, factor = primary_key, 1.0
        if primary_unit not in _METRE_UNITS:
            notes.append(f"Depth unit '{primary_unit or '?'}' unrecognised; assumed metres.")

    depth_m = np.asarray(pd.to_numeric(df[depth_key], errors="coerce"), dtype=float) * factor
    depth_cols = [k for k, _ in depth_candidates]
    logs = pd.DataFrame(df.drop(columns=depth_cols).apply(pd.to_numeric, errors="coerce"))
    logs.index = pd.Index(depth_m, name="depth_m")
    logs = logs.loc[np.isfinite(depth_m)].sort_index()

    header = {item.mnemonic: item.value for item in las.well}
    return LasData(
        well_id=well_id,
        logs=logs,
        depth_unit_original=primary_unit or "?",
        header=header,
        notes=notes,
    )


def load_all_las() -> dict[str, LasData]:
    """Load and normalise all four provided well logs, keyed by canonical id."""
    return {wid: load_las(path, well_id=wid) for wid, path in config.LAS_FILES.items()}
