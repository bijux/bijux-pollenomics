from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from bijux_pollenomics.analysis import propagation_outputs as propagation_outputs_module
from bijux_pollenomics.analysis.propagation_network import PhenomenonEvent
from bijux_pollenomics.analysis.propagation_outputs import (
    PROPAGATION_PRODUCER_ID,
    PROPAGATION_PRODUCER_SOURCE_PATHS,
    PROPAGATION_PRODUCER_VERSION,
    PropagationMaterializationResult,
    PropagationOutputRefusalError,
    materialize_propagation_outputs,
)

_PROPAGATION_CONTRACT_VERSION = "1.0.0"
_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
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
                "enum": ["exact", "reported", "approximate", "centroid", "unresolved"]
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
        propagation_outputs_module._CLASSIFICATION_AUTHORITY,
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
        propagation_outputs_module, "_CLASSIFICATION_AUTHORITY", test_authority
    ):
        return invoke()


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_zero_accepted_mapping_universe_materializes_a_truthful_refusal(
    tmp_path: Path, schema_root: Path
) -> None:
    output_root = tmp_path / "propagation"

    created = _materialize(
        output_root=output_root,
        allowed_output_parent=tmp_path,
        schema_root=schema_root,
    )
    unchanged = _materialize(
        output_root=output_root,
        allowed_output_parent=tmp_path,
        schema_root=schema_root,
    )

    release = _read_json(output_root / "release_metadata.json")
    events = _read_json(output_root / "phenomenon_events.json")
    primary = _read_json(output_root / "primary_scenario_candidates.json")
    reconciliation = _read_json(output_root / "primary_scenario_reconciliation.json")
    sensitivity = _read_json(output_root / "sensitivity_summary.json")
    manifest = _read_json(output_root / "manifest.json")
    assert created.disposition == "created"
    assert unchanged.disposition == "unchanged"
    assert created.manifest_sha256 == unchanged.manifest_sha256
    assert created.file_count == 8
    assert created.eligible_event_count == 0
    assert created.excluded_non_pollen_event_count == 0
    assert events["record_count"] == 0
    assert primary["record_count"] == 0
    assert primary["directed_candidate_count"] == 0
    assert sensitivity["record_count"] == 16
    scenarios = sensitivity["scenarios"]
    assert isinstance(scenarios, list)
    assert all(
        isinstance(scenario, dict)
        and scenario["eligible_event_count"] == 0
        and scenario["excluded_temporal_count"] == 0
        and scenario["country_pair_counts"] == scenario["ordered_country_pair_counts"]
        for scenario in scenarios
    )
    assert sensitivity["feature_stability_across_scenarios"] == []
    reconciliation_record = reconciliation["reconciliation"]
    assert isinstance(reconciliation_record, dict)
    denominator_partitions = reconciliation_record["denominator_partitions"]
    assert isinstance(denominator_partitions, dict)
    assert set(denominator_partitions) == {
        "country_code",
        "ordered_country_pair",
        "source_family",
        "evidence_domain",
        "resolution",
        "feature_key",
        "candidate_status",
        "scenario_id",
        "threshold_profile_id",
    }
    assert all(
        partition["total_count"] == sum(partition["counts"].values())
        for partition in denominator_partitions.values()
    )
    assert denominator_partitions["country_code"]["counts"] == {
        "DK": 0,
        "FI": 0,
        "NO": 0,
        "SE": 0,
    }
    assert denominator_partitions["evidence_domain"]["counts"] == {
        "animal_ancient_dna": 0,
        "human_ancient_dna": 0,
        "pollen_context": 0,
    }
    assert release["release_status"] == "refused"
    assert release["public_release_allowed"] is False
    assert release["reason_codes"] == ["no_accepted_classification_mappings"]
    assert release["accepted_classification_mapping_count"] == 0
    assert release["candidate_materialization_status"] == "empty_refused"
    assert release["schema_version"] == "propagation-release-metadata.v2"
    assert manifest["schema_version"] == "propagation-output-manifest.v2"
    for payload in (sensitivity, release, manifest):
        assert payload["build_id"] == "build-1"
        assert payload["event_manifest_digest"] == events["event_manifest_digest"]
        assert payload["classification_contract_version"] == "classification.v1"
        assert (
            payload["classification_review_digest"]
            == (release["classification_review_digest"])
        )
        assert payload["accepted_classification_mapping_count"] == 0
        assert payload["propagation_contract_version"] == (
            _PROPAGATION_CONTRACT_VERSION
        )
        assert payload["propagation_contract_digest"] == (_PROPAGATION_CONTRACT_DIGEST)
        assert payload["propagation_producer_id"] == _PROPAGATION_PRODUCER_ID
        assert payload["propagation_producer_version"] == (
            _PROPAGATION_PRODUCER_VERSION
        )
        assert payload["propagation_producer_digest"] == _producer_digest()


