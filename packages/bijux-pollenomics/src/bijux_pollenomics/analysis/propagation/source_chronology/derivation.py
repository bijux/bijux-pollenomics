"""Neotoma source-native chronological-node derivation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .admission import source_refusal_reason
from .construction import build_source_chronology_nodes
from .identity import digest, observation_index, optional_text, unique_index
from .indexing import source_default_chronologies
from .models import (
    SourceNodeAdmissionRefusal,
    SourceNodeContext,
    SourceNodeDerivationResult,
)
from .reconciliation import build_reconciliation
from .source_identity import (
    enrich_source_identity,
    source_taxon_identity_was_enriched,
)


def derive_neotoma_source_chronology_nodes(
    *,
    observations: Sequence[Mapping[str, object]],
    samples: Sequence[Mapping[str, object]],
    sites: Sequence[Mapping[str, object]],
    variables: Sequence[Mapping[str, object]],
    chronologies: Sequence[Mapping[str, object]],
    context: SourceNodeContext,
) -> SourceNodeDerivationResult:
    """Derive dated source context nodes with propagation explicitly refused.

    Nodes group stable observation evidence at sample-presence, literal source-code,
    and exact source-taxon levels. They are not reviewed pollen-sum events,
    ecological classifications, or propagation candidates.
    """
    observation_rows, duplicate_ids, duplicate_row_count = observation_index(
        observations
    )
    sample_index, sample_conflicts = unique_index(samples, "sample_id")
    site_index, site_conflicts = unique_index(sites, "site_id")
    variable_index, variable_conflicts = unique_index(variables, "variable_id")
    default_chronologies = source_default_chronologies(chronologies)
    refusals: list[SourceNodeAdmissionRefusal] = []
    source_taxon_enriched_ids: set[str] = set()
    admitted: list[
        tuple[
            Mapping[str, object],
            Mapping[str, object],
            Mapping[str, object],
            Mapping[str, object],
        ]
    ] = []

    for observation_id in sorted(observation_rows):
        observation = observation_rows[observation_id]
        country = optional_text(observation.get("country_code")) or "UNASSIGNED"
        reason: str | None = None
        chronology_detail: str | None = None
        if observation_id in duplicate_ids:
            reason = "duplicate_source_observation"
        sample_id = optional_text(observation.get("sample_id"))
        site_id = optional_text(observation.get("site_id"))
        variable_id = optional_text(observation.get("variable_id"))
        sample = sample_index.get(sample_id or "")
        site = site_index.get(site_id or "")
        variable = variable_index.get(variable_id or "")
        if reason is None and sample_id in sample_conflicts:
            reason = "conflicting_sample"
        if reason is None and site_id in site_conflicts:
            reason = "conflicting_site"
        if reason is None and variable_id in variable_conflicts:
            reason = "conflicting_variable"
        defaults = default_chronologies.get(sample_id or "", ())
        claim = defaults[0] if len(defaults) == 1 else None
        if reason is None and len(defaults) > 1:
            reason = "ambiguous_source_default_chronology"
        if reason is None:
            reason, chronology_detail = source_refusal_reason(
                observation, sample, site, claim
            )
        enriched_observation = dict(observation)
        if reason is None and variable is None:
            reason = "missing_variable"
        if reason is None and variable is not None:
            enriched_observation, reason = enrich_source_identity(observation, variable)
            if reason is None and source_taxon_identity_was_enriched(
                observation, enriched_observation
            ):
                source_taxon_enriched_ids.add(observation_id)
        if reason is None and (
            optional_text(observation.get("source_snapshot_id"))
            != context.source_snapshot_id
            or optional_text(observation.get("build_id")) != context.build_id
        ):
            reason = "source_context_lineage_mismatch"
        if reason is not None:
            refusals.append(
                SourceNodeAdmissionRefusal(
                    observation_id=observation_id,
                    country_code=country,
                    reason_code=reason,
                    chronology_reason_code=chronology_detail,
                )
            )
            continue
        if sample is None or site is None or claim is None:
            raise AssertionError("admission accepted incomplete source relations")
        admitted.append((enriched_observation, sample, site, claim))

    nodes, facet_refusals = build_source_chronology_nodes(admitted, context)
    refusals_tuple = tuple(
        sorted(refusals, key=lambda row: (row.country_code, row.observation_id))
    )
    reconciliation = build_reconciliation(
        input_observation_row_count=len(observations),
        duplicate_observation_row_count=duplicate_row_count,
        observations=tuple(observation_rows.values()),
        claims=chronologies,
        nodes=nodes,
        admission_refusals=refusals_tuple,
        facet_refusals=facet_refusals,
        source_taxon_enriched_observation_ids=source_taxon_enriched_ids,
    )
    status = (
        "materialized_with_refusals"
        if nodes and (refusals_tuple or facet_refusals)
        else "materialized"
        if nodes
        else "refused"
    )
    payload = {
        "context": context.as_dict(),
        "nodes": [node.as_dict() for node in nodes],
        "admission_refusals": [row.as_dict() for row in refusals_tuple],
        "facet_refusals": [row.as_dict() for row in facet_refusals],
        "reconciliation": reconciliation.as_dict(),
        "derivation_status": status,
    }
    return SourceNodeDerivationResult(
        context=context,
        nodes=nodes,
        admission_refusals=refusals_tuple,
        facet_refusals=facet_refusals,
        reconciliation=reconciliation,
        derivation_status=status,
        result_digest=digest(payload),
    )


__all__ = ["derive_neotoma_source_chronology_nodes"]
