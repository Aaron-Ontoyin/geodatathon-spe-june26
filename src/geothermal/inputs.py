"""Self-validating run specification (Pydantic) + a starting-point TOML template.

``InputSpec`` mirrors the TOML input file and is validated by Pydantic — unknown keys,
bad types and out-of-range values are rejected automatically with clear messages. The
same model is reused as the FastAPI request body, so the CLI and the API share one
source of truth (and the API gets OpenAPI docs for free). The template is generated
from the model's own field descriptions, so it never drifts from the config.
"""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator

from geothermal.assumptions import Assumptions
from geothermal.economics.search import DesignConstraints, Objective

_ASSUMPTION_FIELDS = set(Assumptions.model_fields)


class SearchSpec(BaseModel):
    """Optional optimiser request: which assumptions to sweep, constraints, objective."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    ranges: dict[str, tuple[float, float]] = Field(
        default_factory=dict, description="Map of assumption name → [min, max] to search."
    )
    constraints: DesignConstraints = Field(default_factory=DesignConstraints)
    objective: Objective = Field(
        default="min_lcoe", description="min_lcoe, min_capex, or max_capacity."
    )

    @field_validator("ranges")
    @classmethod
    def _ranges_are_real_assumptions(
        cls, value: dict[str, tuple[float, float]]
    ) -> dict[str, tuple[float, float]]:
        unknown = set(value) - _ASSUMPTION_FIELDS
        if unknown:
            raise ValueError(f"unknown search.ranges fields: {sorted(unknown)}")
        return value


class InputSpec(BaseModel):
    """A full run specification: the assumptions, plus an optional search request."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    assumptions: Assumptions = Field(default_factory=Assumptions)
    search: SearchSpec = Field(default_factory=SearchSpec)


def parse_input_data(data: Mapping[str, object]) -> InputSpec:
    """Validate a decoded TOML mapping into an :class:`InputSpec`."""
    return InputSpec.model_validate(data)


def parse_input_file(path: str) -> InputSpec:
    """Read and validate a TOML input file."""
    import tomllib
    from pathlib import Path

    return InputSpec.model_validate(tomllib.loads(Path(path).read_text(encoding="utf-8")))


def default_template() -> str:
    """A commented TOML template listing every assumption (with its description) + an example."""
    lines = [
        "# Geothermal Datathon — input file (TOML).",
        "# Uncomment and edit any value to override its default; omitted values use the default.",
        "",
        "[assumptions]",
    ]
    for name, info in Assumptions.model_fields.items():
        description = f"  # {info.description}" if info.description else ""
        lines.append(f"# {name} = {info.default!r}{description}")
    lines += [
        "",
        "# Optional: let the optimiser SEARCH ranges and honour constraints.",
        "# [search.ranges]",
        "# injection_temp_c = [25.0, 40.0]",
        "# heat_pump_cop = [4.0, 5.5]",
        "",
        "# [search.constraints]",
        "# max_capex_meur = 25.0",
        "# max_lcoe_eur_per_gj = 30.0",
        "",
        "# [search]",
        '# objective = "min_lcoe"   # or "min_capex" or "max_capacity"',
        "",
    ]
    return "\n".join(lines)
