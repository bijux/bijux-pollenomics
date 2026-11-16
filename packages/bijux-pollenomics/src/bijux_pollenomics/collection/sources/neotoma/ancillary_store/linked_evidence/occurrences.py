"""Bind legacy inline occurrences and scoped immutable evidence references."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ...capture.linked_resources.protocol import _RANK
from ...resource_catalogue.source_projection import _same


def verify_linked_metadata_sources(
    documents: dict[str, Any],
    controls: dict[str, Any],
    descriptors: dict[str, Any],
    linked: Mapping[str, Path],
) -> None:
    """Bind each declared occurrence to predecessor metadata; defer native field values."""
    relations = {
        "chronology_preparer": ("chronologies", "contact"),
        "dataset_contributor": ("contacts", "contact"),
        "dataset_publication": ("publications", "publication"),
        "dataset_reported_taxon": ("taxa", "taxon"),
        "taxonomic_reference_publication": ("taxa", "publication"),
        "source_reported_higher_taxon": ("taxa", "taxon"),
    }
    for digest in linked:
        for target in controls[digest]["targets"]:
            roles = []
            for proof in target["source_proofs"]:
                if not isinstance(proof, dict):
                    raise ValueError("Ancillary linked occurrence proof is malformed")
                source = proof.get("source_capture_manifest_sha256")
                if (
                    not isinstance(source, str)
                    or source
                    not in controls[digest]["plan"]["source_facet_manifest_sha256s"]
                    or source not in descriptors
                    or descriptors[source]["kind"] != "facet"
                ):
                    raise ValueError("Ancillary linked occurrence predecessor differs")
                entry = next(
                    (
                        row
                        for row in documents[source]["facets"]
                        if row["facet_key"] == proof.get("source_facet_key")
                    ),
                    None,
                )
                if (
                    entry is None
                    or not entry["attempts"]
                    or "body_file" not in entry["attempts"][-1]
                ):
                    raise ValueError(
                        "Ancillary linked occurrence has no source entity declaration"
                    )
                attempt = entry["attempts"][-1]
                role = (
                    entry.get("parent_scope_role")
                    or entry["root_identity"]["exposure_role"]
                )
                relation, pointer = proof.get("relation"), proof.get("json_pointer")
                if (
                    not isinstance(relation, str)
                    or relation not in relations
                    or relations[relation] != (entry["facet"], target["kind"])
                    or not isinstance(pointer, str)
                    or not pointer.startswith("/data/")
                    or "\x00" in pointer
                ):
                    raise ValueError(
                        "Ancillary linked occurrence relation or pointer differs"
                    )
                higher = relation == "source_reported_higher_taxon"
                if higher and not controls[digest]["plan"]["include_higher_taxa"]:
                    raise ValueError(
                        "Ancillary linked occurrence is outside source selection"
                    )
                expected = {
                    "source_capture_manifest_sha256": source,
                    "source_facet_key": entry["facet_key"],
                    "source_receipt_sha256": attempt["receipt_sha256"],
                    "source_body_sha256": descriptors[source]["files"][
                        attempt["body_file"]
                    ]["sha256"],
                    "root_dataset_id": entry["root_identity"]["dataset_id"],
                    "root_identity": entry["root_identity"],
                    "inherited_exposure_role": role,
                    "content_version": entry["content_version"],
                    "api_version": entry["api_version"],
                    "target_kind": target["kind"],
                    "native_id": target["native_id"],
                    "json_pointer": pointer,
                    "relation": relation,
                    "optional_higher_taxon": higher,
                }
                if not _same(proof, expected):
                    raise ValueError(
                        "Ancillary linked occurrence metadata correspondence differs"
                    )
                roles.append(role)
            if target["exposure_role"] != max(roles, key=lambda role: _RANK[role]):
                raise ValueError("Ancillary linked occurrence inherited role differs")


def verify_scoped_metadata_sources(
    document: dict[str, Any],
    control: dict[str, Any],
    context: Any,
    evidence_sources: Mapping[str, Path] | None,
) -> str:
    """Authenticate all selected references without expanding them into the index."""
    from .metadata import _verify_scoped_metadata_selection

    return _verify_scoped_metadata_selection(
        document, control, context, evidence_sources
    )