def test_manifest_hashes_and_counts_every_payload_file(
    tmp_path: Path, schema_root: Path
) -> None:
    output_root = tmp_path / "propagation"
    _materialize(
        output_root=output_root,
        allowed_output_parent=tmp_path,
        schema_root=schema_root,
    )

    manifest = _read_json(output_root / "manifest.json")
    entries = manifest["files"]
    assert isinstance(entries, list)
    assert manifest["payload_file_count"] == 7
    assert [entry["path"] for entry in entries] == sorted(
        entry["path"] for entry in entries
    )
    for entry in entries:
        payload_bytes = (output_root / entry["path"]).read_bytes()
        payload = json.loads(payload_bytes)
        assert hashlib.sha256(payload_bytes).hexdigest() == entry["sha256"]
        assert payload["record_count"] == entry["record_count"]


def test_sensitivity_summary_has_content_bound_standalone_lineage(
    tmp_path: Path, schema_root: Path
) -> None:
    output_root = tmp_path / "propagation"
    _materialize(
        output_root=output_root,
        allowed_output_parent=tmp_path,
        schema_root=schema_root,
    )
    sensitivity = _read_json(output_root / "sensitivity_summary.json")
    release = _read_json(output_root / "release_metadata.json")
    manifest = _read_json(output_root / "manifest.json")
    lineage_fields = {
        "build_id",
        "event_manifest_digest",
        "classification_contract_version",
        "classification_review_digest",
        "accepted_classification_mapping_count",
        "propagation_contract_version",
        "propagation_contract_digest",
        "propagation_producer_id",
        "propagation_producer_version",
        "propagation_producer_digest",
    }

    for field_name in lineage_fields:
        assert sensitivity[field_name] == release[field_name] == manifest[field_name]
    entries = manifest["files"]
    assert isinstance(entries, list)
    sensitivity_entry = next(
        entry
        for entry in entries
        if isinstance(entry, dict) and entry.get("path") == "sensitivity_summary.json"
    )
    sensitivity_bytes = (output_root / "sensitivity_summary.json").read_bytes()
    assert sensitivity_entry["sha256"] == hashlib.sha256(sensitivity_bytes).hexdigest()
    assert sensitivity_entry["record_count"] == sensitivity["record_count"] == 16


@pytest.mark.parametrize(
    ("artifact_name", "field_name", "invalid_value"),
    (
        ("sensitivity_summary.json", "accepted_classification_mapping_count", True),
        ("sensitivity_summary.json", "propagation_contract_digest", "A" * 64),
        ("sensitivity_summary.json", "propagation_producer_id", 1),
        ("release_metadata.json", "event_manifest_digest", "0" * 64),
        ("manifest.json", "classification_review_digest", "0" * 64),
        ("manifest.json", "build_id", 1),
    ),
)
def test_scenario_lineage_runtime_types_and_consistency_fail_closed(
    tmp_path: Path,
    schema_root: Path,
    artifact_name: str,
    field_name: str,
    invalid_value: object,
) -> None:
    output_root = tmp_path / "propagation"
    _materialize(
        output_root=output_root,
        allowed_output_parent=tmp_path,
        schema_root=schema_root,
    )
    serialized_payloads = {
        name: (output_root / name).read_bytes()
        for name in propagation_outputs_module._OUTPUT_NAMES
    }
    manifest = _read_json(output_root / "manifest.json")
    if artifact_name == "manifest.json":
        manifest[field_name] = invalid_value
    else:
        artifact = _read_json(output_root / artifact_name)
        artifact[field_name] = invalid_value
        serialized_payloads[artifact_name] = _canonical_json_bytes(artifact)
    release = _read_json(output_root / "release_metadata.json")
    event_manifest_digest = release["event_manifest_digest"]
    classification_review_digest = release["classification_review_digest"]
    assert isinstance(event_manifest_digest, str)
    assert isinstance(classification_review_digest, str)

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        propagation_outputs_module._validate_scenario_artifact_lineage(
            serialized_payloads=serialized_payloads,
            manifest=manifest,
            build_id="build-1",
            event_manifest_digest=event_manifest_digest,
            classification_contract_version="classification.v1",
            classification_review_digest=classification_review_digest,
            accepted_classification_mapping_count=0,
            propagation_contract_version=_PROPAGATION_CONTRACT_VERSION,
            propagation_contract_digest=_PROPAGATION_CONTRACT_DIGEST,
            propagation_producer_id=_PROPAGATION_PRODUCER_ID,
            propagation_producer_version=_PROPAGATION_PRODUCER_VERSION,
            propagation_producer_digest=_producer_digest(),
        )

    assert refusal.value.reason_code == "invalid_scenario_artifact_lineage"


