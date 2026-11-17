"""Keep native registry cell counts separate from archaeological evidence admission."""

from __future__ import annotations

NATIVE_REGISTRY_POSTURE: dict[str, object] = {
    "key": "raa-native-registry-cells",
    "kind": "cell-counts",
    "group": "registry-context",
    "semantic_role": "native_registry_context",
    "contribution_role": "display_only",
    "default_enabled": False,
    "applies_country_filter": False,
    "applies_time_filter": False,
    "candidate_ranking_eligible": False,
    "scientific_classification_eligible": False,
    "scientific_selection_enabled": False,
    "source_authority_admitted": False,
    "country_assignment": "not_performed",
    "chronology": "unsupported",
    "propagation_status": "refused",
    "propagation_reason_code": "native_registry_context_only",
    "edge_count": 0,
}


def native_registry_posture(layer: dict[str, object]) -> dict[str, object] | None:
    """Reject promotion or conflation of a source-specific display-only layer."""
    if layer.get("key") != NATIVE_REGISTRY_POSTURE["key"]:
        return None
    if any(
        type(layer.get(key)) is not type(value) or layer.get(key) != value
        for key, value in NATIVE_REGISTRY_POSTURE.items()
    ):
        raise ValueError("Native registry context posture differs")
    return dict(NATIVE_REGISTRY_POSTURE)
