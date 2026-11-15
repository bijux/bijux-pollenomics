"""Guard exact ancillary occurrences before reading and returning authenticated entities."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import re
from typing import Any

from ...capture.facets.profiles import qualify_neotoma_facet_body
from ...capture.facets.protocol import request_for as facet_request
from ...capture.linked_resources.profiles import parse_neotoma_linked_source
from ...capture.linked_resources.protocol import _RANK
from ...capture.linked_resources.protocol import request_for as linked_request
from ...capture.resources.models import (
    DEFAULT_RESOURCE_LIMITS,
    NeotomaResourceLimits,
)
from ...client import positive_native_id
from ...resource_catalogue.source_projection import _same
from ..capsule.models import verify_linked_metadata_sources
from .access import (
    _body,
    _facet_resource,
    _observation,
    _prepare,
    _response,
    _result,
    _role_row,
    _source,
)

_POINTERS = {
    "chronology_preparer": r"/data/(0|[1-9][0-9]*)/chronology/preparedby/contactid",
    "dataset_contributor": r"/data/(0|[1-9][0-9]*)/contacts/contacts/(0|[1-9][0-9]*)/contactid",
    "dataset_publication": r"/data/(0|[1-9][0-9]*)/publication/publicationid",
    "dataset_reported_taxon": r"/data/(0|[1-9][0-9]*)/taxonid",
    "taxonomic_reference_publication": r"/data/(0|[1-9][0-9]*)/publicationid",
    "source_reported_higher_taxon": r"/data/(0|[1-9][0-9]*)/highertaxonid",
}


def _facet(
    directory: Path, *, observation_id: str, dataset_id: int, facet: str, **kwargs: Any
) -> tuple[dict[str, Any], Any]:
    """Guard once and retain the native resource alongside the authenticated bytes."""
    dataset = positive_native_id(dataset_id)
    metadata, scope = _prepare(directory, kwargs)
    row = _observation(metadata, observation_id, "facet")
    if (
        row.get("facet") != facet
        or row.get("root_identity", {}).get("dataset_id") != dataset
    ):
        raise ValueError("Selected facet identity differs")
    capture, entry = _source(metadata, row, "facet")
    resource = _facet_resource(capture, entry)
    parents = scope.guard([entry["root_identity"]])
    role = parents[dataset]["effective_scope_role"]
    _role_row(row, role)
    metadata.slot(row, parents[dataset])
    scope.original(metadata, capture, entry)
    body, receipt = _body(
        metadata,
        capture,
        entry,
        facet_request(resource, facet, len(entry["attempts"])),
        row,
    )
    return _result(row, body, receipt, linked=False), resource


def read_neotoma_ancillary_facet_entity(
    directory: Path,
    *,
    observation_id: str,
    dataset_id: int,
    facet: str,
    expected_manifest_sha256: str,
    expected_context_sha256: str,
    expected_native_archive_sha256: str,
    context_directory: Path,
    native_archive_directory: Path,
    capsule_sources: Mapping[str, Path],
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
) -> dict[str, Any]:
    """Return a forensic entity; failed HTTP/source status remains explicit."""
    kwargs: dict[str, Any] = {
        "expected_manifest_sha256": expected_manifest_sha256,
        "expected_context_sha256": expected_context_sha256,
        "expected_native_archive_sha256": expected_native_archive_sha256,
        "context_directory": context_directory,
        "native_archive_directory": native_archive_directory,
        "capsule_sources": capsule_sources,
        "limits": limits,
    }
    return _facet(
        directory,
        observation_id=observation_id,
        dataset_id=dataset_id,
        facet=facet,
        **kwargs,
    )[0]


def read_neotoma_ancillary_facet(
    directory: Path,
    *,
    observation_id: str,
    dataset_id: int,
    facet: str,
    expected_manifest_sha256: str,
    expected_context_sha256: str,
    expected_native_archive_sha256: str,
    context_directory: Path,
    native_archive_directory: Path,
    capsule_sources: Mapping[str, Path],
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
) -> dict[str, Any]:
    """Add native schema qualification; no method or scientific admission is inferred."""
    kwargs: dict[str, Any] = {
        "expected_manifest_sha256": expected_manifest_sha256,
        "expected_context_sha256": expected_context_sha256,
        "expected_native_archive_sha256": expected_native_archive_sha256,
        "context_directory": context_directory,
        "native_archive_directory": native_archive_directory,
        "capsule_sources": capsule_sources,
        "limits": limits,
    }
    result, resource = _facet(
        directory,
        observation_id=observation_id,
        dataset_id=dataset_id,
        facet=facet,
        **kwargs,
    )
    if result["terminal_status"] != "received_complete_unqualified_facet":
        raise ValueError("Typed facet source is not a complete successful entity")
    qualified = qualify_neotoma_facet_body(
        resource,
        facet,
        result["body"],
        expected_body_sha256=result["body_sha256"],
    )
    if qualified["qualification_status"] != "qualified_source_schema":
        raise ValueError("Selected facet native source schema is unqualified")
    return {**result, "source_qualification": qualified}


def read_neotoma_ancillary_linked_entity(
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
) -> dict[str, Any]:
    """Verify all recorded root restrictions, then only the named native occurrence."""
    kwargs: dict[str, Any] = {
        "expected_manifest_sha256": expected_manifest_sha256,
        "expected_context_sha256": expected_context_sha256,
        "expected_native_archive_sha256": expected_native_archive_sha256,
        "context_directory": context_directory,
        "native_archive_directory": native_archive_directory,
        "capsule_sources": capsule_sources,
        "limits": limits,
    }
    native = positive_native_id(native_id)
    metadata, scope = _prepare(directory, kwargs)
    row = _observation(metadata, observation_id, "linked")
    capture, entry = _source(metadata, row, "linked")
    target = entry["identity"]
    if (
        kind not in {"contact", "publication", "taxon"}
        or target["kind"] != kind
        or target["native_id"] != native
        or not isinstance(occurrence_id, str)
        or not re.fullmatch(
            re.escape(observation_id) + r":proof:(0|[1-9][0-9]*)", occurrence_id
        )
    ):
        raise ValueError(
            "Linked selection requires an exact native target and occurrence"
        )
    proofs = target["source_proofs"]
    offset = int(occurrence_id.rsplit(":", 1)[1])
    if offset >= len(proofs):
        raise ValueError("Selected linked occurrence is absent")
    parents = scope.guard([proof["root_identity"] for proof in proofs])
    role = max(
        (parents[proof["root_dataset_id"]]["effective_scope_role"] for proof in proofs),
        key=lambda value: _RANK[value],
    )
    _role_row(row, role)
    documents, controls, descriptors, sources = {}, {}, {}, {}
    for proof in proofs:
        digest = proof["source_capture_manifest_sha256"]
        predecessor = metadata.capture(digest, "facet")
        candidates = [
            value
            for value in predecessor["document"]["facets"]
            if value["facet_key"] == proof["source_facet_key"]
        ]
        if len(candidates) != 1:
            raise ValueError(
                "Selected linked predecessor source is absent or ambiguous"
            )
        _facet_resource(predecessor, candidates[0])
        scope.original(metadata, predecessor, candidates[0])
        sources[proof["source_facet_key"], digest] = (predecessor, candidates[0])
        documents[digest], controls[digest], descriptors[digest] = (
            predecessor["document"],
            predecessor["control"],
            predecessor["descriptor"],
        )
    digest = row["source_capture_manifest_sha256"]
    documents[digest], descriptors[digest] = capture["document"], capture["descriptor"]
    controls[digest] = {**capture["control"], "targets": [target]}
    verify_linked_metadata_sources(
        documents, controls, descriptors, {digest: capture["directory"]}
    )
    occurrence = metadata.row("linked_occurrences", digest, occurrence_id)
    proof = proofs[offset]
    if (
        occurrence.get("observation_id") != observation_id
        or occurrence.get("source_proof_pointer")
        != f"{row['source_entry_pointer']}/identity/source_proofs/{offset}"
        or not _same(occurrence.get("source_proof"), proof)
        or occurrence.get("native_field_value_verified") is not False
        or occurrence.get("current_owner_join") != "exact_current_owner"
        or occurrence.get("current_use_role")
        != parents[proof["root_dataset_id"]]["effective_scope_role"]
    ):
        raise ValueError("Selected linked occurrence metadata differs")
    request = linked_request(target, len(entry["attempts"]))
    response = _response(metadata, capture, entry, request, row)
    predecessor, source_entry = sources[
        proof["source_facet_key"], proof["source_capture_manifest_sha256"]
    ]
    source_body, _ = _body(
        metadata,
        predecessor,
        source_entry,
        facet_request(
            _facet_resource(predecessor, source_entry),
            source_entry["facet"],
            len(source_entry["attempts"]),
        ),
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
    }


def read_neotoma_ancillary_linked(
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
    }
    result = read_neotoma_ancillary_linked_entity(
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
