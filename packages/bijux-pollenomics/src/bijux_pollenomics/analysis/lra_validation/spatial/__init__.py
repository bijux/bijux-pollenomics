"""Explicit fitted spatial composition model, separate from LRA and baselines."""

from .configuration import SiteCoordinate, SpatialConfig
from .counts import HALF_COUNT, HALF_COUNT_POLICY, half_count_composition
from .identifiability import spatial_identifiability
from .model import FittedSpatialModel, SpatialPrediction, fit_spatial_model
from .uncertainty import (
    JointSpatialDraw,
    UnavailableSpatialDraw,
    propagate_withheld_spatial_draws,
)

__all__ = [
    "FittedSpatialModel",
    "JointSpatialDraw",
    "UnavailableSpatialDraw",
    "propagate_withheld_spatial_draws",
    "spatial_identifiability",
    "HALF_COUNT",
    "HALF_COUNT_POLICY",
    "SiteCoordinate",
    "SpatialConfig",
    "SpatialPrediction",
    "fit_spatial_model",
    "half_count_composition",
]
