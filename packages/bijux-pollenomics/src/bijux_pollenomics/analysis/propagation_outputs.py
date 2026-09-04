from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn, cast

from .propagation_network import (
    COUNTRY_CODES,
    EVIDENCE_DOMAINS,
    PROPAGATION_CONTRACT_VERSION,
    PROPAGATION_SENSITIVITY_SCENARIOS,
    PhenomenonEvent,
    PropagationNetworkResult,
    PropagationScenarioResult,
    generate_propagation_network,
    run_propagation_sensitivity,
)
from .site_candidates import DEFAULT_PROPAGATION_SCENARIO

__all__ = [
    "PROPAGATION_PRODUCER_ID",
    "PROPAGATION_PRODUCER_SOURCE_PATHS",
    "PROPAGATION_PRODUCER_VERSION",
    "PropagationMaterializationResult",
    "PropagationOutputRefusalError",
    "materialize_propagation_outputs",
]

_EVENT_SCHEMA_NAME = "phenomenon-event.schema.json"
_CANDIDATE_SCHEMA_NAME = "propagation-candidate.schema.json"
_MANIFEST_NAME = "manifest.json"
_EXPECTED_SCHEMA_IDS = {
    _EVENT_SCHEMA_NAME: "https://bijux.io/schemas/pollenomics/phenomenon-event.v1.json",
    _CANDIDATE_SCHEMA_NAME: (
        "https://bijux.io/schemas/pollenomics/propagation-candidate.v1.json"
    ),
}
_OUTPUT_NAMES = (
    "phenomenon_events.json",
    "excluded_non_pollen_events.json",
    "primary_scenario_candidates.json",
    "primary_scenario_refusals.json",
    "primary_scenario_reconciliation.json",
    "release_metadata.json",
    "sensitivity_summary.json",
)
PROPAGATION_PRODUCER_ID = "bijux-pollenomics.propagation-output-materializer"
PROPAGATION_PRODUCER_VERSION = "1"
PROPAGATION_PRODUCER_SOURCE_PATHS = (
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation_outputs.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation_network.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/site_candidates.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/core/geo_distance.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/core/temporal_semantics.py",
)
_CLASSIFICATION_MANIFEST_NAME = "manifest.json"
_CLASSIFICATION_RELEASE_NAME = "release_metadata.json"
_CLASSIFICATION_ACCEPTED_QUEUE_NAME = "accepted_mapping_queue.json"
_CLASSIFICATION_PAYLOAD_NAMES = frozenset(
    {
        _CLASSIFICATION_ACCEPTED_QUEUE_NAME,
        "concept_denominators.json",
        "country_partitions.json",
        "not_applicable_mapping_queue.json",
        "observation_denominators.json",
        "observation_memberships.json",
        _CLASSIFICATION_RELEASE_NAME,
        "review_queue.json",
        "unmapped_mapping_queue.json",
    }
)


class PropagationOutputRefusalError(ValueError):
    """Refuse materialization that cannot preserve governed output invariants."""

    def __init__(self, reason_code: str, detail: str) -> None:
        self.reason_code = reason_code
        super().__init__(detail)


@dataclass(frozen=True)
class PropagationMaterializationResult:
    """Observable result of an atomic or byte-identical materialization."""

    output_root: Path
    disposition: str
    manifest_sha256: str
    file_count: int
    eligible_event_count: int
    excluded_non_pollen_event_count: int
    primary_directed_candidate_count: int


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
        isinstance(accepted_classification_mapping_count, bool)
        or not isinstance(accepted_classification_mapping_count, int)
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


