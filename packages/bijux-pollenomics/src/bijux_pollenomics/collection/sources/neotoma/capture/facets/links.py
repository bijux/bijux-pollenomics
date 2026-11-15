"""Bound direct native link occurrences to authenticated facet buffers and root roles."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..resources.models import DEFAULT_RESOURCE_LIMITS, NeotomaResourceLimits
from .models import NeotomaFacetScopeInputs
from .qualification import qualify_neotoma_facet_capture


def discover_neotoma_facet_links(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    include_higher_taxa: bool = False,
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
    scope_inputs: Mapping[str, NeotomaFacetScopeInputs] | None = None,
) -> dict[str, Any]:
    """Collect direct references only; targets are proposals, never authorization to GET."""
    if type(include_higher_taxa) is not bool:
        raise ValueError("higher taxon lead selection must be a boolean")
    qualified = qualify_neotoma_facet_capture(
        directory,
        expected_manifest_sha256=expected_manifest_sha256,
        limits=limits,
        scope_inputs=scope_inputs,
    )
    links: list[dict[str, Any]] = []
    higher: list[dict[str, Any]] = []
    unavailable: list[dict[str, Any]] = []
    for entry in qualified["entries"]:
        if entry["qualification_status"] != "qualified_source_schema":
            unavailable.append(
                {
                    "source_facet_key": entry["source_facet_key"],
                    "reason": entry["reason"],
                }
            )
            continue
        scope = {
            key: entry[key]
            for key in (
                "source_capture_manifest_sha256",
                "source_facet_key",
                "source_body_sha256",
                "source_receipt_sha256",
                "content_version",
                "api_version",
            )
        }
        scope.update(
            root_dataset_id=entry["root_identity"]["dataset_id"],
            root_identity=entry["root_identity"],
            inherited_exposure_role=entry.get("effective_parent_scope_role")
            or entry["root_identity"]["exposure_role"],
        )

        def add(
            kind: str,
            native_id: Any,
            pointer: str,
            relation: str,
            scope: dict[str, Any] = scope,
        ) -> None:
            record = {
                **scope,
                "target_kind": kind,
                "native_id": native_id,
                "json_pointer": pointer,
                "relation": relation,
                "optional_higher_taxon": relation == "source_reported_higher_taxon",
            }
            if native_id is None:
                unavailable.append({**record, "reason": "source_null_native_id"})
            elif relation == "source_reported_higher_taxon":
                higher.append(record)
            else:
                links.append(record)

        data = entry["source_payload"]["data"]
        if entry["facet"] == "chronologies":
            for index, row in enumerate(data):
                add(
                    "contact",
                    row["chronology"]["preparedby"]["contactid"],
                    f"/data/{index}/chronology/preparedby/contactid",
                    "chronology_preparer",
                )
        elif entry["facet"] == "contacts":
            for index, row in enumerate(data):
                for contact_index, contact in enumerate(row["contacts"]["contacts"]):
                    add(
                        "contact",
                        contact["contactid"],
                        f"/data/{index}/contacts/contacts/{contact_index}/contactid",
                        "dataset_contributor",
                    )
        elif entry["facet"] == "publications":
            for index, row in enumerate(data):
                add(
                    "publication",
                    row["publication"]["publicationid"],
                    f"/data/{index}/publication/publicationid",
                    "dataset_publication",
                )
        elif entry["facet"] == "taxa":
            if entry.get("population_status") == "source_null_aggregate_placeholder":
                continue
            for index, row in enumerate(data):
                add(
                    "taxon",
                    row["taxonid"],
                    f"/data/{index}/taxonid",
                    "dataset_reported_taxon",
                )
                add(
                    "publication",
                    row["publicationid"],
                    f"/data/{index}/publicationid",
                    "taxonomic_reference_publication",
                )
                add(
                    "taxon",
                    row["highertaxonid"],
                    f"/data/{index}/highertaxonid",
                    "source_reported_higher_taxon",
                )
    if include_higher_taxa:
        links.extend(higher)
    # Keep root scope in the key: a shared target must not erase a protected sibling role.
    targets: dict[tuple[str, int, int, str], dict[str, Any]] = {}
    for index, link in enumerate(links):
        key = (
            link["target_kind"],
            link["native_id"],
            link["root_dataset_id"],
            link["inherited_exposure_role"],
        )
        if key not in targets:
            targets[key] = {
                field: link[field]
                for field in (
                    "target_kind",
                    "native_id",
                    "root_dataset_id",
                    "root_identity",
                    "inherited_exposure_role",
                )
            }
            targets[key]["proof_indices"] = []
        targets[key]["proof_indices"].append(index)
    return {
        "schema_version": "neotoma-dataset-facet-native-links.v1",
        "source_capture_manifest_sha256": expected_manifest_sha256,
        "links": links,
        "targets": [targets[key] for key in sorted(targets)],
        "higher_taxon_leads": higher,
        "unavailable": unavailable,
        "scientific_admission": "not_asserted",
        "HTTP_requests": 0,
        "recursive_expansion": False,
    }
