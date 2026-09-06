"""Deterministic propagation bundle materialization orchestration."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from bijux_pollenomics.analysis.propagation.network import (
    PROPAGATION_CONTRACT_VERSION,
    PhenomenonEvent,
    generate_propagation_network,
    run_propagation_sensitivity,
)

from .classification import _validate_classification_bundle_identity
from .codec import (
    _canonical_json_bytes,
    _refuse,
    _required_text,
    _sha256,
    _validate_sha256,
)
from .contracts import _validate_propagation_contract_identity
from .inputs import _load_and_check_schemas
from .manifest import _build_manifest, _validate_scenario_artifact_lineage
from .models import _MANIFEST_NAME, PropagationMaterializationResult
from .payloads import (
    _build_payloads,
    _primary_result,
    _validate_scenario_reconciliation,
)
from .producer import _validate_producer_identity
from .publication import _publish_atomically, _validate_output_location


def materialize_propagation_outputs(
    events: Sequence[PhenomenonEvent],
    *,
    output_root: Path,
    allowed_output_parent: Path,
    schema_root: Path,
    classification_bundle_root: Path,
    propagation_contract_path: Path,
    repository_root: Path,
    build_id: str,
    classification_contract_version: str,
    classification_review_digest: str,
    accepted_classification_mapping_count: int,
    propagation_contract_version: str,
    propagation_contract_digest: str,
    propagation_producer_id: str,
    propagation_producer_version: str,
    propagation_producer_digest: str,
) -> PropagationMaterializationResult:
    """Validate and atomically publish one deterministic propagation bundle."""
    output_root = Path(output_root)
    allowed_output_parent = Path(allowed_output_parent)
    _validate_output_location(output_root, allowed_output_parent)
    build_id = _required_text(build_id, field_name="build_id")
    classification_contract_version = _required_text(
        classification_contract_version,
        field_name="classification_contract_version",
    )
    propagation_contract_version = _required_text(
        propagation_contract_version,
        field_name="propagation_contract_version",
    )
    if propagation_contract_version != PROPAGATION_CONTRACT_VERSION:
        _refuse(
            "invalid_propagation_identity",
            "propagation_contract_version does not match the implementation",
        )
    propagation_producer_id = _required_text(
        propagation_producer_id,
        field_name="propagation_producer_id",
    )
    propagation_producer_version = _required_text(
        propagation_producer_version,
        field_name="propagation_producer_version",
    )
    _validate_sha256(
        classification_review_digest,
        field_name="classification_review_digest",
    )
    _validate_sha256(
        propagation_contract_digest,
        field_name="propagation_contract_digest",
    )
    _validate_sha256(
        propagation_producer_digest,
        field_name="propagation_producer_digest",
    )
    if (
        type(accepted_classification_mapping_count) is not int
        or accepted_classification_mapping_count < 0
    ):
        _refuse(
            "invalid_classification_reconciliation",
            "accepted_classification_mapping_count must be a non-negative integer",
        )
    _validate_classification_bundle_identity(
        Path(classification_bundle_root),
        build_id=build_id,
        classification_contract_version=classification_contract_version,
        classification_review_digest=classification_review_digest,
        accepted_classification_mapping_count=accepted_classification_mapping_count,
    )
    _validate_propagation_contract_identity(
        Path(propagation_contract_path),
        schema_root=Path(schema_root),
        propagation_contract_version=propagation_contract_version,
        propagation_contract_digest=propagation_contract_digest,
    )
    _validate_producer_identity(
        Path(repository_root),
        propagation_producer_id=propagation_producer_id,
        propagation_producer_version=propagation_producer_version,
        propagation_producer_digest=propagation_producer_digest,
    )
    if accepted_classification_mapping_count == 0 and events:
        _refuse(
            "unaccepted_classification_input",
            "zero accepted classification mappings requires zero eligible events",
        )
    if any(event.build_id != build_id for event in events):
        _refuse(
            "mixed_build_identity",
            "every event build_id must match the materialization build_id",
        )

    schemas = _load_and_check_schemas(Path(schema_root))
    primary_network = generate_propagation_network(events)
    sensitivity_network = run_propagation_sensitivity(events)
    primary_result = _primary_result(primary_network)
    all_events = (
        *primary_network.events,
        *primary_network.excluded_non_pollen_events,
    )
    _validate_scenario_reconciliation(primary_result, events=all_events)
    for sensitivity_result in sensitivity_network.scenario_results:
        _validate_scenario_reconciliation(sensitivity_result, events=all_events)
    payloads = _build_payloads(
        primary_network=primary_network,
        primary_result=primary_result,
        sensitivity_network=sensitivity_network,
        schemas=schemas,
        build_id=build_id,
        classification_contract_version=classification_contract_version,
        classification_review_digest=classification_review_digest,
        accepted_classification_mapping_count=accepted_classification_mapping_count,
        propagation_contract_version=propagation_contract_version,
        propagation_contract_digest=propagation_contract_digest,
        propagation_producer_id=propagation_producer_id,
        propagation_producer_version=propagation_producer_version,
        propagation_producer_digest=propagation_producer_digest,
    )
    serialized_payloads = {
        name: _canonical_json_bytes(payload) for name, payload in payloads.items()
    }
    manifest = _build_manifest(
        serialized_payloads,
        schemas=schemas,
        build_id=build_id,
        event_manifest_digest=primary_network.event_manifest_digest,
        classification_contract_version=classification_contract_version,
        classification_review_digest=classification_review_digest,
        accepted_classification_mapping_count=accepted_classification_mapping_count,
        propagation_contract_version=propagation_contract_version,
        propagation_contract_digest=propagation_contract_digest,
        propagation_producer_id=propagation_producer_id,
        propagation_producer_version=propagation_producer_version,
        propagation_producer_digest=propagation_producer_digest,
    )
    _validate_scenario_artifact_lineage(
        serialized_payloads=serialized_payloads,
        manifest=manifest,
        build_id=build_id,
        event_manifest_digest=primary_network.event_manifest_digest,
        classification_contract_version=classification_contract_version,
        classification_review_digest=classification_review_digest,
        accepted_classification_mapping_count=accepted_classification_mapping_count,
        propagation_contract_version=propagation_contract_version,
        propagation_contract_digest=propagation_contract_digest,
        propagation_producer_id=propagation_producer_id,
        propagation_producer_version=propagation_producer_version,
        propagation_producer_digest=propagation_producer_digest,
    )
    manifest_bytes = _canonical_json_bytes(manifest)
    expected_files = {**serialized_payloads, _MANIFEST_NAME: manifest_bytes}
    disposition = _publish_atomically(
        output_root=output_root,
        allowed_output_parent=allowed_output_parent,
        expected_files=expected_files,
    )
    return PropagationMaterializationResult(
        output_root=output_root,
        disposition=disposition,
        manifest_sha256=_sha256(manifest_bytes),
        file_count=len(expected_files),
        eligible_event_count=len(primary_network.events),
        excluded_non_pollen_event_count=len(primary_network.excluded_non_pollen_events),
        primary_directed_candidate_count=len(primary_result.directed_candidates),
    )
