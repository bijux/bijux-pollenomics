"""Governed held-out-site validation primitives, independent of the LRA engine.

Scores describe supplied observations; scientific acceptance additionally requires
frozen policy, reviewed independent targets and matched temporal/spatial support.
"""

from .baselines import BaselinePrediction, predict_spatial_baseline
from .contracts import Fold, SiteRecord, ValidationRefusal, manifest_sha256
from .metrics import CompositionScore, score_pollen, score_vegetation
from .policy import FrozenPolicy, validate_final_policy
from .splits import (
    assert_allowed_inputs,
    grouped_block_holdouts,
    grouped_leave_one_out,
    split_manifest,
)

__all__ = [
    "BaselinePrediction",
    "CompositionScore",
    "Fold",
    "FrozenPolicy",
    "SiteRecord",
    "ValidationRefusal",
    "assert_allowed_inputs",
    "grouped_block_holdouts",
    "grouped_leave_one_out",
    "manifest_sha256",
    "predict_spatial_baseline",
    "score_pollen",
    "score_vegetation",
    "split_manifest",
    "validate_final_policy",
]
