"""Canonical propagation network evaluation and reconciliation."""

from .evaluation import evaluate_propagation_pair
from .errors import EventValidationError
from .models import (
    COUNTRY_CODES,
    EDGE_SCHEMA_VERSION,
    EVIDENCE_DOMAINS,
    EVENT_SCHEMA_VERSION,
    NETWORK_PRODUCER_VERSION,
    PROPAGATION_CONTRACT_VERSION,
    TEMPORAL_CONTRACT_VERSION,
    PhenomenonEvent,
    PropagationCandidate,
    PropagationNetworkResult,
    PropagationPairRefusal,
    PropagationScenarioResult,
    ScenarioReconciliation,
)
from .scenarios import PROPAGATION_SENSITIVITY_SCENARIOS
from .service import (
    generate_propagation_network,
    generate_propagation_network_exhaustive,
    run_propagation_sensitivity,
)

__all__ = [
    "COUNTRY_CODES",
    "EDGE_SCHEMA_VERSION",
    "EVIDENCE_DOMAINS",
    "EVENT_SCHEMA_VERSION",
    "NETWORK_PRODUCER_VERSION",
    "PROPAGATION_CONTRACT_VERSION",
    "PROPAGATION_SENSITIVITY_SCENARIOS",
    "TEMPORAL_CONTRACT_VERSION",
    "EventValidationError",
    "PhenomenonEvent",
    "PropagationCandidate",
    "PropagationNetworkResult",
    "PropagationPairRefusal",
    "PropagationScenarioResult",
    "ScenarioReconciliation",
    "evaluate_propagation_pair",
    "generate_propagation_network",
    "generate_propagation_network_exhaustive",
    "run_propagation_sensitivity",
]
