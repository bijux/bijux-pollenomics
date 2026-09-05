"""Scenario denominator and connected-component reconciliation."""

from __future__ import annotations
from collections import defaultdict

from .models import (
    COUNTRY_CODES,
    EVIDENCE_DOMAINS,
    PhenomenonEvent,
    PropagationCandidate,
    PropagationPairRefusal,
    ScenarioReconciliation,
    _CANDIDATE_STATUSES,
)


def _build_reconciliation(
    events: tuple[PhenomenonEvent, ...],
    eligible_events: tuple[PhenomenonEvent, ...],
    evaluated: tuple[PropagationCandidate, ...],
    refusals: tuple[PropagationPairRefusal, ...],
) -> ScenarioReconciliation:
    status_counts = dict.fromkeys(_CANDIDATE_STATUSES, 0)
    country_counts = {
        f"{source}-{target}": {**status_counts, "refused": 0}
        for source in COUNTRY_CODES
        for target in COUNTRY_CODES
    }
    for candidate in evaluated:
        status_counts[candidate.candidate_status] += 1
        country_counts[
            f"{candidate.source_country_code}-{candidate.target_country_code}"
        ][candidate.candidate_status] += 1
    for refusal in refusals:
        country_counts[f"{refusal.source_country_code}-{refusal.target_country_code}"][
            "refused"
        ] += 1
    return ScenarioReconciliation(
        input_event_count=len(events),
        eligible_event_count=len(eligible_events),
        excluded_non_pollen_event_count=len(events) - len(eligible_events),
        evidence_domain_event_counts=tuple(
            (
                domain,
                sum(event.evidence_domain == domain for event in events),
            )
            for domain in EVIDENCE_DOMAINS
        ),
        evaluated_pair_count=len(evaluated),
        refused_pair_count=len(refusals),
        status_counts=tuple(status_counts.items()),
        ordered_country_pair_counts=tuple(
            (key, tuple(counts.items())) for key, counts in country_counts.items()
        ),
        connected_component_count=_connected_component_count(evaluated),
    )


def _connected_component_count(rows: tuple[PropagationCandidate, ...]) -> int:
    adjacency: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if row.candidate_status not in {"definite_candidate", "possible_candidate"}:
            continue
        adjacency[row.source_event_id].add(row.target_event_id)
        adjacency[row.target_event_id].add(row.source_event_id)
    count = 0
    unseen = set(adjacency)
    while unseen:
        count += 1
        pending = [unseen.pop()]
        while pending:
            node = pending.pop()
            for neighbor in adjacency[node]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    pending.append(neighbor)
    return count


def _universe_key(event: PhenomenonEvent) -> tuple[str, ...]:
    return (
        event.evidence_domain,
        event.resolution,
        event.feature_key,
        event.accepted_taxon_concept_id or "",
        event.taxonomic_qualifier or "",
        event.threshold_profile_id,
        event.classification_contract_version or "",
        event.event_type,
        event.measurement_semantics_id,
        event.method_compatibility_key,
        event.temporal_contract_version,
    )