def _build_payloads(
    *,
    primary_network: PropagationNetworkResult,
    primary_result: PropagationScenarioResult,
    sensitivity_network: PropagationNetworkResult,
    schemas: Mapping[str, dict[str, Any]],
    build_id: str,
    classification_contract_version: str,
    classification_review_digest: str,
    accepted_classification_mapping_count: int,
    propagation_contract_version: str,
    propagation_contract_digest: str,
    propagation_producer_id: str,
    propagation_producer_version: str,
    propagation_producer_digest: str,
) -> dict[str, dict[str, object]]:
    event_schema = schemas[_EVENT_SCHEMA_NAME]
    candidate_schema = schemas[_CANDIDATE_SCHEMA_NAME]
    event_records = tuple(
        _event_schema_record(event, event_schema) for event in primary_network.events
    )
    excluded_event_records = tuple(
        _event_schema_record(event, event_schema)
        for event in primary_network.excluded_non_pollen_events
    )
    excluded_non_pollen_records = tuple(
        {
            "reason_code": "evidence_domain_not_pollen_propagation_eligible",
            "event": event_record,
        }
        for event_record in excluded_event_records
    )
    event_evaluation_metadata = tuple(
        _event_evaluation_metadata(event) for event in primary_network.events
    )
    candidate_records = tuple(row.as_dict() for row in primary_result.evaluated_pairs)
    _validate_records(event_records, event_schema, record_kind="phenomenon event")
    _validate_records(
        excluded_event_records,
        event_schema,
        record_kind="excluded non-pollen phenomenon event",
    )
    _validate_records(
        candidate_records,
        candidate_schema,
        record_kind="propagation candidate",
    )
    sensitivity_summaries = tuple(
        _sensitivity_scenario_summary(
            result,
            events=(
                *sensitivity_network.events,
                *sensitivity_network.excluded_non_pollen_events,
            ),
        )
        for result in sensitivity_network.scenario_results
    )
    feature_stability = _feature_stability_across_scenarios(sensitivity_network)
    if len(sensitivity_summaries) != len(PROPAGATION_SENSITIVITY_SCENARIOS):
        _refuse(
            "invalid_sensitivity_reconciliation",
            "the materialized sensitivity set must contain all 16 declared scenarios",
        )
    release_refused = accepted_classification_mapping_count == 0
    release_reason_codes = (
        ("no_accepted_classification_mappings",)
        if release_refused
        else ("independent_scientific_review_required",)
    )
    release_status = "refused" if release_refused else "review_required"

    return {
        "phenomenon_events.json": {
            "schema_version": "propagation-events-artifact.v1",
            "record_schema_id": event_schema["$id"],
            "build_id": build_id,
            "event_manifest_digest": primary_network.event_manifest_digest,
            "record_count": len(event_records),
            "records": event_records,
            "evaluation_metadata_record_count": len(event_evaluation_metadata),
            "evaluation_metadata": event_evaluation_metadata,
        },
        "excluded_non_pollen_events.json": {
            "schema_version": "propagation-event-exclusions.v1",
            "record_schema_id": event_schema["$id"],
            "build_id": build_id,
            "record_count": len(excluded_non_pollen_records),
            "records": excluded_non_pollen_records,
        },
        "primary_scenario_candidates.json": {
            "schema_version": "propagation-candidates-artifact.v1",
            "record_schema_id": candidate_schema["$id"],
            "build_id": build_id,
            "event_manifest_digest": primary_network.event_manifest_digest,
            "scenario_id": primary_result.scenario.scenario_id,
            "record_count": len(candidate_records),
            "directed_candidate_count": len(primary_result.directed_candidates),
            "records": candidate_records,
        },
        "primary_scenario_refusals.json": {
            "schema_version": "propagation-refusals-artifact.v1",
            "build_id": build_id,
            "event_manifest_digest": primary_network.event_manifest_digest,
            "scenario_id": primary_result.scenario.scenario_id,
            "record_count": len(primary_result.refusals),
            "records": tuple(row.as_dict() for row in primary_result.refusals),
        },
        "primary_scenario_reconciliation.json": {
            "schema_version": "propagation-reconciliation-artifact.v1",
            "build_id": build_id,
            "event_manifest_digest": primary_network.event_manifest_digest,
            "scenario_id": primary_result.scenario.scenario_id,
            "record_count": 1,
            "reconciliation": {
                **primary_result.reconciliation.as_dict(),
                "denominator_partitions": _denominator_partitions(
                    (
                        *primary_network.events,
                        *primary_network.excluded_non_pollen_events,
                    ),
                    primary_result,
                ),
            },
        },
        "sensitivity_summary.json": {
            "schema_version": "propagation-sensitivity-summary.v1",
            "build_id": build_id,
            "event_manifest_digest": primary_network.event_manifest_digest,
            "record_count": len(sensitivity_summaries),
            "scenarios": sensitivity_summaries,
            "feature_stability_across_scenarios": feature_stability,
        },
        "release_metadata.json": {
            "schema_version": "propagation-release-metadata.v2",
            "status_namespace": "propagation_release",
            "release_status": release_status,
            "public_release_allowed": False,
            "reason_codes": release_reason_codes,
            "build_id": build_id,
            "classification_contract_version": classification_contract_version,
            "classification_review_digest": classification_review_digest,
            "propagation_contract_version": propagation_contract_version,
            "propagation_contract_digest": propagation_contract_digest,
            "propagation_producer_id": propagation_producer_id,
            "propagation_producer_version": propagation_producer_version,
            "propagation_producer_digest": propagation_producer_digest,
            "accepted_classification_mapping_count": (
                accepted_classification_mapping_count
            ),
            "eligible_event_count": len(primary_network.events),
            "input_event_count": (
                len(primary_network.events)
                + len(primary_network.excluded_non_pollen_events)
            ),
            "excluded_non_pollen_event_count": len(
                primary_network.excluded_non_pollen_events
            ),
            "primary_directed_candidate_count": len(primary_result.directed_candidates),
            "candidate_materialization_status": (
                "empty_refused" if release_refused else "review_only"
            ),
            "record_count": 1,
        },
    }


def _event_schema_record(
    event: PhenomenonEvent, schema: Mapping[str, Any]
) -> dict[str, object]:
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        _refuse("invalid_control_schema", "event schema has no properties object")
    assert isinstance(properties, dict)
    event_payload = event.as_dict()
    return {key: event_payload[key] for key in properties if key in event_payload}