def test_sensitivity_content_tampering_fails_manifest_binding(
    tmp_path: Path, schema_root: Path
) -> None:
    output_root = tmp_path / "propagation"
    _materialize(
        output_root=output_root,
        allowed_output_parent=tmp_path,
        schema_root=schema_root,
    )
    serialized_payloads = {
        name: (output_root / name).read_bytes()
        for name in propagation_outputs_module._OUTPUT_NAMES
    }
    sensitivity = _read_json(output_root / "sensitivity_summary.json")
    sensitivity["feature_stability_across_scenarios"] = [{"tampered": True}]
    serialized_payloads["sensitivity_summary.json"] = _canonical_json_bytes(sensitivity)
    manifest = _read_json(output_root / "manifest.json")
    release = _read_json(output_root / "release_metadata.json")
    event_manifest_digest = release["event_manifest_digest"]
    classification_review_digest = release["classification_review_digest"]
    assert isinstance(event_manifest_digest, str)
    assert isinstance(classification_review_digest, str)

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        propagation_outputs_module._validate_scenario_artifact_lineage(
            serialized_payloads=serialized_payloads,
            manifest=manifest,
            build_id="build-1",
            event_manifest_digest=event_manifest_digest,
            classification_contract_version="classification.v1",
            classification_review_digest=classification_review_digest,
            accepted_classification_mapping_count=0,
            propagation_contract_version=_PROPAGATION_CONTRACT_VERSION,
            propagation_contract_digest=_PROPAGATION_CONTRACT_DIGEST,
            propagation_producer_id=_PROPAGATION_PRODUCER_ID,
            propagation_producer_version=_PROPAGATION_PRODUCER_VERSION,
            propagation_producer_digest=_producer_digest(),
        )

    assert refusal.value.reason_code == "invalid_scenario_artifact_lineage"


def test_primary_and_sensitivity_outputs_are_content_deterministic(
    tmp_path: Path, schema_root: Path
) -> None:
    events = (
        _event("malmo"),
        _event(
            "lund",
            latitude=55.7047,
            longitude=13.191,
            age_bp=5500,
        ),
    )
    first = tmp_path / "first"
    second = tmp_path / "second"

    first_result = _materialize(
        output_root=first,
        allowed_output_parent=tmp_path,
        schema_root=schema_root,
        events=events,
        accepted_mapping_count=1,
    )
    second_result = _materialize(
        output_root=second,
        allowed_output_parent=tmp_path,
        schema_root=schema_root,
        events=tuple(reversed(events)),
        accepted_mapping_count=1,
    )

    assert first_result.manifest_sha256 == second_result.manifest_sha256
    assert first_result.primary_directed_candidate_count == 1
    assert {
        path.name: path.read_bytes() for path in first.iterdir() if path.is_file()
    } == {path.name: path.read_bytes() for path in second.iterdir() if path.is_file()}
    events_payload = _read_json(first / "phenomenon_events.json")
    candidates = _read_json(first / "primary_scenario_candidates.json")
    assert events_payload["record_count"] == 2
    event_records = events_payload["records"]
    assert isinstance(event_records, list)
    assert all(
        isinstance(row, dict) and row["evidence_domain"] == "pollen_context"
        for row in event_records
    )
    assert events_payload["evaluation_metadata_record_count"] == 2
    evaluation_metadata = events_payload["evaluation_metadata"]
    assert isinstance(evaluation_metadata, list)
    assert all(
        isinstance(row, dict) and row["measurement_semantics_id"] == "presence.v1"
        for row in evaluation_metadata
    )
    assert candidates["record_count"] == 2
    assert candidates["directed_candidate_count"] == 1
    sensitivity = _read_json(first / "sensitivity_summary.json")
    stability = sensitivity["feature_stability_across_scenarios"]
    assert isinstance(stability, list)
    assert len(stability) == 1
    assert isinstance(stability[0], dict)
    assert stability[0]["feature_key"] == "taxon:triticum_aestivum"
    assert stability[0]["scenario_count"] == 16
    assert len(stability[0]["scenario_status_counts"]) == 16
    sensitivity_scenarios = sensitivity["scenarios"]
    assert isinstance(sensitivity_scenarios, list)
    for scenario in sensitivity_scenarios:
        assert isinstance(scenario, dict)
        assert scenario["excluded_temporal_count"] == (
            scenario["excluded_temporal_nonpositive_count"]
            + scenario["excluded_temporal_too_large_count"]
        )
        assert (
            scenario["country_pair_counts"] == (scenario["ordered_country_pair_counts"])
        )
        partitions = scenario["denominator_partitions"]
        assert partitions["scenario_id"]["counts"] == {
            scenario["scenario_id"]: (
                scenario["evaluated_pair_count"] + scenario["refused_pair_count"]
            )
        }


