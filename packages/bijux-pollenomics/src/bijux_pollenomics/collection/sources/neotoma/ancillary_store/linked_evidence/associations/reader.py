"""Authenticate a later relationship before opening its retained native detail."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import re
from typing import Any

from ....capture.facets.profiles import qualify_neotoma_facet_body
from ....capture.facets.protocol import request_for as facet_request
from ....capture.linked_resources.models import NeotomaLinkedEvidence
from ....capture.linked_resources.profiles import parse_neotoma_linked_source
from ....capture.linked_resources.protocol import request_for
from ....capture.resources.models import DEVELOPMENT_ROLES
from ....client import positive_native_id
from ....resource_catalogue.source_projection import _same
from ...selection.access import _body, _facet_resource, _observation, _result, _source
from ...selection.metadata import SelectedMetadata
from ...selection.scope import CurrentScope
from ..selection import _POINTERS
from .models import NeotomaLinkedAssociationInputs
from .projection import prepare, project_target
from .publication import read_manifest, read_part


def _selected(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    target_key: str,
    evidence: NeotomaLinkedEvidence,
    inputs: NeotomaLinkedAssociationInputs,
) -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], SelectedMetadata, CurrentScope
]:
    manifest = read_manifest(directory, expected_manifest_sha256)
    if not _same(manifest.get("anchors"), inputs.anchors(evidence.manifest_sha256)):
        raise ValueError("Association source anchors differ")
    if (
        not isinstance(target_key, str)
        or re.fullmatch(r"(?:contact|publication|taxon)-[1-9][0-9]*", target_key)
        is None
    ):
        raise ValueError("Association selection requires an exact native target")
    matches = [
        part
        for part in manifest["parts"]
        if part["first_key"] <= target_key <= part["last_key"]
    ]
    if len(matches) != 1:
        raise ValueError("Association target is absent or ambiguous")
    rows = [
        row
        for row in read_part(directory, matches[0])
        if row["target_key"] == target_key
    ]
    if len(rows) != 1:
        raise ValueError("Association target is absent or ambiguous")
    row = rows[0]
    metadata, scope, header, current = prepare(evidence, inputs)
    observation = _observation(metadata, row["observation_id"], "linked")
    expected, selected = project_target(
        observation, evidence, metadata, scope, header, current
    )
    if not _same(expected, row):
        raise ValueError("Selected association source projection differs")
    return row, selected, observation, metadata, scope


def read_neotoma_linked_association(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    target_key: str,
    evidence: NeotomaLinkedEvidence,
    inputs: NeotomaLinkedAssociationInputs,
) -> dict[str, Any]:
    """Read selected association metadata; no native witness or entity is decoded."""
    row, _, _, _, _ = _selected(
        directory,
        expected_manifest_sha256=expected_manifest_sha256,
        target_key=target_key,
        evidence=evidence,
        inputs=inputs,
    )
    return row


def read_neotoma_linked_association_source(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    target_key: str,
    occurrence_locator: dict[str, Any],
    evidence: NeotomaLinkedEvidence,
    inputs: NeotomaLinkedAssociationInputs,
) -> dict[str, Any]:
    """Verify one literal source pointer and return the original qualified entity buffer."""
    row, selected, observation, metadata, scope = _selected(
        directory,
        expected_manifest_sha256=expected_manifest_sha256,
        target_key=target_key,
        evidence=evidence,
        inputs=inputs,
    )
    if row["current_use_role"] not in DEVELOPMENT_ROLES:
        raise ValueError("Association current protected role forbids entity access")
    if row["kind"] == "contact":
        scope.contact(row["native_id"])
    retained = row["retained_entity"]
    if (
        retained is None
        or retained["http_status"] != 200
        or retained["body_complete"] is not True
    ):
        raise ValueError("Retained association entity is not complete and successful")
    locators = selected["proof_locators"]
    offsets = [
        offset
        for offset, locator in enumerate(locators)
        if _same(locator, occurrence_locator)
    ]
    if len(offsets) != 1:
        raise ValueError("Selected association occurrence locator differs")
    proof = selected["source_proofs"][offsets[0]]
    all_proofs = selected["source_proofs"]
    capture, entry = _source(metadata, observation, "linked")
    old = entry["identity"]["source_proofs"]
    scope.guard([value["root_identity"] for value in [*old, *all_proofs]])
    predecessor = metadata.capture(proof["source_capture_manifest_sha256"], "facet")
    sources = [
        source
        for source in predecessor["document"]["facets"]
        if source["facet_key"] == proof["source_facet_key"]
    ]
    if len(sources) != 1:
        raise ValueError("Selected association source witness is absent or ambiguous")
    source_entry = sources[0]
    resource = _facet_resource(predecessor, source_entry)
    scope.original(metadata, predecessor, source_entry)
    if (
        not _same(proof["root_identity"], source_entry["root_identity"])
        or proof["source_receipt_sha256"]
        != source_entry["attempts"][-1]["receipt_sha256"]
        or proof["content_version"] != source_entry["content_version"]
        or proof["api_version"] != source_entry["api_version"]
    ):
        raise ValueError("Selected association witness source identity differs")
    witness, _ = _body(
        metadata,
        predecessor,
        source_entry,
        facet_request(resource, source_entry["facet"], len(source_entry["attempts"])),
    )
    parsed = qualify_neotoma_facet_body(
        resource,
        source_entry["facet"],
        witness,
        expected_body_sha256=proof["source_body_sha256"],
    )
    pattern = _POINTERS.get(proof["relation"])
    pointer = proof["json_pointer"]
    if (
        parsed["qualification_status"] != "qualified_source_schema"
        or pattern is None
        or re.fullmatch(pattern, pointer) is None
    ):
        raise ValueError(
            "Selected association native witness or pointer is unqualified"
        )
    value = parsed["source_payload"]
    try:
        for token in pointer.split("/")[1:]:
            value = value[int(token)] if isinstance(value, list) else value[token]
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise ValueError("Selected association native pointer is absent") from error
    if positive_native_id(value) != row["native_id"]:
        raise ValueError("Selected association native field target differs")
    target = entry["identity"]
    body, receipt = _body(
        metadata,
        capture,
        entry,
        request_for(target, len(entry["attempts"])),
        observation,
    )
    if entry["terminal_status"] != "received_complete_unqualified_linked_resource":
        raise ValueError("Retained association entity is not complete and successful")
    native = parse_neotoma_linked_source(
        target, body, expected_body_sha256=sha256(body).hexdigest()
    )
    return {
        **_result(observation, body, receipt, linked=True),
        "source_payload": native.payload,
        "source_records": native.records,
        "association": row,
        "evidence_locator": occurrence_locator,
        "association_scope": "later_source_occurrence_current_use",
        "native_entity_owner_verified": True,
    }
