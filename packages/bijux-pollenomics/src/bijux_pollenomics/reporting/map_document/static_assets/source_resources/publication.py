"""Prepare bounded logical resource metadata parts without publishing files."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from ...source_resources import AtlasResourceCatalogue
from ..budgets import ATLAS_COMPRESSED_CHUNK_TARGET_BYTES
from ..nodes import partition_features
from .ancillary.publication import ancillary_counts, ancillary_groups
from .validation import (
    _digest,
    _index_entry,
    _record_id,
    _refuse_native_reader,
    validate_source_resource_payloads,
)


@dataclass(frozen=True)
class SourceResourcePayloads:
    """Detached logical parts awaiting the common Atlas transport envelope."""

    domain: dict[str, Any]
    payloads: tuple[dict[str, Any], ...]


def build_source_resource_payloads(
    catalogue: AtlasResourceCatalogue,
    *,
    target_bytes: int = ATLAS_COMPRESSED_CHUNK_TARGET_BYTES,
) -> SourceResourcePayloads:
    """Retain each full metadata record once and index its exact logical part.

    This owner neither reads native bodies nor writes an alternative asset tree.
    Common publication later binds parts to build IDs, script hashes and SRI.
    """
    if (
        type(target_bytes) is not int
        or not 0 < target_bytes <= ATLAS_COMPRESSED_CHUNK_TARGET_BYTES
    ):
        raise ValueError("Source resource partition target is invalid")
    anchor = _digest(catalogue.provenance.get("catalogue_manifest_sha256"))
    for resource in catalogue.resource_records:
        _refuse_native_reader(resource)
    groups = {
        "context": [
            {
                "record_id": "catalogue",
                "provenance": deepcopy(catalogue.provenance),
                "summary": deepcopy(catalogue.summary),
                "legacy_site_references": deepcopy(
                    list(catalogue.legacy_site_references)
                ),
            }
        ],
        "sites": deepcopy(list(catalogue.site_records)),
        "resources": deepcopy(list(catalogue.resource_records)),
        "descriptors": [
            {"record_id": digest, "descriptor": deepcopy(descriptor)}
            for digest, descriptor in sorted(catalogue.source_descriptors.items())
        ],
    }
    ancillary = ancillary_groups(catalogue)
    groups.update(ancillary)
    parts: list[dict[str, Any]] = []
    index: list[dict[str, Any]] = []
    for kind, records in groups.items():
        ordered = sorted(records, key=lambda row: _record_id(kind, row))
        for number, partition in enumerate(
            partition_features(ordered, target_bytes=target_bytes)
        ):
            part_id = f"{kind}:{number}"
            parts.append(_part(kind, part_id, partition, anchor))
            if kind != "context":
                index.extend(_index_entry(kind, row, part_id) for row in partition)
    index_parts = []
    for number, partition in enumerate(
        partition_features(index, target_bytes=target_bytes)
    ):
        part_id = f"index:{number}"
        parts.append(_part("index", part_id, partition, anchor))
        index_parts.append(part_id)
    domain = {
        "schema_version": "atlas-source-resources.v1",
        "source_family": "neotoma",
        "catalogue_manifest_sha256": anchor,
        "scientific_admission": "not_asserted",
        "numerical_atlas_denominator_changed": False,
        "initial_load": False,
        "payload_encoding": "gzip_base64",
        "record_count": len(catalogue.resource_records),
        "site_count": len(catalogue.site_records),
        "version_status_count": 2 * len(catalogue.resource_records),
        "source_descriptor_count": len(catalogue.source_descriptors),
        "legacy_site_reference_count": len(catalogue.legacy_site_references),
        "part_count": len(parts),
        "index_part_ids": index_parts,
        "context_part_id": "context:0",
    }
    if ancillary:
        domain.update(
            schema_version="atlas-source-resources.v2",
            ancillary_context_part_id="ancillary_context:0",
            **ancillary_counts(ancillary),
        )
    result = SourceResourcePayloads(domain=domain, payloads=tuple(parts))
    validate_source_resource_payloads(result, expected_catalogue_manifest_sha256=anchor)
    return result


def _part(
    kind: str, identity: str, records: list[dict[str, Any]], anchor: str
) -> dict[str, Any]:
    return {
        "schema_version": "atlas-source-resource-chunk.v1",
        "source_family": "neotoma",
        "catalogue_manifest_sha256": anchor,
        "scientific_admission": "not_asserted",
        "kind": kind,
        "part_id": identity,
        "records": records,
    }