def test_materialization_preserves_non_pollen_exclusion_records(
    tmp_path: Path, schema_root: Path
) -> None:
    pollen = _event("pollen")
    animal = replace(
        pollen,
        evidence_domain="animal_ancient_dna",
        source_record_id="animal-record",
        site_id="animal-site",
        event_id="",
    )
    output_root = tmp_path / "propagation"

    result = _materialize(
        output_root=output_root,
        allowed_output_parent=tmp_path,
        schema_root=schema_root,
        events=(pollen, animal),
        accepted_mapping_count=1,
    )

    exclusions = _read_json(output_root / "excluded_non_pollen_events.json")
    release = _read_json(output_root / "release_metadata.json")
    reconciliation = _read_json(output_root / "primary_scenario_reconciliation.json")
    assert result.eligible_event_count == 1
    assert result.excluded_non_pollen_event_count == 1
    assert exclusions["record_count"] == 1
    exclusion_records = exclusions["records"]
    assert isinstance(exclusion_records, list)
    assert exclusion_records[0]["reason_code"] == (
        "evidence_domain_not_pollen_propagation_eligible"
    )
    assert exclusion_records[0]["event"]["event_id"] == animal.event_id
    assert exclusion_records[0]["event"]["evidence_domain"] == ("animal_ancient_dna")
    assert release["input_event_count"] == 2
    assert release["eligible_event_count"] == 1
    assert release["excluded_non_pollen_event_count"] == 1
    reconciliation_record = reconciliation["reconciliation"]
    assert isinstance(reconciliation_record, dict)
    partitions = reconciliation_record["denominator_partitions"]
    assert partitions["evidence_domain"]["counts"] == {
        "animal_ancient_dna": 1,
        "human_ancient_dna": 0,
        "pollen_context": 1,
    }
    assert partitions["source_family"]["total_count"] == 2
    assert partitions["resolution"]["counts"] == {"taxon": 2}
    assert partitions["feature_key"]["counts"] == {"taxon:triticum_aestivum": 2}


@pytest.mark.parametrize(
    (
        "contract_version",
        "contract_digest",
        "producer_id",
        "producer_version",
        "producer_digest",
        "reason_code",
    ),
    (
        (
            "",
            _PROPAGATION_CONTRACT_DIGEST,
            _PROPAGATION_PRODUCER_ID,
            _PROPAGATION_PRODUCER_VERSION,
            _PROPAGATION_PRODUCER_DIGEST,
            "invalid_build_identity",
        ),
        (
            "2.0.0",
            _PROPAGATION_CONTRACT_DIGEST,
            _PROPAGATION_PRODUCER_ID,
            _PROPAGATION_PRODUCER_VERSION,
            _PROPAGATION_PRODUCER_DIGEST,
            "invalid_propagation_identity",
        ),
        (
            _PROPAGATION_CONTRACT_VERSION,
            "not-a-digest",
            _PROPAGATION_PRODUCER_ID,
            _PROPAGATION_PRODUCER_VERSION,
            _PROPAGATION_PRODUCER_DIGEST,
            "invalid_build_identity",
        ),
        (
            _PROPAGATION_CONTRACT_VERSION,
            _PROPAGATION_CONTRACT_DIGEST,
            "",
            _PROPAGATION_PRODUCER_VERSION,
            _PROPAGATION_PRODUCER_DIGEST,
            "invalid_build_identity",
        ),
        (
            _PROPAGATION_CONTRACT_VERSION,
            _PROPAGATION_CONTRACT_DIGEST,
            _PROPAGATION_PRODUCER_ID,
            "",
            _PROPAGATION_PRODUCER_DIGEST,
            "invalid_build_identity",
        ),
        (
            _PROPAGATION_CONTRACT_VERSION,
            _PROPAGATION_CONTRACT_DIGEST,
            _PROPAGATION_PRODUCER_ID,
            _PROPAGATION_PRODUCER_VERSION,
            "A" * 64,
            "invalid_build_identity",
        ),
    ),
)
def test_missing_or_invalid_propagation_identity_is_refused_before_publication(
    tmp_path: Path,
    schema_root: Path,
    contract_version: str,
    contract_digest: str,
    producer_id: str,
    producer_version: str,
    producer_digest: str,
    reason_code: str,
) -> None:
    output_root = tmp_path / "propagation"

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=output_root,
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            propagation_contract_version=contract_version,
            propagation_contract_digest=contract_digest,
            propagation_producer_id=producer_id,
            propagation_producer_version=producer_version,
            propagation_producer_digest=producer_digest,
        )

    assert refusal.value.reason_code == reason_code
    assert not output_root.exists()


