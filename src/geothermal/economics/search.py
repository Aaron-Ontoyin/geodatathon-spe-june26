"""Generalized design optimiser: ranges + constraints + objective.

Each design variable is either **fixed** (a value in the base config) or a **range**
to search; **constraints** are hard requirements the answer must satisfy; the
**objective** is what to optimise. Because one design evaluation costs ~milliseconds,
a grid (or random, for high-dimensional spaces) search over the variable space is
ample — no heavy optimisation machinery needed.

This is the "give me constraints, some ranges, some numbers — return the best design"
engine. It optimises on the expected (P50) case; pair with ``lcoe_monte_carlo`` on the
winner to report the P10/P90 risk.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from geothermal.assumptions import DEFAULT_ASSUMPTIONS, Assumptions
from geothermal.economics.optimization import DesignCandidate, evaluate_candidate

Objective = Literal["min_lcoe", "min_capex", "max_capacity"]


class DesignConstraints(BaseModel):
    """Hard requirements a design must satisfy to be considered."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_backup_fraction: float = Field(
        default=DEFAULT_ASSUMPTIONS.max_backup_fraction,
        ge=0,
        le=1,
        description="Max heat share from backup.",
    )
    max_lcoe_eur_per_gj: float | None = Field(
        default=None, gt=0, description="Optional LCoE cap (€/GJ)."
    )
    max_capex_meur: float | None = Field(
        default=None, gt=0, description="Optional CAPEX budget (M€)."
    )
    min_geo_capacity_mw: float | None = Field(
        default=None, ge=0, description="Optional firm geothermal floor (MW)."
    )
    min_heating_capacity_mw: float | None = Field(
        default=None, ge=0, description="Optional heating-capacity floor (MW)."
    )


@dataclass(frozen=True, slots=True)
class SearchResult:
    """Outcome of a design search: the winner, all feasible options, and effort."""

    best: DesignCandidate | None
    feasible: list[DesignCandidate]
    n_evaluated: int
    objective: Objective


_NO_EXTRA_CONSTRAINTS = DesignConstraints()


def search_designs(
    *,
    base: Assumptions = DEFAULT_ASSUMPTIONS,
    doublet_options: tuple[int, ...] = (1, 2, 3),
    ranges: dict[str, tuple[float, float]] | None = None,
    samples: int = 6,
    max_evaluations: int = 2000,
    constraints: DesignConstraints = _NO_EXTRA_CONSTRAINTS,
    objective: Objective = "min_lcoe",
    seed: int = 0,
) -> SearchResult:
    """Search the design space for the best design satisfying the constraints."""
    ranges = ranges or {}
    combos = _assumption_combos(ranges, samples=samples, max_evaluations=max_evaluations, seed=seed)

    feasible: list[DesignCandidate] = []
    for n_doublets in doublet_options:
        for overrides in combos:
            candidate = evaluate_candidate(
                n_doublets, assumptions=base.model_copy(update=overrides)
            )
            if _is_feasible(candidate, constraints):
                feasible.append(candidate)

    feasible.sort(key=_objective_key(objective))
    n_evaluated = len(doublet_options) * len(combos)
    return SearchResult(
        best=feasible[0] if feasible else None,
        feasible=feasible,
        n_evaluated=n_evaluated,
        objective=objective,
    )


def _assumption_combos(
    ranges: dict[str, tuple[float, float]], *, samples: int, max_evaluations: int, seed: int
) -> list[dict[str, float]]:
    """Build the list of assumption overrides to try (grid, or random if too large)."""
    if not ranges:
        return [{}]
    names = list(ranges)
    bounds = [ranges[name] for name in names]
    grid_size = samples ** len(names)
    if grid_size <= max_evaluations:
        axes = [np.linspace(lo, hi, samples) for (lo, hi) in bounds]
        return [dict(zip(names, values, strict=True)) for values in itertools.product(*axes)]
    rng = np.random.default_rng(seed)
    return [
        {name: float(rng.uniform(lo, hi)) for name, (lo, hi) in zip(names, bounds, strict=True)}
        for _ in range(max_evaluations)
    ]


def _is_feasible(candidate: DesignCandidate, constraints: DesignConstraints) -> bool:
    c = constraints
    if candidate.backup_fraction > c.max_backup_fraction:
        return False
    if c.max_lcoe_eur_per_gj is not None and candidate.lcoe_eur_per_gj > c.max_lcoe_eur_per_gj:
        return False
    if c.max_capex_meur is not None and candidate.capex_meur > c.max_capex_meur:
        return False
    if c.min_geo_capacity_mw is not None and candidate.geo_capacity_mw < c.min_geo_capacity_mw:
        return False
    return not (
        c.min_heating_capacity_mw is not None
        and candidate.heating_capacity_mw < c.min_heating_capacity_mw
    )


def _objective_key(objective: Objective) -> Callable[[DesignCandidate], tuple[float, ...]]:
    if objective == "min_capex":
        return lambda c: (c.capex_meur, c.lcoe_eur_per_gj)
    if objective == "max_capacity":
        return lambda c: (-c.heating_capacity_mw, c.lcoe_eur_per_gj)
    return lambda c: (c.lcoe_eur_per_gj,)
