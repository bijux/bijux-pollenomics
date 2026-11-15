"""Guard exact ancillary occurrences before reading and returning authenticated entities."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
import re
from typing import Any

from ...capture.facets.assessment import assess_http as facet_assessment
from ...capture.facets.profiles import qualify_neotoma_facet_body
from ...capture.facets.protocol import facet_identity
from ...capture.facets.protocol import request_for as facet_request
from ...capture.linked_resources.assessment import assess_http as linked_assessment
from ...capture.linked_resources.profiles import parse_neotoma_linked_source
from ...capture.linked_resources.protocol import _RANK
from ...capture.linked_resources.protocol import request_for as linked_request
from ...capture.receipts import _object, _utc
from ...capture.resources.models import (
    DEFAULT_RESOURCE_LIMITS,
    DEVELOPMENT_ROLES,
    NeotomaResourceLimits,
)
from ...client import positive_native_id
from ...resource_catalogue.source_projection import _same
from ..capsule.models import (
    compact_index,
    verify_linked_metadata_sources,
    verify_receipt_metadata,
)
from .metadata import SelectedMetadata, observation_identity, selected_metadata
from .scope import CurrentScope, current_scope

_POINTERS = {
    "chronology_preparer": r"/data/(0|[1-9][0-9]*)/chronology/preparedby/contactid",
    "dataset_contributor": r"/data/(0|[1-9][0-9]*)/contacts/contacts/(0|[1-9][0-9]*)/contactid",
    "dataset_publication": r"/data/(0|[1-9][0-9]*)/publication/publicationid",
    "dataset_reported_taxon": r"/data/(0|[1-9][0-9]*)/taxonid",
    "taxonomic_reference_publication": r"/data/(0|[1-9][0-9]*)/publicationid",
    "source_reported_higher_taxon": r"/data/(0|[1-9][0-9]*)/highertaxonid",
}


def _source(
    metadata: SelectedMetadata, observation: dict[str, Any], kind: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    population = "facets" if kind == "facet" else "resources"
    digest, offset = observation_identity(observation.get("observation_id"), population)
    capture = metadata.capture(digest, kind)
    entries = capture["document"][population]
    if offset >= len(entries):
        raise ValueError("Selected source observation is absent")
    entry = entries[offset]
    base = compact_index(
        {digest: capture["descriptor"]},
        {digest: capture["document"]},
        {digest: capture["control"]},
    )["observations"][offset]
    if kind == "linked":
        base["identity"] = {
            key: value
            for key, value in base["identity"].items()
            if key != "source_proofs"
        }
    for key, value in base.items():
        if key != "attempts" and not _same(observation.get(key), value):
            raise ValueError("Selected observation source correspondence differs")
    if observation.get("capsule_manifest_sha256") != capture["capsule_pin"]:
        raise ValueError("Selected observation capsule binding differs")
    if not isinstance(observation.get("attempts"), list) or len(
        observation["attempts"]
    ) != len(base["attempts"]):
        raise ValueError("Selected observation attempt population differs")
    for indexed, source in zip(observation["attempts"], base["attempts"], strict=True):
        if not _same({key: indexed.get(key) for key in source}, source):
            raise ValueError("Selected observation attempt identity differs")
    return capture, entry


def _facet_resource(capture: dict[str, Any], entry: dict[str, Any]) -> Any:
    matches = [
        resource
        for resource in capture["plan"].resources
        if resource.dataset_id == entry["root_identity"]["dataset_id"]
    ]
    if (
        len(matches) != 1
        or entry["facet"] not in capture["plan"].facets
        or not _same(
            {key: entry.get(key) for key in facet_identity(matches[0], entry["facet"])},
            facet_identity(matches[0], entry["facet"]),
        )
    ):
        raise ValueError("Selected facet native source owner differs")
    return matches[0]


def _observation(
    metadata: SelectedMetadata, observation_id: str, kind: str
) -> dict[str, Any]:
    digest, _ = observation_identity(
        observation_id, "facets" if kind == "facet" else "resources"
    )
    row = metadata.row("observations", digest, observation_id)
    if (
        row.get("kind") != kind
        or row.get("content_version") != "current"
        or row.get("api_version") != "v2.0"
        or row.get("scientific_admission") != "not_asserted"
    ):
        raise ValueError("Selected source kind, version or scientific claim differs")
    return row


def _role_row(row: dict[str, Any], role: str) -> None:
    if (
        role not in DEVELOPMENT_ROLES
        or row.get("current_use_role") != role
        or row.get("current_owner_join") != "exact_current_owner"
        or row.get("current_use_scope_verification")
        != "authenticated_current_context_only"
        or row.get("access_restrictions") != []
        or row.get("entity_access_status") != "requires_selected_source_guard"
    ):
        raise ValueError("Selected current role or owner scope differs")


def _response(
    metadata: SelectedMetadata,
    capture: dict[str, Any],
    entry: dict[str, Any],
    request: Any,
    observation: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], int]:
    attempts = entry["attempts"]
    if not attempts or "body_file" not in attempts[-1]:
        raise ValueError("Selected source entity is unavailable without an HTTP body")
    reference = attempts[-1]
    if (
        reference.get("request_name") != request.name
        or reference.get("receipt_file") != f"{request.name}.receipt.json"
        or reference.get("body_file") != f"{request.name}.body"
    ):
        raise ValueError("Selected source attempt reference differs")
    receipt = _object(
        metadata.source_member(capture, reference["receipt_file"], bound=1024 * 1024)
    )
    if (
        capture["descriptor"]["files"][reference["receipt_file"]]["sha256"]
        != reference["receipt_sha256"]
        or receipt.get("body_file") != reference["body_file"]
    ):
        raise ValueError("Selected source receipt identity differs")
    verify_receipt_metadata(
        receipt,
        request,
        capture["document"],
        _utc(capture["document"]["capture_utc_start"]),
    )
    member = capture["descriptor"]["files"][reference["body_file"]]
    if (
        receipt.get("retained_body_sha256") != member["sha256"]
        or type(receipt.get("retained_body_bytes")) is not int
        or receipt["retained_body_bytes"] != member["bytes"]
    ):
        raise ValueError("Selected receipt and body declarations differ")
    if observation is not None:
        enriched = observation["attempts"][-1]
        for key in (
            "http_status",
            "body_complete",
            "terminal_status",
            "utc_start",
            "utc_end",
            "tls_mode",
            "requested_url",
        ):
            if not _same(enriched.get(key), receipt.get(key)):
                raise ValueError("Selected observation receipt metadata differs")
    bound = metadata.response_bound(capture, entry, receipt)
    return receipt, bound


def _body(
    metadata: SelectedMetadata,
    capture: dict[str, Any],
    entry: dict[str, Any],
    request: Any,
    observation: dict[str, Any] | None = None,
    response: tuple[dict[str, Any], int] | None = None,
) -> tuple[bytes, dict[str, Any]]:
    receipt, bound = (
        response
        if response is not None
        else _response(metadata, capture, entry, request, observation)
    )
    reference = entry["attempts"][-1]
    body = metadata.source_member(capture, reference["body_file"], bound=bound + 1)
    assessor = (
        facet_assessment if "facets" in capture["document"] else linked_assessment
    )
    assessed = assessor(receipt, request, body, bound)
    if not _same({key: entry.get(key) for key in assessed}, assessed):
        raise ValueError("Selected source body assessment differs")
    return body, receipt


def _result(
    row: dict[str, Any], body: bytes, receipt: dict[str, Any], *, linked: bool
) -> dict[str, Any]:
    return {
        "observation_id": row["observation_id"],
        "body": body,
        "body_sha256": sha256(body).hexdigest(),
        "receipt_sha256": row["attempts"][-1]["receipt_sha256"],
        "source_capture_manifest_sha256": row["source_capture_manifest_sha256"],
        "capsule_manifest_sha256": row["capsule_manifest_sha256"],
        "source_identity": row["root_identity"]
        if row["kind"] == "facet"
        else row["identity"],
        "terminal_status": row["terminal_status"],
        "http_status": receipt["http_status"],
        "body_complete": receipt["body_complete"],
        "capture_parent_scope_verification": row["capture_parent_scope_verification"],
        "integrity_scope": "selected_federation_metadata_current_root_obligations_and_source_chain",
        "source_assessment_replayed_for_selected_entity": True,
        "selected_occurrence_native_field_verified": linked,
        "all_recorded_proof_root_metadata_verified": linked,
        "unselected_occurrence_native_fields_verified": False,
        "unselected_entity_bodies_verified": False,
        "unselected_role_obligations_verified": False,
        "unselected_source_receipts_verified": False,
        "capture_history_replayed": False,
        "original_preget_scope_reconstructed": False,
        "related_resource_graph_complete": False,
        "scientific_admission": "not_asserted",
    }


def _prepare(
    directory: Path, kwargs: dict[str, Any]
) -> tuple[SelectedMetadata, CurrentScope]:
    options = dict(kwargs)
    context = options.pop("context_directory")
    native = options.pop("native_archive_directory")
    metadata = selected_metadata(directory, **options)
    return metadata, current_scope(metadata, context, native)


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
