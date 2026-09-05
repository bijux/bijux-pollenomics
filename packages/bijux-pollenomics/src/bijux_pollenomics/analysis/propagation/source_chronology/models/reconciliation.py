"""Country and whole-snapshot source-node accounting models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CountrySourceNodeReconciliation:
    """Country-owned denominators for source-node and chronology admission."""

    country_code: str
    input_observation_count: int
    pollen_observation_count: int
    eligible_observation_count: int
    refused_observation_count: int
    chronology_node_count: int
    source_taxon_identity_enrichment_count: int
    propagation_eligible_event_count: int
    node_counts_by_level: tuple[tuple[str, int], ...]
    node_observation_counts_by_level: tuple[tuple[str, int], ...]
    facet_refusal_reason_counts: tuple[tuple[str, int], ...]
    age_claim_count: int
    usable_canonical_age_claim_count: int
    canonical_coverage_younger_bp: float | int | None
    canonical_coverage_older_bp: float | int | None
    age_claim_status_counts: tuple[tuple[str, int], ...]
    age_claim_reason_counts: tuple[tuple[str, int], ...]
    refusal_reason_counts: tuple[tuple[str, int], ...]

    def as_dict(self) -> dict[str, object]:
        return {
            **dict(self.__dict__),
            "age_claim_status_counts": dict(self.age_claim_status_counts),
            "age_claim_reason_counts": dict(self.age_claim_reason_counts),
            "refusal_reason_counts": dict(self.refusal_reason_counts),
            "node_counts_by_level": dict(self.node_counts_by_level),
            "node_observation_counts_by_level": dict(
                self.node_observation_counts_by_level
            ),
            "facet_refusal_reason_counts": dict(self.facet_refusal_reason_counts),
        }


@dataclass(frozen=True)
class SourceNodeReconciliation:
    """Complete source-row denominator partition for one derivation."""

    input_observation_row_count: int
    unique_observation_count: int
    duplicate_observation_row_count: int
    governed_observation_count: int
    ungoverned_observation_count: int
    eligible_observation_count: int
    refused_observation_count: int
    chronology_node_count: int
    source_taxon_identity_enrichment_count: int
    propagation_eligible_event_count: int
    node_counts_by_level: tuple[tuple[str, int], ...]
    country_reconciliations: tuple[CountrySourceNodeReconciliation, ...]
    refusal_reason_counts: tuple[tuple[str, int], ...]
    facet_refusal_reason_counts: tuple[tuple[str, int], ...]

    def as_dict(self) -> dict[str, object]:
        return {
            **dict(self.__dict__),
            "country_reconciliations": {
                row.country_code: row.as_dict() for row in self.country_reconciliations
            },
            "refusal_reason_counts": dict(self.refusal_reason_counts),
            "facet_refusal_reason_counts": dict(self.facet_refusal_reason_counts),
            "node_counts_by_level": dict(self.node_counts_by_level),
        }


__all__ = ["CountrySourceNodeReconciliation", "SourceNodeReconciliation"]
