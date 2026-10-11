"""Validate RAÄ map-publication posture without changing its authority."""

from __future__ import annotations

_RAA_CONTEXT_FIXED_POSTURE: dict[str, object] = {
    "key": "raa-archaeology",
    "group": "archaeology-context",
    "semantic_role": "archaeology_context",
    "contribution_role": "display_only",
    "default_enabled": True,
    "applies_country_filter": True,
    "applies_time_filter": False,
    "candidate_ranking_eligible": False,
    "scientific_classification_eligible": False,
    "scientific_selection_enabled": False,
    "propagation_status": "refused",
    "propagation_reason_code": "archaeology_context_only",
    "edge_count": 0,
}


def _raa_context_posture(
    layer: dict[str, object],
) -> dict[str, object] | None:
    """Preserve the RAÄ display/refusal boundary in publication contracts."""
    if layer.get("key") != "raa-archaeology":
        return None
    differing = sorted(
        field
        for field, expected in _RAA_CONTEXT_FIXED_POSTURE.items()
        if layer.get(field) != expected
    )
    if differing:
        raise ValueError("RAÄ context posture differs: " + ", ".join(differing))
    authority_status = layer.get("authority_status")
    admitted = layer.get("source_authority_admitted")
    retained_status = layer.get("retained_surface_status")
    if authority_status not in {"admitted", "degraded"}:
        raise ValueError("RAÄ context authority status differs")
    if admitted is not (authority_status == "admitted"):
        raise ValueError("RAÄ context authority admission differs")
    expected_retained_status = (
        "current_authority" if admitted else "retained_historical_context"
    )
    if retained_status != expected_retained_status:
        raise ValueError("RAÄ retained surface status differs")
    reason_codes = layer.get("authority_reason_codes")
    warning_codes = layer.get("display_warning_codes")
    if not isinstance(reason_codes, list) or any(
        not isinstance(value, str) or not value for value in reason_codes
    ):
        raise ValueError("RAÄ authority reason codes differ")
    if not isinstance(warning_codes, list) or any(
        not isinstance(value, str) or not value for value in warning_codes
    ):
        raise ValueError("RAÄ display warning codes differ")
    accounting = layer.get("density_count_accounting")
    if not isinstance(accounting, dict) or set(accounting) != {
        "status",
        "density_feature_count",
        "density_cell_count_sum",
        "metadata_fornlamning_count",
        "difference",
        "reconciled",
    }:
        raise ValueError("RAÄ density count accounting differs")
    for field in ("density_value_label", "density_count_label"):
        if not isinstance(layer.get(field), str) or not str(layer[field]).strip():
            raise ValueError(f"RAÄ {field} differs")
    return {
        **_RAA_CONTEXT_FIXED_POSTURE,
        "authority_status": authority_status,
        "source_authority_admitted": admitted,
        "authority_reason_codes": list(reason_codes),
        "display_warning_codes": list(warning_codes),
        "retained_surface_status": retained_status,
        "density_count_accounting": dict(accounting),
        "density_value_label": layer["density_value_label"],
        "density_count_label": layer["density_count_label"],
    }
