"""Adapt canonical Neotoma concept accounting into review rows without remapping."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import PurePosixPath
from typing import Any, cast

from bijux_pollenomics.evidence.classification import (
    build_neotoma_classification_accounting,
)

from ..source_completion.evidence import EvidenceReader
from .rows import Occurrences, review_row


def neotoma_rows(reader: EvidenceReader) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest_path = "data/neotoma/relational/manifest.json"
    manifest = reader.json(manifest_path)
    if manifest is None:
        raise ValueError("Neotoma relational authority is missing")
    snapshot: dict[str, Any] = {
        key: manifest[key]
        for key in ("source_family", "source_snapshot_id", "build_id")
    }
    for name in ("observations", "variables", "sites"):
        surface = manifest["surfaces"][name]
        rows = []
        for part in surface["parts"]:
            relative = str(PurePosixPath(manifest_path).parent / part["path"])
            reader.verify(relative, part)
            payload = reader.json(relative)
            if payload is None or len(payload["rows"]) != part["row_count"]:
                raise ValueError(f"Missing or inconsistent Neotoma part: {relative}")
            rows.extend(payload["rows"])
        if len(rows) != surface["row_count"]:
            raise ValueError(f"Neotoma surface count does not reconcile: {name}")
        snapshot[name] = rows
    accounting = cast(dict[str, Any], build_neotoma_classification_accounting(snapshot))
    memberships = {
        row["observation_id"]: row for row in accounting["observation_memberships"]
    }
    counts = Occurrences()
    source_countries: dict[str, Counter[str]] = defaultdict(Counter)
    for observation in snapshot["observations"]:
        membership = memberships[observation["observation_id"]]
        source_countries[membership["classification_concept_id"]][
            membership["source_country_code"] or "UNASSIGNED"
        ] += 1
        counts.add(
            membership["classification_concept_id"],
            observation["observation_id"],
            country=membership["governed_country_code"],
            unit=observation.get("source_unit"),
            value=observation.get("source_value"),
        )
    output = []
    covered_variables = set()
    for concept in accounting["concepts"]:
        key = concept["classification_concept_id"]
        covered_variables.add(concept["source_variable_id"])
        row = review_row(
            row_id=key,
            source="neotoma",
            native_id=concept["source_taxon_id"],
            label=concept["source_reported_name"],
            domain=concept["source_evidence_universe"],
            evidence=concept,
        )
        row.update(
            source_element_type=concept["source_element_type"],
            source_units=[concept["source_unit"]],
            source_groups=[concept["source_ecological_group"]],
            current_mapping_status=concept["mapping_status"],
            current_mapping_status_namespace="canonical_neotoma_classification_mapping_status",
            qualifier_markers=concept["source_label_qualifier_markers"],
            proposed_primary_group_id=concept["primary_group_id"],
            proposed_primary_subgroup_id=concept["primary_subgroup_id"],
            proposed_role_ids=concept["role_ids"],
        )
        counts.annotate(row, key)
        row["country_dimension"] = "governed_country_code"
        row["source_country_counts"] = dict(sorted(source_countries[key].items()))
        output.append(row)
    for variable in snapshot["variables"]:
        if variable["variable_id"] not in covered_variables:
            row = review_row(
                row_id=f"neotoma:unused-variable:{variable['variable_id']}",
                source="neotoma",
                native_id=variable["source_taxon_id"],
                label=variable["source_reported_name"],
                domain="source_lookup_without_observation",
                evidence=variable,
            )
            row.update(observation_count=0, source_units=variable["source_units"])
            output.append(row)
    return output, {
        "reconciliation": accounting["reconciliation"],
        "review": accounting["review"],
        "partitions": accounting["partitions"],
        "source_snapshot_id": manifest["source_snapshot_id"],
        "variable_count": len(snapshot["variables"]),
    }