def test_changed_propagation_identity_refuses_existing_bundle_without_modification(
    tmp_path: Path, schema_root: Path
) -> None:
    output_root = tmp_path / "propagation"
    _materialize(
        output_root=output_root,
        allowed_output_parent=tmp_path,
        schema_root=schema_root,
    )
    original_manifest = (output_root / "manifest.json").read_bytes()
    original_release = (output_root / "release_metadata.json").read_bytes()

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=output_root,
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            propagation_producer_digest=hashlib.sha256(
                b"different-propagation-producer"
            ).hexdigest(),
        )

    assert refusal.value.reason_code == "invalid_propagation_identity"
    assert (output_root / "manifest.json").read_bytes() == original_manifest
    assert (output_root / "release_metadata.json").read_bytes() == original_release


def test_classification_identity_is_bound_to_manifested_bytes_and_counts(
    tmp_path: Path, schema_root: Path
) -> None:
    classification_root, classification_digest = _classification_bundle(tmp_path, 0)
    release_path = classification_root / "release_metadata.json"
    release_path.write_bytes(release_path.read_bytes() + b" ")

    with pytest.raises(PropagationOutputRefusalError) as changed_bytes:
        _materialize(
            output_root=tmp_path / "changed-bytes",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            classification_bundle_root=classification_root,
            classification_review_digest=classification_digest,
        )
    assert changed_bytes.value.reason_code == "invalid_classification_identity"

    classification_root, classification_digest = _classification_bundle(tmp_path, 0)
    with pytest.raises(PropagationOutputRefusalError) as changed_count:
        _materialize(
            output_root=tmp_path / "changed-count",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            classification_bundle_root=classification_root,
            classification_review_digest=classification_digest,
            accepted_mapping_count=1,
        )
    assert changed_count.value.reason_code == "invalid_classification_reconciliation"

    release_path = classification_root / "release_metadata.json"
    release = _read_json(release_path)
    release["accepted_mapping_count"] = 1
    release_path.write_bytes(_canonical_json_bytes(release))
    manifest_path = classification_root / "manifest.json"
    manifest = _read_json(manifest_path)
    entries = manifest["files"]
    assert isinstance(entries, list)
    for entry in entries:
        assert isinstance(entry, dict)
        if entry["path"] == "release_metadata.json":
            entry["sha256"] = hashlib.sha256(release_path.read_bytes()).hexdigest()
    manifest["bundle_digest"] = hashlib.sha256(
        "".join(
            f"{entry['path']}\0{entry['sha256']}\0{entry['record_count']}\n"
            for entry in entries
        ).encode()
    ).hexdigest()
    manifest_path.write_bytes(_canonical_json_bytes(manifest))
    rehashed_digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    with pytest.raises(PropagationOutputRefusalError) as rehashed_release:
        _materialize(
            output_root=tmp_path / "rehashed-release",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            classification_bundle_root=classification_root,
            classification_review_digest=rehashed_digest,
            accepted_mapping_count=1,
        )
    assert rehashed_release.value.reason_code == "invalid_classification_reconciliation"


