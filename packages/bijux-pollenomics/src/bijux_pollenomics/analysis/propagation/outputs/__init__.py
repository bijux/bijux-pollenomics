"""Governed, deterministic propagation output materialization."""

from .models import (
    PROPAGATION_PRODUCER_ID,
    PROPAGATION_PRODUCER_SOURCE_PATHS,
    PROPAGATION_PRODUCER_VERSION,
    PropagationMaterializationResult,
    PropagationOutputRefusalError,
)
from .service import materialize_propagation_outputs

__all__ = [
    "PROPAGATION_PRODUCER_ID",
    "PROPAGATION_PRODUCER_SOURCE_PATHS",
    "PROPAGATION_PRODUCER_VERSION",
    "PropagationMaterializationResult",
    "PropagationOutputRefusalError",
    "materialize_propagation_outputs",
]