def _event_evaluation_metadata(event: PhenomenonEvent) -> dict[str, object]:
    return {
        "event_id": event.event_id,
        "measurement_semantics_id": event.measurement_semantics_id,
        "evidence_method_id": event.evidence_method_id,
        "method_compatibility_key": event.method_compatibility_key,
        "subject_granularity": event.subject_granularity,
        "preaggregation_valid": event.preaggregation_valid,
        "role_membership_explicit": event.role_membership_explicit,
        "temporal_contract_version": event.temporal_contract_version,
    }


def _sensitivity_scenario_summary(
    result: PropagationScenarioResult,
    *,
    events: Sequence[PhenomenonEvent],
) -> dict[str, object]:
    reconciliation = result.reconciliation.as_dict()
    status_counts = dict(result.reconciliation.status_counts)
    return {
        "scenario_id": result.scenario.scenario_id,
        "maximum_distance_km": result.scenario.maximum_distance_km,
        "maximum_lag_years": result.scenario.maximum_lag_years,
        "eligible_event_count": result.reconciliation.eligible_event_count,
        "evaluated_pair_count": result.reconciliation.evaluated_pair_count,
        "refused_pair_count": result.reconciliation.refused_pair_count,
        "definite_candidate_count": status_counts["definite_candidate"],
        "possible_candidate_count": status_counts["possible_candidate"],
        "indeterminate_order_count": status_counts["indeterminate_order"],
        "unresolved_pair_count": status_counts["unresolved"],
        "excluded_spatial_count": status_counts["excluded_spatial"],
        "excluded_temporal_nonpositive_count": status_counts[
            "excluded_temporal_nonpositive"
        ],
        "excluded_temporal_too_large_count": status_counts[
            "excluded_temporal_too_large"
        ],
        "excluded_temporal_count": (
            status_counts["excluded_temporal_nonpositive"]
            + status_counts["excluded_temporal_too_large"]
        ),
        "connected_component_count": result.reconciliation.connected_component_count,
        "ordered_country_pair_counts": reconciliation["ordered_country_pair_counts"],
        "country_pair_counts": reconciliation["ordered_country_pair_counts"],
        "denominator_partitions": _denominator_partitions(events, result),
    }


def _primary_result(network: PropagationNetworkResult) -> PropagationScenarioResult:
    matches = tuple(
        result
        for result in network.scenario_results
        if result.scenario.scenario_id == DEFAULT_PROPAGATION_SCENARIO.scenario_id
    )
    if len(matches) != 1:
        _refuse(
            "invalid_primary_scenario",
            "the network must contain exactly one governed primary scenario",
        )
    return matches[0]


def _denominator_partitions(
    events: Sequence[PhenomenonEvent],
    result: PropagationScenarioResult,
) -> dict[str, dict[str, object]]:
    event_fields = {
        "country_code": Counter(event.country_code for event in events),
        "source_family": Counter(event.source_family for event in events),
        "evidence_domain": Counter(event.evidence_domain for event in events),
        "resolution": Counter(event.resolution for event in events),
        "feature_key": Counter(event.feature_key for event in events),
        "threshold_profile_id": Counter(event.threshold_profile_id for event in events),
    }
    event_fields["country_code"] = Counter(
        {code: event_fields["country_code"][code] for code in COUNTRY_CODES}
    )
    event_fields["evidence_domain"] = Counter(
        {domain: event_fields["evidence_domain"][domain] for domain in EVIDENCE_DOMAINS}
    )
    ordered_country_pairs = {
        key: sum(dict(statuses).values())
        for key, statuses in result.reconciliation.ordered_country_pair_counts
    }
    candidate_statuses = dict(result.reconciliation.status_counts)
    pair_decision_count = (
        result.reconciliation.evaluated_pair_count
        + result.reconciliation.refused_pair_count
    )
    partitions: dict[str, dict[str, object]] = {
        name: {
            "counting_basis": "input_event",
            "total_count": len(events),
            "counts": dict(sorted(counts.items())),
        }
        for name, counts in event_fields.items()
    }
    partitions.update(
        {
            "ordered_country_pair": {
                "counting_basis": "evaluated_or_refused_pair",
                "total_count": pair_decision_count,
                "counts": dict(sorted(ordered_country_pairs.items())),
            },
            "candidate_status": {
                "counting_basis": "evaluated_pair",
                "total_count": result.reconciliation.evaluated_pair_count,
                "counts": dict(sorted(candidate_statuses.items())),
            },
            "scenario_id": {
                "counting_basis": "evaluated_or_refused_pair",
                "total_count": pair_decision_count,
                "counts": {result.scenario.scenario_id: pair_decision_count},
            },
        }
    )
    return dict(sorted(partitions.items()))


