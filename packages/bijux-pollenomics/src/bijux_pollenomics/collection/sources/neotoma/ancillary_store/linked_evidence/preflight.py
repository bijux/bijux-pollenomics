"""Selected global entities require native source pointers and every current duty."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import json
from pathlib import Path
import re
from typing import Any

from ...capture.facets.models import SCOPED_FACET_SCHEMA
from ...capture.facets.protocol import request_for as facet_request
from ...capture.linked_resources.models import SCOPED_LINKED_SCHEMA
from ...capture.linked_resources.protocol import _RANK
from ...capture.linked_resources.protocol import request_for as linked_request
from ...capture.resources.models import DEFAULT_RESOURCE_LIMITS, NeotomaResourceLimits
from ...client import positive_native_id
from ...resource_catalogue.source_projection import _same
from ..capsule.models import verify_linked_metadata_sources
from ..federation.models import scoped_occurrence
from ..selection.access import (
    _facet_resource,
    _observation,
    _prepare,
    _response,
    _role_row,
    _source,
)
from ..selection.metadata import SelectedMetadata
from ..selection.scope import CurrentScope
from .sources import (
    _prepared_scoped_target,
    read_scoped_target,
    resolve_linked_evidence,
)


@dataclass(frozen=True)
class LinkedAccess:
    """Both selected ledgers are closed; native pointer and bodies remain unverified."""

    metadata: SelectedMetadata
    scope: CurrentScope
    row: dict[str, Any]
    capture: dict[str, Any]
    entry: dict[str, Any]
    native_id: int
    scoped: bool
    proof: dict[str, Any]
    locator: dict[str, Any] | None
    request: Any
    response: tuple[dict[str, Any], int]
    predecessor: dict[str, Any]
    source_entry: dict[str, Any]
    source_request: Any
    source_response: tuple[dict[str, Any], int]
    parents: dict[int, dict[str, Any]]
    entity_bodies_verified: bool = field(default=False, init=False)
    native_field_value_verified: bool = field(default=False, init=False)


def prepare_linked_access(
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
) -> LinkedAccess:
    """Close original and current duties without reading either native buffer."""
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
    native = positive_native_id(native_id)
    metadata, scope = _prepare(directory, kwargs)
    return _prepared_linked_access(
        metadata,
        scope,
        observation_id=observation_id,
        occurrence_id=occurrence_id,
        kind=kind,
        native_id=native,
    )


def _prepared_linked_access(
    metadata: SelectedMetadata,
    scope: CurrentScope,
    *,
    observation_id: str,
    occurrence_id: str,
    kind: str,
    native_id: int,
    parts: Any = None,
) -> LinkedAccess:
    native = positive_native_id(native_id)
    row = _observation(metadata, observation_id, "linked")
    capture, entry = _source(metadata, row, "linked")
    target = entry["identity"]
    scoped = capture["document"]["schema_version"] == SCOPED_LINKED_SCHEMA
    if (
        not isinstance(kind, str)
        or kind not in {"contact", "publication", "taxon"}
        or target["kind"] != kind
        or target["native_id"] != native
        or not isinstance(occurrence_id, str)
        or not re.fullmatch(
            re.escape(observation_id)
            + (
                r":evidence:[0-9a-f]{64}:[0-9a-f]{64}:(0|[1-9][0-9]*)"
                if scoped
                else r":proof:(0|[1-9][0-9]*)"
            ),
            occurrence_id,
        )
    ):
        raise ValueError(
            "Linked selection requires an exact native target and occurrence"
        )
    locator = None
    if scoped:
        evidence = resolve_linked_evidence(
            capture["control"], metadata.evidence_sources
        )
        current = scope.linked_metadata()

        def load_target() -> dict[str, Any]:
            if parts is None:
                return read_scoped_target(evidence, target, current, attempted=True)
            return _prepared_scoped_target(
                evidence,
                target,
                current,
                attempted=True,
                reader=lambda path, digest, bound: parts.read(
                    path, digest, bound, source=evidence.manifest_sha256
                ),
            )

        selected = (
            load_target()
            if parts is None
            else parts.memo(
                evidence.manifest_sha256
                + ":"
                + json.dumps(target, sort_keys=True, allow_nan=False)
                + ":"
                + metadata.context_pin
                + ":"
                + metadata.native_pin,
                load_target,
            )
        )
        proofs = selected["source_proofs"]
        names = [
            observation_id
            + ":evidence:"
            + value["evidence_manifest_sha256"]
            + ":"
            + value["part_sha256"]
            + ":"
            + str(value["row_offset"])
            for value in selected["proof_locators"]
        ]
        if occurrence_id not in names:
            raise ValueError("Selected linked evidence occurrence is absent")
        offset = names.index(occurrence_id)
        locator = selected["proof_locators"][offset]
    else:
        proofs = target["source_proofs"]
        offset = int(occurrence_id.rsplit(":", 1)[1])
        if offset >= len(proofs):
            raise ValueError("Selected linked occurrence is absent")
        if kind == "contact":
            scope.contact(native)
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
    controls[digest] = {
        **capture["control"],
        "targets": [{**target, "source_proofs": list(proofs)}],
    }
    verify_linked_metadata_sources(
        documents, controls, descriptors, {digest: capture["directory"]}
    )
    occurrence = metadata.row("linked_occurrences", digest, occurrence_id)
    proof = proofs[offset]
    if scoped:
        if locator is None:
            raise ValueError("Selected scoped occurrence locator is missing")
        predecessor = sources[
            proof["source_facet_key"], proof["source_capture_manifest_sha256"]
        ][0]
        attestation = (
            "authenticated_source_inputs"
            if predecessor["document"]["schema_version"] == SCOPED_FACET_SCHEMA
            else "not_recorded_legacy_capture"
        )
        expected = scoped_occurrence(
            proof,
            locator,
            observation_id,
            {value["dataset_id"]: value for value in scope.roster["resources"]},
            {key: value["effective_scope_role"] for key, value in parents.items()},
            attestation,
        )
        if not _same(occurrence, expected):
            raise ValueError(
                "Selected scoped occurrence metadata or native locator differs"
            )
    else:
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
    source_request = facet_request(
        _facet_resource(predecessor, source_entry),
        source_entry["facet"],
        len(source_entry["attempts"]),
    )
    source_response = _response(metadata, predecessor, source_entry, source_request)
    return LinkedAccess(
        metadata,
        scope,
        row,
        capture,
        entry,
        native,
        scoped,
        proof,
        locator,
        request,
        response,
        predecessor,
        source_entry,
        source_request,
        source_response,
        parents,
    )
