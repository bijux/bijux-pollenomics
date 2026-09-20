"""Typed final-scoring and conditional uncertainty boundary."""

from ..experiments.reading.scores import read_scored_experiment_evidence
from .adapter import EvaluationAdapterAudit, audit_scored_evaluation_readiness
from .block_intervals import (
    AUTHENTICATED_BLOCK_CONDITIONAL_INTERVAL_PROFILE,
    freeze_authenticated_block_pollen_interval,
    freeze_authenticated_block_pollen_rows,
)
from .block_local_rows import adapt_authenticated_spatial_block_local_vegetation_rows
from .block_products import (
    adapt_authenticated_spatial_block_withheld_pollen_rows,
    adapt_authenticated_spatial_block_withheld_vegetation_rows,
)
from .contracts import (
    AcceptanceCell,
    EvaluationPolicy,
    EvaluationResult,
    EvaluationRow,
    EvaluationScope,
    EvaluationSite,
    ExternalInput,
    PredictiveInterval,
    SourceModelIdentity,
    Support,
    freeze_evaluation_prediction,
    validate_frozen_prediction,
)
from .intervals import (
    AUTHENTICATED_CONDITIONAL_INTERVAL_PROFILE,
    freeze_authenticated_pollen_interval,
)
from .policy import validate_evaluation_policy
from .release import (
    FINAL_EVALUATION_RELEASE_PROFILE,
    FinalEvaluationProtocol,
    FinalEvaluationReleaseAdmission,
    admit_final_evaluation_release,
)
from .resampling import resample_independent_units
from .scoring import evaluate_final

__all__ = [
    "read_scored_experiment_evidence",
    "EvaluationAdapterAudit",
    "audit_scored_evaluation_readiness",
    "AcceptanceCell",
    "EvaluationPolicy",
    "EvaluationResult",
    "EvaluationRow",
    "EvaluationScope",
    "EvaluationSite",
    "ExternalInput",
    "PredictiveInterval",
    "SourceModelIdentity",
    "Support",
    "evaluate_final",
    "freeze_evaluation_prediction",
    "validate_frozen_prediction",
    "resample_independent_units",
    "validate_evaluation_policy",
    "AUTHENTICATED_CONDITIONAL_INTERVAL_PROFILE",
    "freeze_authenticated_pollen_interval",
    "AUTHENTICATED_BLOCK_CONDITIONAL_INTERVAL_PROFILE",
    "freeze_authenticated_block_pollen_interval",
    "freeze_authenticated_block_pollen_rows",
    "adapt_authenticated_spatial_block_local_vegetation_rows",
    "adapt_authenticated_spatial_block_withheld_pollen_rows",
    "adapt_authenticated_spatial_block_withheld_vegetation_rows",
    "FINAL_EVALUATION_RELEASE_PROFILE",
    "FinalEvaluationProtocol",
    "FinalEvaluationReleaseAdmission",
    "admit_final_evaluation_release",
]
