"""Shared builders for propagation output contract tests."""

from __future__ import annotations
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest
from tests.support.repository import REPOSITORY_ROOT
from unittest.mock import patch
from bijux_pollenomics.analysis.propagation.network import PhenomenonEvent
from bijux_pollenomics.analysis.propagation.outputs import (
    PROPAGATION_PRODUCER_ID,
    PROPAGATION_PRODUCER_SOURCE_PATHS,
    PROPAGATION_PRODUCER_VERSION,
    PropagationMaterializationResult,
    materialize_propagation_outputs,
)
from bijux_pollenomics.analysis.propagation.outputs import (
    classification as propagation_classification,
)

_PROPAGATION_CONTRACT_VERSION = "1.0.0"

_REPOSITORY_ROOT = REPOSITORY_ROOT

_MODEL = {
    "schema_version": "1.0.0",
    "contract_id": "bijux-pollenomics.propagation-model",
    "contract_version": _PROPAGATION_CONTRACT_VERSION,
    "status": "normative",
    "scientific_claim": {
        "output_class": "candidate_propagation",
        "preferred_label": "candidate propagation link",
        "alternate_label": "spatiotemporal succession consistent with spread",
        "establishes_route": False,
        "establishes_causation": False,
        "establishes_human_migration": False,
        "establishes_plant_migration": False,
        "establishes_local_cultivation": False,
        "note": (
            "An edge is a versioned exploratory relation between evidence events, "
            "not a physical route or proof of a mechanism."
        ),
    },
    "geographic_scope": {
        "countries": ["SE", "NO", "FI", "DK"],
        "country_boundaries_partition_candidate_generation": False,
        "domestic_and_cross_border_rules_identical": True,
        "required_ordered_country_pair_reporting": [
            f"{source}-{target}"
            for source in ("SE", "NO", "FI", "DK")
            for target in ("SE", "NO", "FI", "DK")
        ],
    },
    "default_scenario": {
        "scenario_id": "rectangular_100km_100yr_v1",
        "spatial": {
            "maximum_distance_km": 100.0,
            "maximum_is_inclusive": True,
            "is_diameter": False,
        },
        "temporal": {
            "minimum_positive_lag_years": 0.0,
            "minimum_is_exclusive": True,
            "maximum_lag_years": 100.0,
            "maximum_is_inclusive": True,
            "direction": "older_event_to_younger_event",
        },
        "geometry": "rectangular_threshold",
        "rate_or_velocity_model": False,
        "biological_law": False,
    },
    "spatial_calculation": {
        "coordinate_reference_system": "EPSG:4326",
        "algorithm": "WGS84 inverse geodesic",
        "ellipsoid": "WGS84",
        "eligibility_distance_field": "distance_km_unrounded",
        "eligibility_value_rounding_allowed": False,
        "eligibility_uses_unrounded_value": True,
        "silent_algorithm_fallback_allowed": False,
    },
    "event_contract": {
        "allowed_evidence_domains": [
            "pollen_context",
            "human_ancient_dna",
            "animal_ancient_dna",
        ],
        "pollen_candidate_domain": "pollen_context",
        "non_pollen_domain_posture": (
            "retain as accounted input evidence but exclude from pollen candidate "
            "generation"
        ),
    },
    "candidate_logic": {
        "no_midpoint_shortcut": True,
        "same_point_age_directional": False,
    },
    "output_edge_contract": {
        "map_geometry": (
            "straight geodesic endpoint connection for visualization only"
        ),
        "route_interpretation_allowed": False,
    },
    "sensitivity_analysis": {
        "distance_km_values": [25.0, 50.0, 100.0, 200.0],
        "lag_year_values": [50.0, 100.0, 200.0, 500.0],
        "required_metrics": [
            "eligible_event_count",
            "evaluated_pair_count",
            "definite_candidate_count",
            "possible_candidate_count",
            "indeterminate_order_count",
            "unresolved_pair_count",
            "excluded_spatial_count",
            "excluded_temporal_count",
            "connected_component_count",
            "country_pair_counts",
            "feature_stability_across_scenarios",
        ],
    },
    "map_contract": {
        "merge_selected_features": False,
        "color_alone_is_sufficient": False,
    },
    "denominators": {
        "statuses_are_mutually_exclusive": True,
        "all_evaluated_pairs_must_be_accounted_for": True,
        "required_partitions": [
            "country_code",
            "ordered_country_pair",
            "source_family",
            "evidence_domain",
            "resolution",
            "feature_key",
            "candidate_status",
            "scenario_id",
            "threshold_profile_id",
        ],
    },
}