def _feature_stability_across_scenarios(
    network: PropagationNetworkResult,
) -> tuple[dict[str, object], ...]:
    event_counts = Counter(
        (event.resolution, event.feature_key, event.threshold_profile_id)
        for event in network.events
    )
    rows: list[dict[str, object]] = []
    for resolution, feature_key, threshold_profile_id in sorted(event_counts):
        scenario_status_counts: dict[str, dict[str, int]] = {}
        directed_scenarios = 0
        for result in network.scenario_results:
            counts = Counter(
                row.candidate_status
                for row in result.evaluated_pairs
                if row.resolution == resolution
                and row.feature_key == feature_key
                and row.threshold_profile_id == threshold_profile_id
            )
            scenario_status_counts[result.scenario.scenario_id] = {
                status: counts[status]
                for status, _ in result.reconciliation.status_counts
            }
            if counts["definite_candidate"] + counts["possible_candidate"]:
                directed_scenarios += 1
        rows.append(
            {
                "resolution": resolution,
                "feature_key": feature_key,
                "threshold_profile_id": threshold_profile_id,
                "eligible_event_count": event_counts[
                    (resolution, feature_key, threshold_profile_id)
                ],
                "scenario_count": len(network.scenario_results),
                "directed_candidate_scenario_count": directed_scenarios,
                "directed_candidate_in_every_scenario": (
                    directed_scenarios == len(network.scenario_results)
                ),
                "scenario_status_counts": scenario_status_counts,
            }
        )
    return tuple(rows)


