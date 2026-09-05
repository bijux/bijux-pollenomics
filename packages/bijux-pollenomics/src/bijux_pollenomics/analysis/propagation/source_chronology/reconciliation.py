"""Exact country-owned accounting for source-native chronology nodes."""

from __future__ import annotations

from collections import Counter
from collections.abc import Collection, Mapping, Sequence

from .admission import canonical_claim_interval, chronology_reason
from .constants import COUNTRY_CODES
from .identity import optional_text
from .models import (
    CountrySourceNodeReconciliation,
    SourceChronologyNode,
    SourceNodeAdmissionRefusal,
    SourceNodeFacetRefusal,
    SourceNodeReconciliation,
)


def build_reconciliation(
    *,
    input_observation_row_count: int,
    duplicate_observation_row_count: int,
    observations: Sequence[Mapping[str, object]],
    claims: Sequence[Mapping[str, object]],
    nodes: Sequence[SourceChronologyNode],
    admission_refusals: Sequence[SourceNodeAdmissionRefusal],
    facet_refusals: Sequence[SourceNodeFacetRefusal],
    source_taxon_enriched_observation_ids: Collection[str],
) -> SourceNodeReconciliation:
    """Build and verify exact country-owned denominator partitions."""
    country_rows: list[CountrySourceNodeReconciliation] = []
    for country in COUNTRY_CODES:
        country_observations = [
            row
            for row in observations
            if optional_text(row.get("country_code")) == country
        ]
        country_claims = [
            row for row in claims if optional_text(row.get("country_code")) == country
        ]
        canonical_intervals = [
            interval
            for row in country_claims
            if (interval := canonical_claim_interval(row)) is not None
        ]
        country_nodes = [node for node in nodes if node.country_code == country]
        country_refusals = [
            row for row in admission_refusals if row.country_code == country
        ]
        country_facet_refusals = [
            row for row in facet_refusals if row.country_code == country
        ]
        eligible_ids = {
            observation_id
            for node in country_nodes
            if node.node_level == "source_sample_presence"
            for observation_id in node.observation_ids
        }
        enriched_ids = eligible_ids.intersection(source_taxon_enriched_observation_ids)
        if len(country_observations) != len(eligible_ids) + len(country_refusals):
            raise AssertionError(f"{country} source-node denominator is incomplete")
        status_counts = Counter(
            optional_text(row.get("comparability_status")) or "unavailable"
            for row in country_claims
        )
        age_reason_counts = Counter(
            f"{optional_text(row.get('comparability_status')) or 'unavailable'}:"
            f"{chronology_reason(row) or 'none'}"
            for row in country_claims
            if canonical_claim_interval(row) is None
        )
        node_counts = Counter(node.node_level for node in country_nodes)
        node_observation_counts: Counter[str] = Counter()
        for node in country_nodes:
            node_observation_counts[node.node_level] += len(node.observation_ids)
        facet_refusal_levels = Counter(row.node_level for row in country_facet_refusals)
        for level in ("source_ecological_code", "source_taxon"):
            if node_observation_counts[level] + facet_refusal_levels[level] != len(
                eligible_ids
            ):
                raise AssertionError(f"{country} {level} denominator is incomplete")
        country_rows.append(
            CountrySourceNodeReconciliation(
                country_code=country,
                input_observation_count=len(country_observations),
                pollen_observation_count=sum(
                    optional_text(row.get("source_element_type")) == "pollen"
                    for row in country_observations
                ),
                eligible_observation_count=len(eligible_ids),
                refused_observation_count=len(country_refusals),
                chronology_node_count=len(country_nodes),
                source_taxon_identity_enrichment_count=len(enriched_ids),
                propagation_eligible_event_count=0,
                node_counts_by_level=tuple(sorted(node_counts.items())),
                node_observation_counts_by_level=tuple(
                    sorted(node_observation_counts.items())
                ),
                facet_refusal_reason_counts=tuple(
                    sorted(
                        Counter(
                            row.reason_code for row in country_facet_refusals
                        ).items()
                    )
                ),
                age_claim_count=len(country_claims),
                usable_canonical_age_claim_count=len(canonical_intervals),
                canonical_coverage_younger_bp=min(
                    (interval[0] for interval in canonical_intervals), default=None
                ),
                canonical_coverage_older_bp=max(
                    (interval[1] for interval in canonical_intervals), default=None
                ),
                age_claim_status_counts=tuple(sorted(status_counts.items())),
                age_claim_reason_counts=tuple(sorted(age_reason_counts.items())),
                refusal_reason_counts=tuple(
                    sorted(Counter(row.reason_code for row in country_refusals).items())
                ),
            )
        )

    unique_count = len(observations)
    governed_count = sum(
        optional_text(row.get("country_code")) in COUNTRY_CODES for row in observations
    )
    eligible_ids = {
        observation_id
        for node in nodes
        if node.node_level == "source_sample_presence"
        for observation_id in node.observation_ids
    }
    if unique_count != len(eligible_ids) + len(admission_refusals):
        raise AssertionError("source-node denominator partition is incomplete")
    if input_observation_row_count != unique_count + duplicate_observation_row_count:
        raise AssertionError("source-node duplicate accounting is incomplete")
    if not set(source_taxon_enriched_observation_ids) <= eligible_ids:
        raise AssertionError(
            "source taxon enrichment includes an ineligible observation"
        )
    node_counts = Counter(node.node_level for node in nodes)
    if any(node.propagation_eligible for node in nodes):
        raise AssertionError(
            "source chronology nodes must not become propagation events"
        )
    return SourceNodeReconciliation(
        input_observation_row_count=input_observation_row_count,
        unique_observation_count=unique_count,
        duplicate_observation_row_count=duplicate_observation_row_count,
        governed_observation_count=governed_count,
        ungoverned_observation_count=unique_count - governed_count,
        eligible_observation_count=len(eligible_ids),
        refused_observation_count=len(admission_refusals),
        chronology_node_count=len(nodes),
        source_taxon_identity_enrichment_count=len(
            source_taxon_enriched_observation_ids
        ),
        propagation_eligible_event_count=0,
        node_counts_by_level=tuple(sorted(node_counts.items())),
        country_reconciliations=tuple(country_rows),
        refusal_reason_counts=tuple(
            sorted(Counter(row.reason_code for row in admission_refusals).items())
        ),
        facet_refusal_reason_counts=tuple(
            sorted(Counter(row.reason_code for row in facet_refusals).items())
        ),
    )


__all__ = ["build_reconciliation"]
