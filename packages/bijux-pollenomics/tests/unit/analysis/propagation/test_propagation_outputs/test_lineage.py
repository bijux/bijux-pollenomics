"""Lineage tests."""

from __future__ import annotations
import hashlib
from pathlib import Path
import pytest
from bijux_pollenomics.analysis.propagation.outputs import (
    PropagationOutputRefusalError,
)
from bijux_pollenomics.analysis.propagation.outputs import (
    manifest as propagation_manifest,
)
from bijux_pollenomics.analysis.propagation.outputs import models as propagation_models
from .conftest import (
    _PROPAGATION_CONTRACT_DIGEST,
    _PROPAGATION_CONTRACT_VERSION,
    _PROPAGATION_PRODUCER_ID,
    _PROPAGATION_PRODUCER_VERSION,
    _canonical_json_bytes,
    _event,
    _materialize,
    _producer_digest,
    _read_json,
)


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
        for name in propagation_models._OUTPUT_NAMES
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
        propagation_manifest._validate_scenario_artifact_lineage(
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
        for name in propagation_models._OUTPUT_NAMES
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
        propagation_manifest._validate_scenario_artifact_lineage(
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
