"""Reuse every governed SEAD candidate and account taxonless observations separately."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any

from bijux_pollenomics.collection.sources.sead.evidence.review import (
    validate_sead_scientific_classification_review,
)

from ..source_completion.evidence import EvidenceReader, indexed_rows
from .rows import Occurrences, review_row


def sead_rows(reader: EvidenceReader) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Preserve governed SEAD candidates and count taxonless observations."""
    path = "data/sead/review/scientific_classification_review.json"
    packet = reader.json(path)
    if packet is None:
        raise ValueError("SEAD scientific candidate authority is missing")
    validate_sead_scientific_classification_review(packet)
    registry = reader.json("data/source_fact_ownership_registry.json")
    if registry is None:
        raise ValueError("Source fact ownership authority is missing")
    owners = indexed_rows(registry, "fact_key")
    native_path = owners["sead_source_native_observations"]["governing_surface_path"]
    native = reader.json(native_path)
    if native is None:
        raise ValueError("SEAD source-native observation authority is missing")
    counts = Occurrences()
    for part in native["partitioned_fields"]["observations"]["parts"]:
        relative = str(PurePosixPath(native_path).parent / part["path"])
        reader.verify(relative, part)
        payload = reader.json(relative)
        if payload is None or len(payload["observations"]) != part["row_count"]:
            raise ValueError(
                f"Missing or inconsistent SEAD observation part: {relative}"
            )
        for observation in payload["observations"]:
            key = (
                observation.get("taxon_relation_id")
                or "sead:unresolved-taxon-observations"
            )
            unit_id = observation["source_semantics"].get("source_unit_id")
            unit = (
                None
                if unit_id is None
                else f"sead-unit:{unit_id}:{observation['source_value_field']}"
            )
            counts.add(
                key,
                observation["observation_id"],
                country=observation.get("country_code"),
                unit=unit,
                value=observation.get("source_value"),
            )
    if len(counts.ids) != native["observation_count"]:
        raise ValueError("SEAD observations do not reconcile with native authority")
    output = []
    expected_keys = set()
    for candidate in packet["candidates"]:
        key = candidate["taxon_relation_id"]
        expected_keys.add(key)
        row = review_row(
            row_id=candidate["candidate_id"],
            source="sead",
            native_id=candidate["taxon_id"],
            label=candidate["source_species"],
            domain="source_native_taxon_not_accepted_as_pollen",
            evidence=candidate,
        )
        row.update(
            source_genus_name=candidate["source_genus_name"],
            source_family_name=candidate["source_family_name"],
            source_order_name=candidate["source_order_name"],
            source_groups=candidate["source_ecocodes"],
            current_mapping_status=candidate["current_classification_status"],
            current_mapping_status_namespace="sead_source_candidate_classification_status",
            proposed_primary_group_id=candidate["proposed_primary_group_id"],
            proposed_primary_subgroup_id=candidate["proposed_primary_subgroup_id"],
            proposed_role_ids=candidate["proposed_role_ids"] or [],
        )
        counts.annotate(row, key)
        row["country_dimension"] = "governed_source_native_observation_country_code"
        output.append(row)
    for key in sorted(set(counts.counts) - expected_keys):
        row = review_row(
            row_id=key,
            source="sead",
            native_id=None,
            label=None,
            domain="observations_without_reviewed_taxon_identity",
            evidence={"taxon_relation_id": key},
        )
        row["current_mapping_status"] = "unresolved"
        counts.annotate(row, key)
        row["country_dimension"] = "governed_source_native_observation_country_code"
        output.append(row)
    return output, {
        "lineage": packet["lineage"],
        "taxonomic_inventory": packet["taxonomic_inventory"],
        "citation_audit": packet["citation_audit"],
        "observation_count": len(counts.ids),
        "candidate_count": len(packet["candidates"]),
        "canonical_returned_decision_import_supported": False,
        "import_blocker": "Existing SEAD validator requires pending/null review fields; coordinator must govern an acceptance transition before canonical write.",
    }