@pytest.mark.parametrize(
    ("payload_name", "mutation"),
    (
        (
            "accepted_mapping_queue.json",
            lambda payload: payload.update(record_count=1),
        ),
        (
            "release_metadata.json",
            lambda payload: payload.update(human_approval_synthesized=True),
        ),
        (
            "concept_denominators.json",
            lambda payload: payload["mapping_status_counts"].update(unmapped=1),
        ),
    ),
)
def test_coherently_rehashed_classification_accounting_mutations_are_refused(
    tmp_path: Path,
    schema_root: Path,
    payload_name: str,
    mutation: object,
) -> None:
    classification_root, _ = _classification_bundle(tmp_path, 0)
    payload_path = classification_root / payload_name
    payload = _read_json(payload_path)
    assert callable(mutation)
    mutation(payload)
    payload_path.write_bytes(_canonical_json_bytes(payload))
    digest = _rehash_classification_bundle(classification_root)

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=tmp_path / f"refused-{payload_name}",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            classification_bundle_root=classification_root,
            classification_review_digest=digest,
        )

    assert refusal.value.reason_code == "invalid_classification_reconciliation"


@pytest.mark.parametrize(
    "mutation",
    (
        lambda accepted, release: accepted["records"][0].update(review_complete=False),
        lambda accepted, release: release.update(reviewed_accepted_mapping_count=0),
        lambda accepted, release: accepted["records"][0].update(
            citation_reference_ids=[]
        ),
    ),
)
def test_coherently_rehashed_accepted_mapping_requires_complete_review_evidence(
    tmp_path: Path,
    schema_root: Path,
    mutation: object,
) -> None:
    classification_root, _ = _classification_bundle(tmp_path, 1)
    accepted_path = classification_root / "accepted_mapping_queue.json"
    release_path = classification_root / "release_metadata.json"
    accepted = _read_json(accepted_path)
    release = _read_json(release_path)
    assert callable(mutation)
    mutation(accepted, release)
    accepted_path.write_bytes(_canonical_json_bytes(accepted))
    release_path.write_bytes(_canonical_json_bytes(release))
    digest = _rehash_classification_bundle(classification_root)

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=tmp_path / "refused-incomplete-review",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            classification_bundle_root=classification_root,
            classification_review_digest=digest,
            accepted_mapping_count=1,
        )

    assert refusal.value.reason_code == "invalid_classification_reconciliation"


def test_caller_cannot_authorize_a_coherent_fabricated_classification_bundle(
    tmp_path: Path, schema_root: Path
) -> None:
    classification_root, forged_manifest_digest = _classification_bundle(tmp_path, 1)

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=tmp_path / "forged-accepted-classification",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            classification_bundle_root=classification_root,
            classification_review_digest=forged_manifest_digest,
            accepted_mapping_count=1,
            events=(_event("forged-acceptance"),),
            use_product_classification_authority=True,
        )

    assert refusal.value.reason_code == "invalid_classification_authority"
    assert not (tmp_path / "forged-accepted-classification").exists()


def test_opaque_classification_and_build_claims_are_refused(
    tmp_path: Path, schema_root: Path
) -> None:
    classification_root, _ = _classification_bundle(tmp_path, 1)
    with pytest.raises(PropagationOutputRefusalError) as opaque_digest:
        _materialize(
            output_root=tmp_path / "opaque-digest",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            classification_bundle_root=classification_root,
            classification_review_digest="0" * 64,
            accepted_mapping_count=1,
        )
    with pytest.raises(PropagationOutputRefusalError) as wrong_build:
        _materialize(
            output_root=tmp_path / "wrong-build",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            classification_bundle_root=classification_root,
            accepted_mapping_count=1,
            build_id="forged-build",
        )
    with pytest.raises(PropagationOutputRefusalError) as wrong_version:
        _materialize(
            output_root=tmp_path / "wrong-version",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            classification_bundle_root=classification_root,
            accepted_mapping_count=1,
            classification_contract_version="forged-classification",
        )

    assert opaque_digest.value.reason_code == "invalid_classification_identity"
    assert wrong_build.value.reason_code == "invalid_classification_identity"
    assert wrong_version.value.reason_code == "invalid_classification_identity"


