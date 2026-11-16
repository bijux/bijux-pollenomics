"""Authenticate selected source correspondence and budgeted native entity buffers."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from typing import Any

from ...capture.facets.assessment import assess_http as facet_assessment
from ...capture.facets.protocol import facet_identity
from ...capture.linked_resources.assessment import assess_http as linked_assessment
from ...capture.receipts import _object, _utc
from ...capture.resources.models import DEVELOPMENT_ROLES
from ...resource_catalogue.source_projection import _same
from ..capsule.models import compact_index, verify_receipt_metadata
from .metadata import SelectedMetadata, observation_identity, selected_metadata
from .scope import CurrentScope, current_scope


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
    *,
    _before_body_read: Callable[[], None] | None = None,
) -> tuple[bytes, dict[str, Any]]:
    receipt, bound = (
        response
        if response is not None
        else _response(metadata, capture, entry, request, observation)
    )
    reference = entry["attempts"][-1]
    if _before_body_read is not None:
        _before_body_read()
    body = metadata.source_member(capture, reference["body_file"], bound=bound + 1)
    if _before_body_read is not None:
        _before_body_read()
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
