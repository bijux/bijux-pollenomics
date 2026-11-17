"""Separate captured facet, occurrence and supporting metadata populations."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from ....source_resources import AtlasResourceCatalogue
from ....source_resources.ancillary.models import AtlasAncillarySupportingMetadata

SUPPORT_POPULATIONS = {
    "unit_metadata": "units",
    "reference_tables": "tables",
    "context_resources": "resources",
    "taxon_ancestry": "targets",
}


def ancillary_groups(
    catalogue: AtlasResourceCatalogue,
) -> dict[str, list[dict[str, Any]]]:
    """Partition metadata without changing native resource populations."""
    source = catalogue.ancillary
    if source is None:
        return {}
    groups = {
        "ancillary_context": [
            {
                "record_id": "ancillary",
                "source_manifest": deepcopy(source.source_manifest),
                "summary": deepcopy(source.summary),
                "provenance": deepcopy(source.provenance),
                "integrity_scope": source.integrity_scope,
                "entity_body_hashes_verified": source.entity_body_hashes_verified,
                "source_assessments_replayed": source.source_assessments_replayed,
            }
        ],
        "facet_slots": deepcopy(list(source.slots)),
        "ancillary_observations": deepcopy(list(source.observations)),
        "linked_occurrences": deepcopy(list(source.linked_occurrences)),
        "supporting_archives": [],
        "supporting_entries": [],
    }
    if isinstance(source, AtlasAncillarySupportingMetadata):
        for archive in source.supporting_archives:
            population = SUPPORT_POPULATIONS[archive["archive_kind"]]
            index = archive["index"]
            header = {
                key: deepcopy(value) for key, value in archive.items() if key != "index"
            }
            header.update(
                index_population=population,
                index_record_count=len(index[population]),
                index_metadata={
                    key: deepcopy(value)
                    for key, value in index.items()
                    if key != population
                },
            )
            groups["supporting_archives"].append(header)
            for number, row in enumerate(index[population]):
                groups["supporting_entries"].append(
                    {
                        "archive_kind": archive["archive_kind"],
                        "archive_manifest_sha256": archive["archive_manifest_sha256"],
                        "population": population,
                        "row_index": number,
                        "entry": deepcopy(row),
                    }
                )
    return groups


def ancillary_counts(groups: dict[str, Any]) -> dict[str, int]:
    """Count each recorded metadata population independently."""
    observations = groups["ancillary_observations"]
    rows = observations.values() if isinstance(observations, dict) else observations
    kinds = [row["kind"] for row in rows]
    return {
        "ancillary_slot_count": len(groups["facet_slots"]),
        "ancillary_observation_count": len(observations),
        "ancillary_facet_observation_count": kinds.count("facet"),
        "ancillary_linked_observation_count": kinds.count("linked"),
        "ancillary_linked_occurrence_count": len(groups["linked_occurrences"]),
        "supporting_archive_count": len(groups["supporting_archives"]),
        "supporting_entry_count": len(groups["supporting_entries"]),
    }


def ancillary_index_entry(
    kind: str, row: Mapping[str, Any], part_id: str, identity: str
) -> dict[str, Any]:
    """Project indexed owner fields for lazy selected metadata validation."""
    result: dict[str, Any] = {
        "entity_type": kind,
        "record_id": identity,
        "part_id": part_id,
    }
    if kind == "facet_slots":
        result.update(
            root_dataset_id=row["root_identity"]["dataset_id"],
            facet=row["facet"],
            current_use_role=row["current_use_role"],
            coverage_status=row["coverage_status"],
            site_id=row["root_identity"]["site_id"],
            collection_unit_id=row["root_identity"]["collection_unit_id"],
            dataset_type=row["root_identity"]["dataset_type"],
            current_declared_role=row["current_declared_role"],
        )
    elif kind == "ancillary_observations":
        result.update(
            {
                key: row[key]
                for key in (
                    "kind",
                    "terminal_status",
                    "current_owner_join",
                    "current_use_role",
                    "source_capture_manifest_sha256",
                    "capture_epoch",
                )
            }
        )
        if row["kind"] == "facet":
            result.update(
                root_dataset_id=row["root_identity"]["dataset_id"],
                facet=row["facet"],
                facet_key=row["facet_key"],
                site_id=row["root_identity"]["site_id"],
                collection_unit_id=row["root_identity"]["collection_unit_id"],
                dataset_type=row["root_identity"]["dataset_type"],
                original_role=row.get("parent_scope_role"),
            )
        else:
            result.update(
                linked_kind=row["identity"]["kind"],
                native_id=row["identity"]["native_id"],
            )
    elif kind == "linked_occurrences":
        result.update(
            observation_id=row["observation_id"],
            root_dataset_id=row.get(
                "root_dataset_id", row.get("source_proof", {}).get("root_dataset_id")
            ),
            current_owner_join=row["current_owner_join"],
            current_use_role=row["current_use_role"],
        )
    elif kind == "supporting_archives":
        result.update(
            archive_kind=row["archive_kind"],
            archive_manifest_sha256=row["archive_manifest_sha256"],
        )
    elif kind == "supporting_entries":
        result.update(
            archive_kind=row["archive_kind"],
            archive_manifest_sha256=row["archive_manifest_sha256"],
            row_index=row["row_index"],
            population=row["population"],
        )
        entry = row["entry"]
        result["source_selectors"] = {
            key: deepcopy(value)
            for key, value in entry.items()
            if key
            in {
                "unit_key",
                "resource_key",
                "table_key",
                "table",
                "site_id",
                "terminal_status",
            }
            or row["archive_kind"] == "taxon_ancestry"
            and key in {"target_key", "kind", "native_id"}
        }
        result["scope"] = deepcopy(entry.get("scope"))
    return result