def _validate_scenario_reconciliation(
    result: PropagationScenarioResult,
    *,
    events: Sequence[PhenomenonEvent],
) -> None:
    reconciliation = result.reconciliation
    observed_status_counts = Counter(
        row.candidate_status for row in result.evaluated_pairs
    )
    declared_status_counts = dict(reconciliation.status_counts)
    domain_counts = dict(reconciliation.evidence_domain_event_counts)
    if (
        set(domain_counts) != set(EVIDENCE_DOMAINS)
        or sum(domain_counts.values()) != reconciliation.input_event_count
        or domain_counts["pollen_context"] != reconciliation.eligible_event_count
        or reconciliation.input_event_count
        != reconciliation.eligible_event_count
        + reconciliation.excluded_non_pollen_event_count
        or sum(declared_status_counts.values()) != len(result.evaluated_pairs)
        or reconciliation.evaluated_pair_count != len(result.evaluated_pairs)
        or reconciliation.refused_pair_count != len(result.refusals)
        or any(
            observed_status_counts[status] != count
            for status, count in declared_status_counts.items()
        )
    ):
        _refuse(
            "invalid_output_reconciliation",
            f"scenario counts do not reconcile: {result.scenario.scenario_id}",
        )
    country_counts = dict(reconciliation.ordered_country_pair_counts)
    expected_country_pairs = {
        f"{source}-{target}" for source in COUNTRY_CODES for target in COUNTRY_CODES
    }
    if set(country_counts) != expected_country_pairs:
        _refuse(
            "invalid_output_reconciliation",
            f"ordered country pairs are incomplete: {result.scenario.scenario_id}",
        )
    country_total = sum(
        sum(dict(statuses).values()) for statuses in country_counts.values()
    )
    if country_total != len(result.evaluated_pairs) + len(result.refusals):
        _refuse(
            "invalid_output_reconciliation",
            f"country-pair counts do not reconcile: {result.scenario.scenario_id}",
        )
    partitions = _denominator_partitions(events, result)
    required_partitions = {
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
    if set(partitions) != required_partitions:
        _refuse(
            "invalid_output_reconciliation",
            f"denominator partitions are incomplete: {result.scenario.scenario_id}",
        )
    for name, partition in partitions.items():
        counts = partition["counts"]
        assert isinstance(counts, dict)
        if sum(counts.values()) != partition["total_count"]:
            _refuse(
                "invalid_output_reconciliation",
                f"denominator partition does not reconcile: {name}",
            )


def _validate_classification_bundle_identity(
    bundle_root: Path,
    *,
    build_id: str,
    classification_contract_version: str,
    classification_review_digest: str,
    accepted_classification_mapping_count: int,
) -> None:
    if (
        not bundle_root.is_absolute()
        or bundle_root.is_symlink()
        or not bundle_root.is_dir()
    ):
        _refuse(
            "invalid_classification_identity",
            "classification_bundle_root must be an absolute non-symlink directory",
        )
    manifest_bytes = _read_identity_file(
        bundle_root / _CLASSIFICATION_MANIFEST_NAME,
        parent=bundle_root,
        reason_code="invalid_classification_identity",
    )
    if _sha256(manifest_bytes) != classification_review_digest:
        _refuse(
            "invalid_classification_identity",
            "classification_review_digest does not match classification manifest bytes",
        )
    manifest = _json_object(
        manifest_bytes,
        reason_code="invalid_classification_identity",
        label="classification manifest",
    )
    if manifest.get("schema_version") != "classification-audit-manifest.v1":
        _refuse(
            "invalid_classification_identity",
            "classification manifest schema_version is not governed",
        )
    entries = _identity_manifest_entries(
        manifest,
        reason_code="invalid_classification_identity",
    )
    if {entry[0] for entry in entries} != _CLASSIFICATION_PAYLOAD_NAMES:
        _refuse(
            "invalid_classification_identity",
            "classification manifest does not contain the governed payload set",
        )
    expected_names = {_CLASSIFICATION_MANIFEST_NAME, *(entry[0] for entry in entries)}
    actual_names = {path.name for path in bundle_root.iterdir()}
    if actual_names != expected_names:
        _refuse(
            "invalid_classification_identity",
            "classification bundle inventory does not match its manifest",
        )
    payloads: dict[str, dict[str, Any]] = {}
    for name, expected_digest, expected_count in entries:
        payload_bytes = _read_identity_file(
            bundle_root / name,
            parent=bundle_root,
            reason_code="invalid_classification_identity",
        )
        if _sha256(payload_bytes) != expected_digest:
            _refuse(
                "invalid_classification_identity",
                f"classification payload digest changed: {name}",
            )
        payload = _json_object(
            payload_bytes,
            reason_code="invalid_classification_identity",
            label=f"classification payload {name}",
        )
        if payload.get("record_count") != expected_count:
            _refuse(
                "invalid_classification_identity",
                f"classification payload count changed: {name}",
            )
        if (
            payload.get("source_family") != manifest.get("source_family")
            or payload.get("source_snapshot_id") != manifest.get("source_snapshot_id")
            or payload.get("build_id") != manifest.get("build_id")
            or payload.get("classification_contract_version")
            != manifest.get("classification_contract_version")
            or payload.get("classification_contract_digest")
            != manifest.get("classification_contract_digest")
            or payload.get("classification_producer_id")
            != manifest.get("classification_producer_id")
            or payload.get("classification_producer_version")
            != manifest.get("classification_producer_version")
            or payload.get("classification_producer_digest")
            != manifest.get("classification_producer_digest")
        ):
            _refuse(
                "invalid_classification_identity",
                f"classification payload identity changed: {name}",
            )
        payloads[name] = payload
    digest_input = "".join(
        f"{name}\0{digest}\0{count}\n" for name, digest, count in entries
    ).encode("utf-8")
    if manifest.get("bundle_digest") != _sha256(digest_input):
        _refuse(
            "invalid_classification_identity",
            "classification bundle digest does not reconcile",
        )
    if (
        manifest.get("build_id") != build_id
        or manifest.get("classification_contract_version")
        != classification_contract_version
    ):
        _refuse(
            "invalid_classification_identity",
            "classification manifest build or contract version does not match the pin",
        )
    release = payloads.get(_CLASSIFICATION_RELEASE_NAME)
    accepted_queue = payloads.get(_CLASSIFICATION_ACCEPTED_QUEUE_NAME)
    if release is None or accepted_queue is None:
        _refuse(
            "invalid_classification_identity",
            "classification release metadata and accepted queue must be manifested",
        )
    if (
        release.get("schema_version") != "classification-release-metadata.v1"
        or release.get("build_id") != build_id
        or release.get("classification_contract_version")
        != classification_contract_version
        or accepted_queue.get("build_id") != build_id
        or accepted_queue.get("classification_contract_version")
        != classification_contract_version
    ):
        _refuse(
            "invalid_classification_identity",
            "classification release and accepted queue do not match pinned identities",
        )
    accepted_records = accepted_queue.get("records")
    if not isinstance(accepted_records, list):
        _refuse(
            "invalid_classification_identity",
            "classification accepted queue records must be an array",
        )
    embedded_count = release.get("accepted_mapping_count")
    if (
        isinstance(embedded_count, bool)
        or not isinstance(embedded_count, int)
        or embedded_count != accepted_classification_mapping_count
        or accepted_queue.get("record_count") != embedded_count
        or len(accepted_records) != embedded_count
    ):
        _refuse(
            "invalid_classification_reconciliation",
            "accepted classification count does not match the verified bundle",
        )


def _validate_propagation_contract_identity(
    contract_path: Path,
    *,
    schema_root: Path,
    propagation_contract_version: str,
    propagation_contract_digest: str,
) -> None:
    if (
        not contract_path.is_absolute()
        or contract_path.name != "propagation-model.v1.yaml"
        or contract_path.parent != schema_root
    ):
        _refuse(
            "invalid_propagation_identity",
            "propagation contract must be the governed file in schema_root",
        )
    contract_bytes = _read_identity_file(
        contract_path,
        parent=schema_root,
        reason_code="invalid_propagation_identity",
    )
    if _sha256(contract_bytes) != propagation_contract_digest:
        _refuse(
            "invalid_propagation_identity",
            "propagation_contract_digest does not match contract bytes",
        )
    try:
        import yaml
    except ImportError as error:
        raise PropagationOutputRefusalError(
            "invalid_propagation_identity",
            "PyYAML is required to verify the propagation contract",
        ) from error
    try:
        contract = yaml.safe_load(contract_bytes)
    except (ValueError, yaml.YAMLError) as error:
        raise PropagationOutputRefusalError(
            "invalid_propagation_identity",
            "propagation contract cannot be parsed",
        ) from error
    if not isinstance(contract, dict):
        _refuse(
            "invalid_propagation_identity",
            "propagation contract must be a mapping",
        )
    sensitivity = contract.get("sensitivity_analysis")
    event_contract = contract.get("event_contract")
    geography = contract.get("geographic_scope")
    default = contract.get("default_scenario")
    if not all(
        isinstance(value, dict)
        for value in (sensitivity, event_contract, geography, default)
    ):
        _refuse(
            "invalid_propagation_identity",
            "propagation contract omits governed model sections",
        )
    assert isinstance(sensitivity, dict)
    assert isinstance(event_contract, dict)
    assert isinstance(geography, dict)
    assert isinstance(default, dict)
    spatial = default.get("spatial")
    temporal = default.get("temporal")
    required_metrics = sensitivity.get("required_metrics")
    governed_metrics = {
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
    }
    if (
        contract.get("contract_id") != "bijux-pollenomics.propagation-model"
        or contract.get("contract_version") != propagation_contract_version
        or event_contract.get("allowed_evidence_domains") != list(EVIDENCE_DOMAINS)
        or event_contract.get("pollen_candidate_domain") != "pollen_context"
        or geography.get("countries") != list(COUNTRY_CODES)
        or default.get("scenario_id") != DEFAULT_PROPAGATION_SCENARIO.scenario_id
        or not isinstance(spatial, dict)
        or spatial.get("maximum_distance_km")
        != DEFAULT_PROPAGATION_SCENARIO.maximum_distance_km
        or not isinstance(temporal, dict)
        or temporal.get("maximum_lag_years")
        != DEFAULT_PROPAGATION_SCENARIO.maximum_lag_years
        or sensitivity.get("distance_km_values") != [25.0, 50.0, 100.0, 200.0]
        or sensitivity.get("lag_year_values") != [50.0, 100.0, 200.0, 500.0]
        or not isinstance(required_metrics, list)
        or not all(isinstance(metric, str) for metric in required_metrics)
        or set(required_metrics) != governed_metrics
    ):
        _refuse(
            "invalid_propagation_identity",
            "propagation contract semantics do not match the implementation",
        )


def _validate_producer_identity(
    repository_root: Path,
    *,
    propagation_producer_id: str,
    propagation_producer_version: str,
    propagation_producer_digest: str,
) -> None:
    executing_source = Path(__file__).resolve()
    governed_source = repository_root / PROPAGATION_PRODUCER_SOURCE_PATHS[0]
    if (
        not repository_root.is_absolute()
        or repository_root.is_symlink()
        or not repository_root.is_dir()
        or not governed_source.is_file()
        or governed_source.resolve(strict=True) != executing_source
    ):
        _refuse(
            "invalid_propagation_identity",
            "repository_root does not own the executing propagation producer",
        )
    if (
        propagation_producer_id != PROPAGATION_PRODUCER_ID
        or propagation_producer_version != PROPAGATION_PRODUCER_VERSION
    ):
        _refuse(
            "invalid_propagation_identity",
            "propagation producer id or version is not governed",
        )
    records = []
    for relative_name in PROPAGATION_PRODUCER_SOURCE_PATHS:
        source_path = repository_root / relative_name
        source_bytes = _read_identity_file(
            source_path,
            parent=repository_root,
            reason_code="invalid_propagation_identity",
            allow_descendant=True,
        )
        records.append({"path": relative_name, "sha256": _sha256(source_bytes)})
    computed_digest = _sha256(
        json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    if computed_digest != propagation_producer_digest:
        _refuse(
            "invalid_propagation_identity",
            "propagation_producer_digest does not match governed source bytes",
        )


def _identity_manifest_entries(
    manifest: Mapping[str, Any],
    *,
    reason_code: str,
) -> tuple[tuple[str, str, int], ...]:
    raw_entries = manifest.get("files")
    if not isinstance(raw_entries, list):
        _refuse(reason_code, "identity manifest files must be an array")
    entries: list[tuple[str, str, int]] = []
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, dict):
            _refuse(reason_code, "identity manifest entries must be objects")
        name = raw_entry.get("path")
        digest = raw_entry.get("sha256")
        count = raw_entry.get("record_count")
        if (
            not isinstance(name, str)
            or not name
            or Path(name).name != name
            or name == _CLASSIFICATION_MANIFEST_NAME
            or not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
            or isinstance(count, bool)
            or not isinstance(count, int)
            or count < 0
        ):
            _refuse(reason_code, "identity manifest entry is invalid")
        entries.append((name, digest, count))
    if (
        len(entries) != len({entry[0] for entry in entries})
        or entries != sorted(entries)
        or manifest.get("payload_file_count") != len(entries)
    ):
        _refuse(reason_code, "identity manifest entries are not deterministic")
    return tuple(entries)


def _read_identity_file(
    path: Path,
    *,
    parent: Path,
    reason_code: str,
    allow_descendant: bool = False,
) -> bytes:
    try:
        resolved_parent = parent.resolve(strict=True)
        resolved_path = path.resolve(strict=True)
    except OSError as error:
        raise PropagationOutputRefusalError(
            reason_code,
            f"identity file cannot be resolved: {path.name}",
        ) from error
    direct_parent_matches = (
        path.parent == parent and resolved_path.parent == resolved_parent
    )
    descendant_matches = resolved_path.is_relative_to(resolved_parent)
    if (
        path.is_symlink()
        or not path.is_file()
        or not (descendant_matches if allow_descendant else direct_parent_matches)
    ):
        _refuse(reason_code, f"identity file is unsafe: {path.name}")
    try:
        return path.read_bytes()
    except OSError as error:
        raise PropagationOutputRefusalError(
            reason_code,
            f"identity file cannot be read: {path.name}",
        ) from error


def _json_object(value: bytes, *, reason_code: str, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(value)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PropagationOutputRefusalError(
            reason_code,
            f"{label} is not valid JSON",
        ) from error
    if not isinstance(payload, dict):
        _refuse(reason_code, f"{label} must be an object")
    return cast(dict[str, Any], payload)


def _load_and_check_schemas(schema_root: Path) -> dict[str, dict[str, Any]]:
    if not schema_root.is_absolute() or not schema_root.is_dir():
        _refuse(
            "unsafe_schema_root",
            "schema_root must be an existing absolute directory",
        )
    try:
        from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
        from jsonschema.exceptions import SchemaError  # type: ignore[import-untyped]
    except ImportError as error:
        raise PropagationOutputRefusalError(
            "schema_validator_unavailable",
            "jsonschema is required to validate propagation materializations",
        ) from error

    schemas: dict[str, dict[str, Any]] = {}
    for schema_name in (_EVENT_SCHEMA_NAME, _CANDIDATE_SCHEMA_NAME):
        schema_path = schema_root / schema_name
        if schema_path.parent != schema_root or not schema_path.is_file():
            _refuse(
                "missing_control_schema",
                f"required control schema is missing: {schema_name}",
            )
        try:
            raw_schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise PropagationOutputRefusalError(
                "invalid_control_schema",
                f"control schema cannot be read: {schema_name}",
            ) from error
        if not isinstance(raw_schema, dict):
            _refuse(
                "invalid_control_schema",
                f"control schema must be a JSON object: {schema_name}",
            )
        if raw_schema.get("$id") != _EXPECTED_SCHEMA_IDS[schema_name]:
            _refuse(
                "invalid_control_schema",
                f"control schema identity is not governed: {schema_name}",
            )
        try:
            Draft202012Validator.check_schema(raw_schema)
        except SchemaError as error:
            raise PropagationOutputRefusalError(
                "invalid_control_schema",
                f"control schema is invalid: {schema_name}: {error.message}",
            ) from error
        schemas[schema_name] = raw_schema
    return schemas


def _validate_records(
    records: Sequence[Mapping[str, object]],
    schema: Mapping[str, Any],
    *,
    record_kind: str,
) -> None:
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(schema)
    for index, record in enumerate(records):
        errors = sorted(
            validator.iter_errors(record),
            key=lambda error: tuple(str(part) for part in error.absolute_path),
        )
        if errors:
            error = errors[0]
            path = ".".join(str(part) for part in error.absolute_path) or "<root>"
            _refuse(
                "schema_validation_failed",
                f"{record_kind} {index} fails at {path}: {error.message}",
            )


def _build_manifest(
    serialized_payloads: Mapping[str, bytes],
    *,
    schemas: Mapping[str, dict[str, Any]],
    build_id: str,
    event_manifest_digest: str,
    propagation_contract_version: str,
    propagation_contract_digest: str,
    propagation_producer_id: str,
    propagation_producer_version: str,
    propagation_producer_digest: str,
) -> dict[str, object]:
    entries = tuple(
        {
            "path": name,
            "sha256": _sha256(serialized_payloads[name]),
            "record_count": _payload_record_count(serialized_payloads[name]),
        }
        for name in sorted(serialized_payloads)
    )
    digest_input = "".join(
        f"{entry['path']}\0{entry['sha256']}\0{entry['record_count']}\n"
        for entry in entries
    ).encode("utf-8")
    schema_entries = tuple(
        {
            "name": name,
            "schema_id": schemas[name]["$id"],
            "sha256": _sha256(_canonical_json_bytes(schemas[name])),
        }
        for name in sorted(schemas)
    )
    return {
        "schema_version": "propagation-output-manifest.v2",
        "build_id": build_id,
        "event_manifest_digest": event_manifest_digest,
        "propagation_contract_version": propagation_contract_version,
        "propagation_contract_digest": propagation_contract_digest,
        "propagation_producer_id": propagation_producer_id,
        "propagation_producer_version": propagation_producer_version,
        "propagation_producer_digest": propagation_producer_digest,
        "bundle_digest": _sha256(digest_input),
        "payload_file_count": len(entries),
        "files": entries,
        "validated_record_schemas": schema_entries,
    }


def _payload_record_count(payload_bytes: bytes) -> int:
    payload: object = json.loads(payload_bytes)
    if not isinstance(payload, dict):
        _refuse(
            "invalid_output_reconciliation",
            "every materialized payload must be a JSON object",
        )
    assert isinstance(payload, dict)
    count = payload.get("record_count")
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        _refuse(
            "invalid_output_reconciliation",
            "every materialized payload requires a non-negative record_count",
        )
    assert isinstance(count, int)
    return count


def _publish_atomically(
    *,
    output_root: Path,
    allowed_output_parent: Path,
    expected_files: Mapping[str, bytes],
) -> str:
    lock_path = allowed_output_parent / f".{output_root.name}.materialization.lock"
    try:
        lock_descriptor = os.open(
            lock_path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
    except FileExistsError as error:
        raise PropagationOutputRefusalError(
            "materialization_lock_exists",
            f"another materialization owns {lock_path.name}",
        ) from error
    try:
        os.close(lock_descriptor)
        if output_root.exists() or output_root.is_symlink():
            if _existing_bundle_is_identical(output_root, expected_files):
                return "unchanged"
            _refuse(
                "non_identical_overwrite_refused",
                "an existing output may only be reused when every byte is identical",
            )
        staging_root = Path(
            tempfile.mkdtemp(
                prefix=f".{output_root.name}.staging-",
                dir=allowed_output_parent,
            )
        )
        try:
            for name in sorted(expected_files):
                target = staging_root / name
                with target.open("xb") as stream:
                    stream.write(expected_files[name])
                    stream.flush()
                    os.fsync(stream.fileno())
            if output_root.exists() or output_root.is_symlink():
                _refuse(
                    "non_identical_overwrite_refused",
                    "the output appeared while its candidate bundle was staged",
                )
            staging_root.rename(output_root)
        except Exception:
            if staging_root.exists():
                shutil.rmtree(staging_root)
            raise
        return "created"
    finally:
        lock_path.unlink(missing_ok=True)


def _existing_bundle_is_identical(
    output_root: Path, expected_files: Mapping[str, bytes]
) -> bool:
    if output_root.is_symlink() or not output_root.is_dir():
        return False
    actual_entries = tuple(sorted(path.name for path in output_root.iterdir()))
    if actual_entries != tuple(sorted(expected_files)):
        return False
    return all(
        not (output_root / name).is_symlink()
        and (output_root / name).is_file()
        and (output_root / name).read_bytes() == expected
        for name, expected in expected_files.items()
    )


def _validate_output_location(output_root: Path, allowed_output_parent: Path) -> None:
    if not output_root.is_absolute() or not allowed_output_parent.is_absolute():
        _refuse(
            "unsafe_output_path",
            "output_root and allowed_output_parent must be absolute paths",
        )
    if ".." in output_root.parts or ".." in allowed_output_parent.parts:
        _refuse("unsafe_output_path", "parent traversal is not allowed")
    if allowed_output_parent.is_symlink() or not allowed_output_parent.is_dir():
        _refuse(
            "unsafe_output_path",
            "allowed_output_parent must be an existing non-symlink directory",
        )
    resolved_parent = allowed_output_parent.resolve(strict=True)
    if resolved_parent == Path(resolved_parent.anchor):
        _refuse("unsafe_output_path", "the filesystem root cannot own an output")
    if output_root.parent != allowed_output_parent or not output_root.name:
        _refuse(
            "unsafe_output_path",
            "output_root must be one direct child of allowed_output_parent",
        )
    if output_root.is_symlink():
        _refuse("unsafe_output_path", "a symlink cannot be an output root")
    if output_root.parent.resolve(strict=True) != resolved_parent:
        _refuse("unsafe_output_path", "output_root escapes its allowed parent")


def _canonical_json_bytes(payload: object) -> bytes:
    try:
        rendered = json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
    except (TypeError, ValueError) as error:
        raise PropagationOutputRefusalError(
            "invalid_output_serialization",
            "propagation output must be finite canonical JSON",
        ) from error
    return f"{rendered}\n".encode()


def _validate_sha256(value: object, *, field_name: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _refuse("invalid_build_identity", f"{field_name} must be a SHA-256 digest")
    assert isinstance(value, str)
    if any(character not in "0123456789abcdef" for character in value):
        _refuse(
            "invalid_build_identity",
            f"{field_name} must use lowercase hexadecimal",
        )


def _required_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _refuse("invalid_build_identity", f"{field_name} must be non-empty")
    assert isinstance(value, str)
    return value.strip()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _refuse(reason_code: str, detail: str) -> NoReturn:
    raise PropagationOutputRefusalError(reason_code, detail)
