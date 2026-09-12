"""Synthetic train-only reconstruction experiments with separate outcome access."""

from .configuration import ExperimentSpec
from .outputs import ExperimentProduct, read_experiment_product
from .scoring import score_experiment_predictions
from .workflow import prepare_experiment_predictions

__all__ = [
    "ExperimentSpec",
    "ExperimentProduct",
    "read_experiment_product",
    "prepare_experiment_predictions",
    "score_experiment_predictions",
]
