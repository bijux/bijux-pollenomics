from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.propagation_network import PhenomenonEvent
from bijux_pollenomics.analysis.propagation_outputs import (
    PropagationMaterializationResult,
    PropagationOutputRefusalError,
    materialize_propagation_outputs,
)

_DIGEST = hashlib.sha256(b"classification-review").hexdigest()
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


def _materialize(
    *,
    output_root: Path,
    allowed_output_parent: Path,
    schema_root: Path,
    events: tuple[PhenomenonEvent, ...] = (),
    accepted_mapping_count: int = 0,
) -> PropagationMaterializationResult:
    return materialize_propagation_outputs(
        events,
        output_root=output_root,
        allowed_output_parent=allowed_output_parent,
        schema_root=schema_root,
        build_id="build-1",
        classification_contract_version="classification.v1",
        classification_review_digest=_DIGEST,
        accepted_classification_mapping_count=accepted_mapping_count,
    )


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
    sensitivity = _read_json(output_root / "sensitivity_summary.json")
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
        isinstance(scenario, dict) and scenario["eligible_event_count"] == 0
        for scenario in scenarios
    )
    assert release["release_status"] == "refused"
    assert release["public_release_allowed"] is False
    assert release["reason_codes"] == ["no_accepted_classification_mappings"]
    assert release["accepted_classification_mapping_count"] == 0
    assert release["candidate_materialization_status"] == "empty_refused"


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
