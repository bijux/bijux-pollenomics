"""Deterministic relational table and country reconciliation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping

from bijux_pollenomics.evidence.sources.neotoma.contract import (
    SOURCE_OCCURRENCE_COUNTER_FIELDS,
    accumulate_source_occurrence_refusals,
)

from .contracts import COUNTRY_COUNT_FIELDS, TABLE_ID_FIELDS
from .country import country_attribution_counts
from .state import RelationalBuildState
from .variables import finalize_variables


def build_snapshot_payload(state: RelationalBuildState) -> dict[str, object]:
    normalized_tables = {
        name: sorted(
            records.values(),
            key=lambda item: str(item[TABLE_ID_FIELDS[name]]),
        )
        for name, records in state.tables.items()
    }
    finalize_variables(normalized_tables["variables"])
    normalized_counts = {name: len(rows) for name, rows in normalized_tables.items()}
    for country_code, counts in state.country_counts.items():
        counts["sites"] = sum(
            1
            for site in normalized_tables["sites"]
            if site.get("country_code") == country_code
        )
        counts["collection_units"] = sum(
            1
            for unit in normalized_tables["collection_units"]
            if parent_country(unit, normalized_tables["sites"]) == country_code
        )
        counts["datasets"] = sum(
            1
            for dataset_record in normalized_tables["datasets"]
            if parent_country(dataset_record, normalized_tables["sites"])
            == country_code
        )
        counts["samples"] = sum(
            1
            for sample_record in normalized_tables["samples"]
            if sample_record.get("country_code") == country_code
        )
        counts["chronologies"] = sum(
            1
            for chronology_record in normalized_tables["chronologies"]
            if chronology_record.get("country_code") == country_code
        )
        counts["chronology_controls"] = sum(
            1
            for control_record in normalized_tables["chronology_controls"]
            if control_record.get("country_code") == country_code
        )
        # These country bins describe normalized surfaces, as required by the
        # materialization contract. Global source and age counters retain visits.
        country_claims = [
            claim
            for claim in normalized_tables["age_claims"]
            if claim.get("country_code") == country_code
        ]
        counts["age_claim_rows"] = len(country_claims)
        for posture in ("comparable", "context_only", "refused", "unresolved"):
            counts[f"age_{posture}"] = sum(
                claim["comparability_status"] == posture for claim in country_claims
            )
        counts["observation_rows"] = sum(
            observation.get("country_code") == country_code
            for observation in normalized_tables["observations"]
        )
        counts["variables"] = len(
            {
                observation["variable_id"]
                for observation in normalized_tables["observations"]
                if observation.get("country_code") == country_code
            }
        )
        for status in ("assigned", "review", "unassigned", "refused"):
            counts[f"{status}_sites"] = sum(
                1
                for site in normalized_tables["sites"]
                if site.get("country_code") == country_code
                and site.get("country_decision_status") == status
            )
        counts["propagation_eligible_sites"] = sum(
            1
            for site in normalized_tables["sites"]
            if site.get("country_code") == country_code
            and site.get("country_propagation_eligible") is True
        )
        for field in COUNTRY_COUNT_FIELDS:
            counts[field] += 0

    unit_family_counts = Counter(
        str(observation["unit_family"])
        for observation in normalized_tables["observations"]
    )
    variable_semantic_variant_count = 0
    for variable in normalized_tables["variables"]:
        source_semantics = variable.get("source_semantics")
        if isinstance(source_semantics, list):
            variable_semantic_variant_count += len(source_semantics)

    refusals: dict[str, Counter[str]] = {}
    accumulate_source_occurrence_refusals(state.orphans, counts=refusals)
    state.conflicts.sort(key=lambda item: str(item["conflict_id"]))
    state.orphans.sort(key=lambda item: str(item["orphan_id"]))
    return {
        "schema_version": "neotoma-relational-snapshot.v2",
        "source_family": "neotoma",
        "source_snapshot_id": state.source_snapshot_id,
        "build_id": state.build_id,
        **normalized_tables,
        "reconciliation": {
            "source_row_counts": dict(sorted(state.source_counts.items())),
            "normalized_row_counts": normalized_counts,
            "source_occurrence_accounting": _source_occurrence_accounting(
                state, normalized_counts
            ),
            "unregistered_source_occurrence_counts_by_reason": {
                surface: dict(sorted(refusals.get(counter, Counter()).items()))
                for surface, counter in SOURCE_OCCURRENCE_COUNTER_FIELDS.items()
            },
            "age_comparability_counts": dict(sorted(state.age_postures.items())),
            "age_reason_counts": dict(sorted(state.age_reasons.items())),
            "source_unit_counts": dict(sorted(state.unit_counts.items())),
            "unit_family_counts": dict(sorted(unit_family_counts.items())),
            "variable_semantic_variant_count": variable_semantic_variant_count,
            "country_counts": {
                code: dict(sorted(counts.items()))
                for code, counts in state.country_counts.items()
            },
            "country_attribution_counts": country_attribution_counts(
                normalized_tables["sites"]
            ),
            "conflict_count": len(state.conflicts),
            "orphan_count": len(state.orphans),
        },
        "conflicts": state.conflicts,
        "orphans": state.orphans,
    }


def _source_occurrence_accounting(
    state: RelationalBuildState, normalized_counts: Mapping[str, int]
) -> dict[str, object]:
    """Reconcile encountered native entity projections without another row index.

    Registration visits are partitioned into retained rows, identical repeats
    and unselected distinct variants. Existing conflict variants supply the
    latter population even when a repeated variant is not the canonical winner.
    Thus A/B/B and B/B/A have identical counts. These are entity occurrences,
    not independent observation trials: repeated site metadata is legitimate,
    and identical datum entries within a sample retain their distinct row IDs.

    Source counters include extractable native descendants of refused parents.
    Their payload is retained once in an orphan with exact exclusion counters.
    Unregistered occurrences are not the orphan total: fallback rows can retain
    an identity diagnostic and still be registered. Variables are derived lookup
    semantics and excluded from this native-row partition.
    """
    kinds = {
        "sites": "site_payload_conflict",
        "collection_units": "collection_unit_payload_conflict",
        "datasets": "dataset_payload_conflict",
        "chronologies": "chronology_payload_conflict",
        "chronology_controls": "chronology_control_payload_conflict",
        "samples": "sample_payload_conflict",
        "age_claims": "age_claim_identity_conflict",
        "observations": "observation_identity_conflict",
    }
    additional_variants: Counter[str] = Counter()
    by_kind = {kind: surface for surface, kind in kinds.items()}
    for conflict in state.conflicts:
        surface = by_kind.get(str(conflict["conflict_kind"]))
        detail = conflict["detail"]
        if surface is None or not isinstance(detail, Mapping):
            continue
        variants = detail.get("variants")
        if (
            detail.get("resolution") != "canonical_minimum"
            or not isinstance(variants, list)
            or conflict["subject_id"] not in state.tables[surface]
        ):
            raise ValueError("Native entity conflict variant accounting is invalid")
        additional_variants[surface] += len(variants) - 1
    result: dict[str, object] = {}
    for surface, counter in SOURCE_OCCURRENCE_COUNTER_FIELDS.items():
        registered = state.registered_occurrences[TABLE_ID_FIELDS[surface]]
        unselected = additional_variants[surface]
        repeated = registered - normalized_counts[surface] - unselected
        unregistered = state.source_counts[counter] - registered
        if min(repeated, unselected, unregistered) < 0:
            raise ValueError("Native source occurrence partition is negative")
        result[surface] = {
            "source_counter": counter,
            "registered_occurrences": registered,
            "unregistered_source_occurrences": unregistered,
            "excluded_occurrence_counts": {
                "repeated_identical_entity_record": repeated,
                "unselected_conflicting_entity_variant": unselected,
            },
        }
    return result


def parent_country(record: Mapping[str, object], sites: list[dict[str, object]]) -> str:
    site_id = record.get("site_id")
    for site in sites:
        if site.get("site_id") == site_id:
            return str(site.get("country_code", "UNASSIGNED"))
    return "UNASSIGNED"
