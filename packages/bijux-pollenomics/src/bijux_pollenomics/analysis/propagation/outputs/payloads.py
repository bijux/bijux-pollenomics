"""Propagation event, candidate, reconciliation, and sensitivity payloads."""

from __future__ import annotations
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any
from bijux_pollenomics.analysis.propagation.network import (
    COUNTRY_CODES,
    EVIDENCE_DOMAINS,
    PROPAGATION_SENSITIVITY_SCENARIOS,
    PhenomenonEvent,
    PropagationNetworkResult,
    PropagationScenarioResult,
)
from bijux_pollenomics.analysis.propagation.candidates import (
    DEFAULT_PROPAGATION_SCENARIO,
)

from .codec import _refuse
from .inputs import _validate_records
from .models import _CANDIDATE_SCHEMA_NAME, _EVENT_SCHEMA_NAME


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
            "classification_contract_version": classification_contract_version,
            "classification_review_digest": classification_review_digest,
            "accepted_classification_mapping_count": (
                accepted_classification_mapping_count
            ),
            "propagation_contract_version": propagation_contract_version,
            "propagation_contract_digest": propagation_contract_digest,
            "propagation_producer_id": propagation_producer_id,
            "propagation_producer_version": propagation_producer_version,
            "propagation_producer_digest": propagation_producer_digest,
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
            "event_manifest_digest": primary_network.event_manifest_digest,
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
        if not isinstance(counts, dict):
            _refuse(
                "invalid_output_reconciliation",
                f"denominator partition counts are invalid: {name}",
            )
        if sum(counts.values()) != partition["total_count"]:
            _refuse(
                "invalid_output_reconciliation",
                f"denominator partition does not reconcile: {name}",
            )