_MODEL_BYTES = json.dumps(_MODEL, sort_keys=True).encode()

_PROPAGATION_CONTRACT_DIGEST = hashlib.sha256(_MODEL_BYTES).hexdigest()

_PROPAGATION_PRODUCER_ID = PROPAGATION_PRODUCER_ID

_PROPAGATION_PRODUCER_VERSION = PROPAGATION_PRODUCER_VERSION

_EVENT_REQUIRED = (
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

_CANDIDATE_REQUIRED = (
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
    root = tmp_path / "schemas"
    root.mkdir()
    event_properties: dict[str, object] = {field: {} for field in _EVENT_REQUIRED}
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
        "required": list(_EVENT_REQUIRED),
        "properties": event_properties,
    }
    candidate_properties: dict[str, object] = {
        field: {} for field in _CANDIDATE_REQUIRED
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
        "required": list(_CANDIDATE_REQUIRED),
        "properties": candidate_properties,
    }
    (root / "phenomenon-event.schema.json").write_text(
        json.dumps(event_schema), encoding="utf-8"
    )
    (root / "propagation-candidate.schema.json").write_text(
        json.dumps(candidate_schema), encoding="utf-8"
    )
    (root / "propagation-model.v1.yaml").write_bytes(_MODEL_BYTES)
    return root


def _producer_digest() -> str:
    records = [
        {
            "path": relative_name,
            "sha256": hashlib.sha256(
                (_REPOSITORY_ROOT / relative_name).read_bytes()
            ).hexdigest(),
        }
        for relative_name in PROPAGATION_PRODUCER_SOURCE_PATHS
    ]
    return hashlib.sha256(
        json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


_PROPAGATION_PRODUCER_DIGEST = _producer_digest()


def _event(
    name: str,
    *,
    country_code: str = "SE",
    latitude: float = 55.605,
    longitude: float = 13.0038,
    age_bp: int = 5600,
) -> PhenomenonEvent:
    return PhenomenonEvent(
        source_family="source-native-fixture",
        evidence_domain="pollen_context",
        source_snapshot_id="snapshot-1",
        source_record_id=f"record-{name}",
        site_id=f"site-{name}",
        observation_ids=(f"observation-{name}",),
        country_code=country_code,
        latitude=latitude,
        longitude=longitude,
        coordinate_quality="reported",
        event_type="reported_positive_observation",
        resolution="taxon",
        feature_key="taxon:triticum_aestivum",
        chronology_claim_id=f"chronology-{name}",
        younger_bp=age_bp,
        older_bp=age_bp,
        comparability_status="comparable",
        threshold_profile_id="reported_positive_v1",
        classification_contract_version="classification.v1",
        provenance_record_id=f"provenance-{name}",
        input_digest=f"input-{name}",
        config_digest="event-config-v1",
        producer_version="fixture-producer.v1",
        build_id="build-1",
        measurement_semantics_id="presence.v1",
        evidence_method_id="source-native-method",
        method_compatibility_key="pollen-presence.v1",
        accepted_taxon_concept_id="accepted-taxon-1",
        taxonomic_qualifier="accepted",
    )


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode()


def _classification_bundle(parent: Path, accepted_count: int) -> tuple[Path, str]:
    root = parent / f"classification-evidence-{accepted_count}"
    root.mkdir(exist_ok=True)
    common = {
        "source_family": "source-native-fixture",
        "source_snapshot_id": "snapshot-1",
        "build_id": "build-1",
        "classification_contract_version": "classification.v1",
        "classification_contract_digest": f"sha256:{'1' * 64}",
        "classification_producer_id": "classification-fixture",
        "classification_producer_version": "1",
        "classification_producer_digest": f"sha256:{'2' * 64}",
    }
    accepted_records = [
        {
            "classification_concept_id": f"accepted-{index}",
            "mapping_status": "accepted",
            "mapping_version": "fixture-crosswalk.v1",
            "reviewer_id": "reviewer-fixture",
            "decision_date": "2026-09-04",
            "accepted_taxon_concept_id": f"taxon-{index}",
            "citation_reference_ids": ["citation-fixture"],
            "review_complete": True,
            "release_eligible": True,
        }
        for index in range(accepted_count)
    ]
    mapping_status_counts = {
        "accepted": accepted_count,
        "accepted_qualified": 0,
        "contested": 0,
        "not_applicable": 0,
        "refused": 0,
        "unmapped": 0,
    }
    payloads: dict[str, dict[str, object]] = {
        "accepted_mapping_queue.json": {
            "schema_version": "classification-accepted-mapping-queue.v1",
            **common,
            "record_count": accepted_count,
            "records": accepted_records,
        },
        "concept_denominators.json": {
            "schema_version": "classification-concept-denominators.v1",
            **common,
            "record_count": accepted_count,
            "total_concept_count": accepted_count,
            "mapping_status_counts": mapping_status_counts,
            "accepted_queue_count": accepted_count,
            "unmapped_queue_count": 0,
            "not_applicable_queue_count": 0,
            "review_queue_count": 0,
        },
        "country_partitions.json": {
            "schema_version": "classification-country-partitions.v1",
            **common,
            "record_count": 0,
            "source_country": [],
            "governed_country": [],
            "country_relation": [],
        },
        "not_applicable_mapping_queue.json": {
            "schema_version": "classification-not-applicable-mapping-queue.v1",
            **common,
            "record_count": 0,
            "records": [],
        },
        "observation_denominators.json": {
            "schema_version": "classification-observation-denominators.v1",
            **common,
            "record_count": 0,
            "total_observation_count": 0,
            "mapping_status_counts": dict.fromkeys(mapping_status_counts, 0),
        },
        "observation_memberships.json": {
            "schema_version": "classification-observation-memberships.v1",
            **common,
            "record_count": 0,
            "records": [],
        },
        "release_metadata.json": {
            "schema_version": "classification-release-metadata.v1",
            **common,
            "accepted_mapping_count": accepted_count,
            "reviewed_accepted_mapping_count": accepted_count,
            "release_eligible_mapping_count": accepted_count,
            "unmapped_mapping_count": 0,
            "not_applicable_mapping_count": 0,
            "human_approval_synthesized": False,
            "record_count": 1,
        },
        "review_queue.json": {
            "schema_version": "classification-review-queue.v1",
            **common,
            "record_count": 0,
            "records": [],
        },
        "unmapped_mapping_queue.json": {
            "schema_version": "classification-unmapped-mapping-queue.v1",
            **common,
            "record_count": 0,
            "records": [],
        },
    }
    serialized = {
        name: _canonical_json_bytes(payload) for name, payload in payloads.items()
    }
    entries = [
        {
            "path": name,
            "sha256": hashlib.sha256(serialized[name]).hexdigest(),
            "record_count": payloads[name]["record_count"],
        }
        for name in sorted(serialized)
    ]
    digest_input = "".join(
        f"{entry['path']}\0{entry['sha256']}\0{entry['record_count']}\n"
        for entry in entries
    ).encode()
    manifest = {
        "schema_version": "classification-audit-manifest.v1",
        **common,
        "bundle_digest": hashlib.sha256(digest_input).hexdigest(),
        "payload_file_count": len(entries),
        "files": entries,
    }
    for name, value in serialized.items():
        (root / name).write_bytes(value)
    manifest_bytes = _canonical_json_bytes(manifest)
    (root / "manifest.json").write_bytes(manifest_bytes)
    return root, hashlib.sha256(manifest_bytes).hexdigest()


def _rehash_classification_bundle(root: Path) -> str:
    manifest_path = root / "manifest.json"
    manifest = _read_json(manifest_path)
    entries = manifest["files"]
    assert isinstance(entries, list)
    for entry in entries:
        assert isinstance(entry, dict)
        payload_path = root / str(entry["path"])
        payload = _read_json(payload_path)
        payload_bytes = _canonical_json_bytes(payload)
        payload_path.write_bytes(payload_bytes)
        entry["sha256"] = hashlib.sha256(payload_bytes).hexdigest()
        entry["record_count"] = payload["record_count"]
    manifest["bundle_digest"] = hashlib.sha256(
        "".join(
            f"{entry['path']}\0{entry['sha256']}\0{entry['record_count']}\n"
            for entry in entries
        ).encode()
    ).hexdigest()
    manifest_bytes = _canonical_json_bytes(manifest)
    manifest_path.write_bytes(manifest_bytes)
    return hashlib.sha256(manifest_bytes).hexdigest()


def _materialize(
    *,
    output_root: Path,
    allowed_output_parent: Path,
    schema_root: Path,
    classification_bundle_root: Path | None = None,
    classification_review_digest: str | None = None,
    events: tuple[PhenomenonEvent, ...] = (),
    accepted_mapping_count: int = 0,
    build_id: str = "build-1",
    classification_contract_version: str = "classification.v1",
    propagation_contract_version: str = _PROPAGATION_CONTRACT_VERSION,
    propagation_contract_digest: str = _PROPAGATION_CONTRACT_DIGEST,
    propagation_contract_path: Path | None = None,
    propagation_producer_id: str = _PROPAGATION_PRODUCER_ID,
    propagation_producer_version: str = _PROPAGATION_PRODUCER_VERSION,
    propagation_producer_digest: str | None = None,
    repository_root: Path = _REPOSITORY_ROOT,
    use_product_classification_authority: bool = False,
) -> PropagationMaterializationResult:
    if classification_bundle_root is None:
        classification_bundle_root, observed_review_digest = _classification_bundle(
            allowed_output_parent,
            accepted_mapping_count,
        )
    else:
        observed_review_digest = hashlib.sha256(
            (classification_bundle_root / "manifest.json").read_bytes()
        ).hexdigest()
    if classification_review_digest is None:
        classification_review_digest = observed_review_digest
    if propagation_producer_digest is None:
        propagation_producer_digest = _producer_digest()
    if propagation_contract_path is None:
        propagation_contract_path = schema_root / "propagation-model.v1.yaml"
    manifest = _read_json(classification_bundle_root / "manifest.json")
    release = _read_json(classification_bundle_root / "release_metadata.json")
    authority_accepted_count = release["accepted_mapping_count"]
    assert isinstance(authority_accepted_count, int)
    test_authority = replace(
        propagation_classification._CLASSIFICATION_AUTHORITY,
        manifest_sha256=observed_review_digest,
        source_family=str(manifest["source_family"]),
        source_snapshot_id=str(manifest["source_snapshot_id"]),
        build_id=str(manifest["build_id"]),
        contract_version=str(manifest["classification_contract_version"]),
        contract_digest=str(manifest["classification_contract_digest"]),
        producer_id=str(manifest["classification_producer_id"]),
        producer_version=str(manifest["classification_producer_version"]),
        producer_digest=str(manifest["classification_producer_digest"]),
        accepted_mapping_count=authority_accepted_count,
    )

    def invoke() -> PropagationMaterializationResult:
        return materialize_propagation_outputs(
            events,
            output_root=output_root,
            allowed_output_parent=allowed_output_parent,
            schema_root=schema_root,
            classification_bundle_root=classification_bundle_root,
            propagation_contract_path=propagation_contract_path,
            repository_root=repository_root,
            build_id=build_id,
            classification_contract_version=classification_contract_version,
            classification_review_digest=classification_review_digest,
            accepted_classification_mapping_count=accepted_mapping_count,
            propagation_contract_version=propagation_contract_version,
            propagation_contract_digest=propagation_contract_digest,
            propagation_producer_id=propagation_producer_id,
            propagation_producer_version=propagation_producer_version,
            propagation_producer_digest=propagation_producer_digest,
        )

    if use_product_classification_authority:
        return invoke()
    with patch.object(
        propagation_classification, "_CLASSIFICATION_AUTHORITY", test_authority
    ):
        return invoke()


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value
