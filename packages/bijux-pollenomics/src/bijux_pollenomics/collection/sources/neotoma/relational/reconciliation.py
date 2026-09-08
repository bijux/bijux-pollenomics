"""Deterministic relational table and country reconciliation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping

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


def parent_country(record: Mapping[str, object], sites: list[dict[str, object]]) -> str:
    site_id = record.get("site_id")
    for site in sites:
        if site.get("site_id") == site_id:
            return str(site.get("country_code", "UNASSIGNED"))
    return "UNASSIGNED"
