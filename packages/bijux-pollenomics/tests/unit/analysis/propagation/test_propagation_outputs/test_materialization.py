"""Materialization tests."""

from __future__ import annotations
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from .conftest import (
    _PROPAGATION_CONTRACT_DIGEST,
    _PROPAGATION_CONTRACT_VERSION,
    _PROPAGATION_PRODUCER_ID,
    _PROPAGATION_PRODUCER_VERSION,
    _event,
    _materialize,
    _producer_digest,
    _read_json,
)


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
