"""Selected global entities require native source pointers and every current duty."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import re
from typing import Any

from ...capture.facets.profiles import qualify_neotoma_facet_body
from ...capture.linked_resources.profiles import parse_neotoma_linked_source
from ...capture.resources.models import DEFAULT_RESOURCE_LIMITS, NeotomaResourceLimits
from ...client import positive_native_id
from ..selection.access import (
    _body,
    _facet_resource,
    _result,
)

_POINTERS = {
    "chronology_preparer": r"/data/(0|[1-9][0-9]*)/chronology/preparedby/contactid",
    "dataset_contributor": r"/data/(0|[1-9][0-9]*)/contacts/contacts/(0|[1-9][0-9]*)/contactid",
    "dataset_publication": r"/data/(0|[1-9][0-9]*)/publication/publicationid",
    "dataset_reported_taxon": r"/data/(0|[1-9][0-9]*)/taxonid",
    "taxonomic_reference_publication": r"/data/(0|[1-9][0-9]*)/publicationid",
    "source_reported_higher_taxon": r"/data/(0|[1-9][0-9]*)/highertaxonid",
}


def read_linked_entity(
    directory: Path,
    *,
    observation_id: str,
    occurrence_id: str,
    kind: str,
    native_id: int,
    expected_manifest_sha256: str,
    expected_context_sha256: str,
    expected_native_archive_sha256: str,
    context_directory: Path,
    native_archive_directory: Path,
    capsule_sources: Mapping[str, Path],
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
    evidence_sources: Mapping[str, Path] | None = None,
) -> dict[str, Any]:
    """Verify all recorded root restrictions, then only the named native occurrence."""
    from .preflight import prepare_linked_access

    kwargs: dict[str, Any] = {
        "expected_manifest_sha256": expected_manifest_sha256,
        "expected_context_sha256": expected_context_sha256,
        "expected_native_archive_sha256": expected_native_archive_sha256,
        "context_directory": context_directory,
        "native_archive_directory": native_archive_directory,
        "capsule_sources": capsule_sources,
        "limits": limits,
        "evidence_sources": evidence_sources,
    }
    prepared = prepare_linked_access(
        directory,
        observation_id=observation_id,
        occurrence_id=occurrence_id,
        kind=kind,
        native_id=native_id,
        **kwargs,
    )
    metadata, row = prepared.metadata, prepared.row
    capture, entry, native = prepared.capture, prepared.entry, prepared.native_id
    scoped = prepared.scoped
    proof, locator = prepared.proof, prepared.locator
    request, response = prepared.request, prepared.response
    predecessor, source_entry = prepared.predecessor, prepared.source_entry
    source_body, _ = _body(
        metadata,
        predecessor,
        source_entry,
        prepared.source_request,
        response=prepared.source_response,
    )
    qualified = qualify_neotoma_facet_body(
        _facet_resource(predecessor, source_entry),
        source_entry["facet"],
        source_body,
        expected_body_sha256=proof["source_body_sha256"],
    )
    pointer = proof["json_pointer"]
    pattern = _POINTERS.get(proof["relation"])
    if (
        qualified["qualification_status"] != "qualified_source_schema"
        or pattern is None
        or re.fullmatch(pattern, pointer) is None
    ):
        raise ValueError(
            "Selected linked native pointer or source schema is unqualified"
        )
    value: Any = qualified["source_payload"]
    try:
        for token in pointer.split("/")[1:]:
            value = value[int(token)] if isinstance(value, list) else value[token]
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise ValueError("Selected linked native pointer is absent") from error
    if positive_native_id(value) != native:
        raise ValueError("Selected linked native field target differs")
    body, receipt = _body(metadata, capture, entry, request, row, response)
    return {
        **_result(row, body, receipt, linked=True),
        "occurrence_id": occurrence_id,
        "source_proof": proof,
        **({"evidence_locator": locator} if scoped else {}),
    }


def read_linked(
    directory: Path,
    *,
    observation_id: str,
    occurrence_id: str,
    kind: str,
    native_id: int,
    expected_manifest_sha256: str,
    expected_context_sha256: str,
    expected_native_archive_sha256: str,
    context_directory: Path,
    native_archive_directory: Path,
    capsule_sources: Mapping[str, Path],
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
    evidence_sources: Mapping[str, Path] | None = None,
) -> dict[str, Any]:
    """Qualify the same returned global detail buffer independently of its associations."""
    kwargs: dict[str, Any] = {
        "expected_manifest_sha256": expected_manifest_sha256,
        "expected_context_sha256": expected_context_sha256,
        "expected_native_archive_sha256": expected_native_archive_sha256,
        "context_directory": context_directory,
        "native_archive_directory": native_archive_directory,
        "capsule_sources": capsule_sources,
        "limits": limits,
        "evidence_sources": evidence_sources,
    }
    result = read_linked_entity(
        directory,
        observation_id=observation_id,
        occurrence_id=occurrence_id,
        kind=kind,
        native_id=native_id,
        **kwargs,
    )
    if result["terminal_status"] != "received_complete_unqualified_linked_resource":
        raise ValueError("Typed linked source is not a complete successful entity")
    identity = result["source_identity"]
    parsed = parse_neotoma_linked_source(
        identity, result["body"], expected_body_sha256=result["body_sha256"]
    )
    return {
        **result,
        "source_payload": parsed.payload,
        "source_records": parsed.records,
    }
