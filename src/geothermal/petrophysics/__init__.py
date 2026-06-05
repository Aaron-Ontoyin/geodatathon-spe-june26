"""Phase 1 — the data foundation.

Reconciles along-hole and true-vertical depth (directional surveys, minimum
curvature) and fills missing reservoir properties (ML imputation), producing a
clean, TVD-correct, gap-filled per-sample reservoir dataset for resource work.
"""

from geothermal.petrophysics.imputation import (
    add_permeability,
    density_porosity,
    impute_porosity,
    imputed_vs_thermogis,
    porosity_cross_well_skill,
    porosity_log_quality,
)
from geothermal.petrophysics.reservoir import (
    build_reservoir_table,
    build_well_reservoir,
    infer_orientation,
)
from geothermal.petrophysics.survey import (
    DeviationSurvey,
    SurveyPath,
    minimum_curvature,
    survey_tvd_residual_m,
)

__all__ = [
    "DeviationSurvey",
    "SurveyPath",
    "add_permeability",
    "build_reservoir_table",
    "build_well_reservoir",
    "density_porosity",
    "impute_porosity",
    "imputed_vs_thermogis",
    "infer_orientation",
    "minimum_curvature",
    "porosity_cross_well_skill",
    "porosity_log_quality",
    "survey_tvd_residual_m",
]
