"""JSON Schema fixtures for propagation output contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from .model import MODEL_BYTES

EVENT_REQUIRED = (
    "schema_version",
    "event_id",
    "source_family",
    "evidence_domain",
    "source_snapshot_id",
    "source_record_id",
    "site_id",
    "observation_ids",
    "country_code",
    "latitude",
    "longitude",
    "coordinate_quality",
    "event_type",
    "resolution",
    "feature_key",
    "chronology_claim_id",
    "younger_bp",
    "older_bp",
    "comparability_status",
    "threshold_profile_id",
    "classification_contract_version",
    "provenance_record_id",
    "input_digest",
    "config_digest",
    "producer_version",
    "build_id",
)

CANDIDATE_REQUIRED = (
    "schema_version",
    "edge_id",
    "source_event_id",
    "target_event_id",
    "source_site_id",
    "target_site_id",
    "source_country_code",
    "target_country_code",
    "cross_border",
    "shared_location",
    "resolution",
    "feature_key",
    "distance_km_unrounded",
    "distance_km_display",
    "distance_algorithm",
    "distance_library",
    "distance_library_version",
    "minimum_lag_years",
    "maximum_lag_years",
    "candidate_status",
    "reason_code",
    "scenario_id",
    "threshold_profile_id",
    "temporal_contract_version",
    "classification_contract_version",
    "propagation_contract_version",
    "event_manifest_digest",
    "config_digest",
    "producer_version",
    "map_geometry_role",
    "directional_arrow_allowed",
    "route_interpretation_allowed",
    "build_id",
)


@pytest.fixture
def schema_root(tmp_path: Path) -> Path:
    """Materialize the event, candidate, and model contracts for one test."""
    root = tmp_path / "schemas"
    root.mkdir()
    event_properties: dict[str, object] = {field: {} for field in EVENT_REQUIRED}
    event_properties.update(
        {
            "schema_version": {"const": "1.0.0"},
            "event_id": {"type": "string", "minLength": 1},
            "evidence_domain": {
                "enum": [
                    "pollen_context",
                    "human_ancient_dna",
                    "animal_ancient_dna",
                ]
            },
            "observation_ids": {
                "type": "array",
                "minItems": 1,
                "uniqueItems": True,
                "items": {"type": "string", "minLength": 1},
            },
            "country_code": {"enum": ["SE", "DK", "NO", "FI"]},
            "latitude": {"type": "number", "minimum": -90, "maximum": 90},
            "longitude": {"type": "number", "minimum": -180, "maximum": 180},
            "coordinate_quality": {
                "enum": [
                    "exact",
                    "reported",
                    "approximate",
                    "centroid",
                    "unresolved",
                ]
            },
        }
    )
    event_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://bijux.io/schemas/pollenomics/phenomenon-event.v1.json",
        "type": "object",
        "additionalProperties": False,
        "required": list(EVENT_REQUIRED),
        "properties": event_properties,
    }
    candidate_properties: dict[str, object] = {
        field: {} for field in CANDIDATE_REQUIRED
    }
    candidate_properties.update(
        {
            "schema_version": {"const": "1.0.0"},
            "candidate_status": {
                "enum": [
                    "definite_candidate",
                    "possible_candidate",
                    "indeterminate_order",
                    "unresolved",
                    "excluded_spatial",
                    "excluded_temporal_nonpositive",
                    "excluded_temporal_too_large",
                ]
            },
            "distance_algorithm": {"const": "WGS84 inverse geodesic"},
            "map_geometry_role": {"const": "endpoint_connection_only"},
            "route_interpretation_allowed": {"const": False},
        }
    )
    candidate_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://bijux.io/schemas/pollenomics/propagation-candidate.v1.json",
        "type": "object",
        "additionalProperties": False,
        "required": list(CANDIDATE_REQUIRED),
        "properties": candidate_properties,
    }
    (root / "phenomenon-event.schema.json").write_text(
        json.dumps(event_schema), encoding="utf-8"
    )
    (root / "propagation-candidate.schema.json").write_text(
        json.dumps(candidate_schema), encoding="utf-8"
    )
    (root / "propagation-model.v1.yaml").write_bytes(MODEL_BYTES)
    return root
