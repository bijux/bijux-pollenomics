"""Governed identities for source-native chronology nodes."""

from __future__ import annotations

import hashlib
import json

COUNTRY_CODES = ("SE", "DK", "NO", "FI")
NODE_PRODUCER_VERSION = "neotoma-source-chronology-nodes.v2"
NODE_LEVELS = (
    "source_sample_presence",
    "source_ecological_code",
    "source_taxon",
)


def source_node_config_payload() -> dict[str, object]:
    """Return a fresh canonical payload for the fixed derivation policy."""
    return {
        "schema_version": "neotoma-source-chronology-config.v2",
        "source_family": "neotoma",
        "source_element_type": "pollen",
        "countries": list(COUNTRY_CODES),
        "chronology_admission": {
            "preferred": "exactly-one-source-default-comparable-canonical-bp",
            "fallback": "exactly-one-nondefault-comparable-canonical-bp",
            "ambiguous_fallback": "refused",
        },
        "observation_admission": "reported-finite-positive-value-only",
        "node_levels": list(NODE_LEVELS),
        "node_order": "older-bp-desc-younger-bp-desc-node-id",
        "propagation_eligible": False,
        "candidate_refusal_by_level": {
            "source_sample_presence": "reviewed_pollen_sum_not_available",
            "source_ecological_code": "source_ecological_equivalence_not_reviewed",
            "source_taxon": "source_taxon_equivalence_not_reviewed",
        },
    }


SOURCE_NODE_CONFIG_DIGEST = (
    "sha256:"
    + hashlib.sha256(
        json.dumps(
            source_node_config_payload(), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
)

__all__ = [
    "COUNTRY_CODES",
    "NODE_LEVELS",
    "NODE_PRODUCER_VERSION",
    "SOURCE_NODE_CONFIG_DIGEST",
    "source_node_config_payload",
]