def test_contract_and_producer_pins_are_recomputed_from_governed_files(
    tmp_path: Path, schema_root: Path
) -> None:
    changed_model = dict(_MODEL)
    default_scenario = _MODEL["default_scenario"]
    assert isinstance(default_scenario, dict)
    changed_model["default_scenario"] = {
        **default_scenario,
        "spatial": {"maximum_distance_km": 101.0},
    }
    changed_bytes = json.dumps(changed_model, sort_keys=True).encode()
    contract_path = schema_root / "propagation-model.v1.yaml"
    contract_path.write_bytes(changed_bytes)

    with pytest.raises(PropagationOutputRefusalError) as semantic_change:
        _materialize(
            output_root=tmp_path / "changed-contract",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            propagation_contract_digest=hashlib.sha256(changed_bytes).hexdigest(),
        )
    assert semantic_change.value.reason_code == "invalid_propagation_identity"

    contract_path.write_bytes(_MODEL_BYTES)
    with pytest.raises(PropagationOutputRefusalError) as opaque_producer:
        _materialize(
            output_root=tmp_path / "opaque-producer",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            propagation_producer_digest="0" * 64,
        )
    with pytest.raises(PropagationOutputRefusalError) as wrong_repository:
        _materialize(
            output_root=tmp_path / "wrong-repository",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            repository_root=tmp_path,
        )
    with pytest.raises(PropagationOutputRefusalError) as wrong_producer_id:
        _materialize(
            output_root=tmp_path / "wrong-producer-id",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            propagation_producer_id="forged-producer",
        )

    assert opaque_producer.value.reason_code == "invalid_propagation_identity"
    assert wrong_repository.value.reason_code == "invalid_propagation_identity"
    assert wrong_producer_id.value.reason_code == "invalid_propagation_identity"


@pytest.mark.parametrize(
    ("section", "field", "value"),
    (
        ("scientific_claim", "establishes_route", True),
        ("scientific_claim", "establishes_causation", True),
        ("scientific_claim", "establishes_human_migration", True),
        ("scientific_claim", "establishes_plant_migration", True),
        ("scientific_claim", "establishes_local_cultivation", True),
        ("scientific_claim", "preferred_label", "propagation route"),
        ("scientific_claim", "alternate_label", "migration"),
        ("event_contract", "non_pollen_domain_posture", "merge all evidence"),
        ("geographic_scope", "domestic_and_cross_border_rules_identical", False),
        ("candidate_logic", "no_midpoint_shortcut", False),
        ("output_edge_contract", "route_interpretation_allowed", True),
    ),
)
def test_rehashed_normative_claim_semantic_mutations_are_refused(
    tmp_path: Path,
    schema_root: Path,
    section: str,
    field: str,
    value: object,
) -> None:
    changed_model = json.loads(json.dumps(_MODEL))
    changed_section = changed_model[section]
    assert isinstance(changed_section, dict)
    changed_section[field] = value
    changed_bytes = json.dumps(changed_model, sort_keys=True).encode()
    contract_path = schema_root / "propagation-model.v1.yaml"
    contract_path.write_bytes(changed_bytes)

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=tmp_path / f"changed-{section}-{field}",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            propagation_contract_digest=hashlib.sha256(changed_bytes).hexdigest(),
        )

    assert refusal.value.reason_code == "invalid_propagation_identity"


def test_symlinked_schema_root_and_contract_components_are_refused(
    tmp_path: Path, schema_root: Path
) -> None:
    linked_schema_root = tmp_path / "linked-schemas"
    linked_schema_root.symlink_to(schema_root, target_is_directory=True)
    with pytest.raises(PropagationOutputRefusalError) as linked_root:
        _materialize(
            output_root=tmp_path / "linked-root-output",
            allowed_output_parent=tmp_path,
            schema_root=linked_schema_root,
        )

    contract_path = schema_root / "propagation-model.v1.yaml"
    real_contract = tmp_path / "governed-model.yaml"
    real_contract.write_bytes(contract_path.read_bytes())
    contract_path.unlink()
    contract_path.symlink_to(real_contract)
    with pytest.raises(PropagationOutputRefusalError) as linked_contract:
        _materialize(
            output_root=tmp_path / "linked-contract-output",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            propagation_contract_path=contract_path,
        )

    assert linked_root.value.reason_code == "invalid_propagation_identity"
    assert linked_contract.value.reason_code == "invalid_propagation_identity"


def test_symlinked_classification_bundle_ancestor_is_refused(
    tmp_path: Path, schema_root: Path
) -> None:
    real_parent = tmp_path / "classification-parent"
    real_parent.mkdir()
    classification_root, classification_digest = _classification_bundle(real_parent, 0)
    linked_parent = tmp_path / "linked-classification-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=tmp_path / "classification-ancestor-output",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            classification_bundle_root=linked_parent / classification_root.name,
            classification_review_digest=classification_digest,
        )

    assert refusal.value.reason_code == "invalid_classification_identity"


