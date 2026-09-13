"""Typed final-scoring and conditional uncertainty boundary."""

from ..experiments.reading.scores import read_scored_experiment_evidence
from .adapter import EvaluationAdapterAudit, audit_scored_evaluation_readiness
from .contracts import (
    AcceptanceCell,
    EvaluationPolicy,
    EvaluationResult,
    EvaluationRow,
    EvaluationScope,
    EvaluationSite,
    ExternalInput,
    PredictiveInterval,
    Support,
    freeze_evaluation_prediction,
)
from .policy import validate_evaluation_policy
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
    "Support",
    "evaluate_final",
    "freeze_evaluation_prediction",
    "resample_independent_units",
    "validate_evaluation_policy",
]
