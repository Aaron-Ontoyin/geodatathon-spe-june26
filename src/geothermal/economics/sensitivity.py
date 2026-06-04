"""One-way sensitivity analysis over the typed config (Phase 5d).

Now that every lever is a parameter, sensitivity is just "vary one field, re-optimise,
record the result". ``lcoe_sensitivity`` sweeps a field; ``tornado`` ranks several
assumptions by how much their plausible range swings the optimal LCoE — the chart
that tells judges which numbers actually matter (and which assumptions don't).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import pandas as pd

from geothermal.assumptions import DEFAULT_ASSUMPTIONS, Assumptions
from geothermal.economics.optimization import optimize


def lcoe_sensitivity(
    field: str, values: Sequence[float], *, base: Assumptions = DEFAULT_ASSUMPTIONS
) -> pd.DataFrame:
    """Re-optimise across values of one assumption; return value → best design + LCoE."""
    rows: list[dict[str, float]] = []
    for value in values:
        candidates = optimize(assumptions=base.model_copy(update={field: value}))
        best = candidates[0] if candidates else None
        rows.append(
            {
                field: float(value),
                "n_doublets": float(best.n_doublets) if best else 0.0,
                "lcoe_eur_per_gj": best.lcoe_eur_per_gj if best else math.nan,
                "capex_meur": best.capex_meur if best else math.nan,
            }
        )
    return pd.DataFrame(rows)


def tornado(
    fields: dict[str, tuple[float, float]], *, base: Assumptions = DEFAULT_ASSUMPTIONS
) -> pd.DataFrame:
    """Rank assumptions by how much their low→high range swings the optimal LCoE."""
    rows = [
        {
            "field": name,
            "low": low,
            "high": high,
            "lcoe_low": _best_lcoe(base.model_copy(update={name: low})),
            "lcoe_high": _best_lcoe(base.model_copy(update={name: high})),
            "swing": abs(
                _best_lcoe(base.model_copy(update={name: high}))
                - _best_lcoe(base.model_copy(update={name: low}))
            ),
        }
        for name, (low, high) in fields.items()
    ]
    return pd.DataFrame(rows).sort_values("swing", ascending=False).reset_index(drop=True)


def _best_lcoe(assumptions: Assumptions) -> float:
    candidates = optimize(assumptions=assumptions)
    return candidates[0].lcoe_eur_per_gj if candidates else math.nan