def test_symlinked_repository_root_ancestor_is_refused(
    tmp_path: Path, schema_root: Path
) -> None:
    linked_parent = tmp_path / "linked-repository-parent"
    linked_parent.symlink_to(_REPOSITORY_ROOT.parent, target_is_directory=True)

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=tmp_path / "repository-ancestor-output",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            repository_root=linked_parent / _REPOSITORY_ROOT.name,
        )

    assert refusal.value.reason_code == "invalid_propagation_identity"


def test_symlinked_output_parent_ancestor_is_refused(
    tmp_path: Path, schema_root: Path
) -> None:
    real_container = tmp_path / "output-container"
    allowed_parent = real_container / "allowed"
    allowed_parent.mkdir(parents=True)
    linked_container = tmp_path / "linked-output-container"
    linked_container.symlink_to(real_container, target_is_directory=True)
    linked_parent = linked_container / "allowed"

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=linked_parent / "published",
            allowed_output_parent=linked_parent,
            schema_root=schema_root,
        )

    assert refusal.value.reason_code == "unsafe_output_path"
    assert not (allowed_parent / "published").exists()


def test_non_identical_overwrite_is_refused_without_modification(
    tmp_path: Path, schema_root: Path
) -> None:
    output_root = tmp_path / "propagation"
    _materialize(
        output_root=output_root,
        allowed_output_parent=tmp_path,
        schema_root=schema_root,
    )
    altered_path = output_root / "release_metadata.json"
    altered_path.write_text("altered\n", encoding="utf-8")

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=output_root,
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
        )

    assert refusal.value.reason_code == "non_identical_overwrite_refused"
    assert altered_path.read_text(encoding="utf-8") == "altered\n"
    assert not tuple(tmp_path.glob(".propagation.staging-*"))
    assert not (tmp_path / ".propagation.materialization.lock").exists()


def test_staging_failure_leaves_no_partial_bundle(
    tmp_path: Path,
    schema_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_root = tmp_path / "propagation"

    def refuse_fsync(_descriptor: int) -> None:
        raise OSError("injected staging write failure")

    monkeypatch.setattr(
        "bijux_pollenomics.analysis.propagation_outputs.os.fsync",
        refuse_fsync,
    )

    with pytest.raises(OSError, match="injected staging write failure"):
        _materialize(
            output_root=output_root,
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
        )

    assert not output_root.exists()
    assert not tuple(tmp_path.glob(".propagation.staging-*"))
    assert not (tmp_path / ".propagation.materialization.lock").exists()


@pytest.mark.parametrize("unsafe_kind", ("relative", "parent", "nested"))
def test_unsafe_output_paths_are_refused_before_writing(
    tmp_path: Path, schema_root: Path, unsafe_kind: str
) -> None:
    output_root = {
        "relative": Path("relative-propagation"),
        "parent": tmp_path,
        "nested": tmp_path / "nested" / "propagation",
    }[unsafe_kind]

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=output_root,
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
        )

    assert refusal.value.reason_code == "unsafe_output_path"


def test_symlink_output_and_zero_mapping_event_input_are_refused(
    tmp_path: Path, schema_root: Path
) -> None:
    real_output = tmp_path / "real-output"
    real_output.mkdir()
    linked_output = tmp_path / "linked-output"
    linked_output.symlink_to(real_output, target_is_directory=True)

    with pytest.raises(PropagationOutputRefusalError) as symlink_refusal:
        _materialize(
            output_root=linked_output,
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
        )
    with pytest.raises(PropagationOutputRefusalError) as classification_refusal:
        _materialize(
            output_root=tmp_path / "classified-output",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            events=(_event("unaccepted"),),
        )

    assert symlink_refusal.value.reason_code == "unsafe_output_path"
    assert classification_refusal.value.reason_code == "unaccepted_classification_input"
    assert not (tmp_path / "classified-output").exists()


def test_schema_failure_refuses_the_bundle_before_publication(
    tmp_path: Path, schema_root: Path
) -> None:
    event_schema_path = schema_root / "phenomenon-event.schema.json"
    event_schema = _read_json(event_schema_path)
    properties = event_schema["properties"]
    assert isinstance(properties, dict)
    coordinate_quality = properties["coordinate_quality"]
    assert isinstance(coordinate_quality, dict)
    coordinate_quality["enum"] = ["exact"]
    event_schema_path.write_text(json.dumps(event_schema), encoding="utf-8")
    output_root = tmp_path / "propagation"

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=output_root,
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            events=(_event("schema-invalid"),),
            accepted_mapping_count=1,
        )

    assert refusal.value.reason_code == "schema_validation_failed"
    assert not output_root.exists()
