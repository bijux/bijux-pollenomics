"""Complete metadata-only capture refusal gates before any native-body replay."""

from __future__ import annotations

from hashlib import sha256
from typing import TYPE_CHECKING, Any

from .....resource_catalogue.archive.files import _digest
from ....receipts import _object, _request_record, _utc, _validate_transport_failure
from ....resources.models import DEVELOPMENT_ROLES
from ...protocol import request_for
from .models import (
    MAX_CAPTURE_BYTES,
    MAX_ENTITY_BYTES,
    NeotomaTaxonAncestryChainLimits,
    capture_control,
    capture_members,
    capture_population,
    capture_target,
    strongest_roles,
    validate_capture_pins,
)
from .projection import project

if TYPE_CHECKING:
    from .authority import ChainOperation


def preflight_sources(
    operation: ChainOperation,
    pins: tuple[str, ...],
    parent: str | None,
    limits: NeotomaTaxonAncestryChainLimits,
) -> None:
    """Seal complete finite controls and epochs without native-body access."""
    validate_capture_pins(pins, limits.max_new_requests)
    for pin in pins:
        if pin not in operation.sources.ancestry_capture_sources:
            raise ValueError("Ancestry capture source is missing")
        if (pin, parent) not in operation.controls:
            root = operation.sources.ancestry_capture_sources[pin]
            operation.seal(root, bound=MAX_CAPTURE_BYTES)
            manifest, plan = capture_control(
                operation.read(root, "capture-manifest.json", 16 * 1024 * 1024),
                operation.read(root, "request-plan.json", 16 * 1024 * 1024),
                pin,
                parent,
                operation.sources.expected_baseline_projection_sha256,
            )
            capture_population(manifest, plan)
            operation.epoch(
                plan["current_context_manifest_sha256"],
                plan["current_native_archive_manifest_sha256"],
            )
            operation.controls[pin, parent] = manifest, plan


def receipt_metadata(operation: ChainOperation, pin: str, entry: dict[str, Any]) -> int:
    """Verify receipt identity and declared body membership, never body contents."""
    root = operation.sources.ancestry_capture_sources[pin]
    if not entry["attempts"]:
        if (
            entry["terminal_status"] != "not_attempted_protected_scope"
            or entry["recorded_role"] in DEVELOPMENT_ROLES
        ):
            raise ValueError("Ancestry closed capture has an untouched eligible slot")
        return 0
    attempt = entry["attempts"][0]
    raw = operation.read(root, attempt["receipt_file"], 1024 * 1024)
    if sha256(raw).hexdigest() != attempt["receipt_sha256"]:
        raise ValueError("Ancestry exact source receipt differs")
    receipt = _object(raw)
    request = request_for(entry, 1)
    if "body_file" not in attempt:
        _validate_transport_failure(receipt, request)
        if entry["terminal_status"] != "unavailable_transport":
            raise ValueError("Ancestry transport terminal status differs")
        return 0
    expected = _request_record(request, receipt.get("utc_start", ""))
    fields = {
        "utc_end",
        "final_url",
        "http_status",
        "response_headers",
        "body_file",
        "body_complete",
        "retained_body_bytes",
        "retained_body_sha256",
        "terminal_status",
    }
    if (
        set(receipt) != set(expected) | fields
        or any(receipt.get(key) != value for key, value in expected.items())
        or receipt["final_url"] != request.url
        or receipt["body_file"] != attempt["body_file"]
    ):
        raise ValueError("Ancestry receipt request/body control identity differs")
    size = operation.seal(root).files[attempt["body_file"]][4]
    if (
        type(receipt["body_complete"]) is not bool
        or type(receipt["retained_body_bytes"]) is not int
        or receipt["retained_body_bytes"] != size
        or size > MAX_ENTITY_BYTES + int(not receipt["body_complete"])
        or not _digest(receipt["retained_body_sha256"])
        or type(receipt["http_status"]) is not int
        or not 100 <= receipt["http_status"] <= 599
    ):
        raise ValueError("Ancestry receipt declared body size or status differs")
    if _utc(receipt["utc_start"]) > _utc(receipt["utc_end"]):
        raise ValueError("Ancestry receipt timestamps are reversed")
    headers = receipt["response_headers"]
    if not isinstance(headers, list) or any(
        not isinstance(pair, list)
        or len(pair) != 2
        or any(not isinstance(value, str) for value in pair)
        for pair in headers
    ):
        raise ValueError("Ancestry receipt header population differs")
    for name, value in headers:
        if name.lower() == "content-length" and receipt["body_complete"]:
            try:
                declared = int(value)
            except ValueError as error:
                raise ValueError(
                    "Ancestry receipt content length is invalid"
                ) from error
            if declared != size:
                raise ValueError("Ancestry receipt content length differs")
    terminal = (
        "complete_http_200"
        if receipt["http_status"] == 200 and receipt["body_complete"]
        else "refused_http_response"
    )
    if receipt["terminal_status"] != terminal:
        raise ValueError("Ancestry receipt terminal status differs")
    statuses = (
        {"unavailable_http"}
        if receipt["http_status"] != 200
        else {"refused_incomplete_body"}
        if not receipt["body_complete"]
        else {
            "received_complete_unqualified_linked_resource",
            "refused_native_json",
            "refused_http_receipt",
        }
    )
    if entry["terminal_status"] not in statuses:
        raise ValueError("Ancestry declared source HTTP status differs")
    return size


def check_capture(
    operation: ChainOperation,
    state: dict[str, Any],
    parent: str | None,
    pin: str,
    limits: NeotomaTaxonAncestryChainLimits,
    allowed: set[str],
) -> None:
    """Refuse any late target, bound, namespace or receipt defect before bodies."""
    root = operation.sources.ancestry_capture_sources[pin]
    tree = operation.seal(root, bound=MAX_CAPTURE_BYTES)
    manifest, plan = operation.controls[pin, parent]
    epoch = operation.epoch(
        plan["current_context_manifest_sha256"],
        plan["current_native_archive_manifest_sha256"],
    )
    recorded_graph = project(
        state, strongest_roles(operation.history, epoch["roles"]), limits
    )
    current_graph = project(
        state,
        strongest_roles(*(epoch["roles"] for epoch in operation.epochs.values())),
        limits,
    )
    frontier = {row["target_key"]: row for row in recorded_graph["frontier"]}
    entries, keys = capture_population(manifest, plan)
    expected = {"capture-manifest.json", "request-plan.json"}
    for key, entry in zip(keys, entries, strict=True):
        if key not in allowed:
            raise ValueError("Ancestry target was not in the anchored parent frontier")
        node = capture_target(key, entry, frontier)
        witness = state["edges"].get(entry["witness_edge_id"])
        if (
            not witness
            or witness["native_id"] != node["native_id"]
            or witness["target_kind"] != node["target_kind"]
            or witness["status"] not in {"literal_parent", "literal_citation"}
        ):
            raise ValueError("Ancestry immediate native child source witness differs")
        attempts = entry["attempts"]
        if not isinstance(attempts, list) or len(attempts) > 1:
            raise ValueError("Ancestry capture requires one finite attempt")
        if attempts:
            child = current_graph["nodes"][f"taxon-{witness['child_taxon_id']}"]
            if (
                node["status"] != "not_attempted_capture_not_authorized"
                or current_graph["nodes"][key]["current_use_role"]
                not in DEVELOPMENT_ROLES
                or child["current_use_role"] not in DEVELOPMENT_ROLES
            ):
                raise ValueError(
                    "Ancestry protected or bounded target/witness forbids body access"
                )
        expected.update(capture_members(entry))
    if set(tree.files) != expected:
        raise ValueError("Ancestry capture namespace closure differs")
    sizes = [receipt_metadata(operation, pin, entry) for entry in entries]
    if (
        type(manifest["request_count"]) is not int
        or type(manifest["response_bytes"]) is not int
        or manifest["request_count"]
        != sum(bool(entry["attempts"]) for entry in entries)
        or manifest["response_bytes"] != sum(sizes)
    ):
        raise ValueError("Ancestry declared request/body accounting differs")


def check_group(
    operation: ChainOperation,
    state: dict[str, Any],
    parent: str | None,
    pins: tuple[str, ...],
    limits: NeotomaTaxonAncestryChainLimits,
) -> None:
    """Check the complete group against one independently pinned parent graph."""
    preflight_sources(operation, pins, parent, limits)
    current = operation.epoch(
        operation.sources.expected_current_context_sha256,
        operation.sources.expected_current_native_archive_sha256,
    )
    allowed = {
        row["target_key"]
        for row in project(state, current["roles"], limits)["frontier"]
    }
    keys: set[str] = set()
    requests = state["new_request_count"]
    for pin in pins:
        if pin in operation.capture_pins:
            raise ValueError("Ancestry capture source is reused")
        check_capture(operation, state, parent, pin, limits, allowed)
        manifest, plan = operation.controls[pin, parent]
        if keys.intersection(plan["frontier_target_keys"]):
            raise ValueError("Ancestry parent-frontier target is duplicated")
        keys.update(plan["frontier_target_keys"])
        requests += manifest["request_count"]
    if requests > limits.max_new_requests:
        raise ValueError("Ancestry cumulative request bound exceeded")


def advance_metadata(
    operation: ChainOperation,
    state: dict[str, Any],
    document: dict[str, Any],
    parent: str | None,
    limits: NeotomaTaxonAncestryChainLimits,
) -> None:
    """Use pinned delta metadata only to refuse, pending complete native replay."""
    from .projection import seed_digest

    baseline = document["baseline"]
    if (
        baseline["seed_projection_manifest_sha256"] != state["baseline_sha256"]
        or baseline["evidence_manifest_sha256"] != state["evidence_sha256"]
        or baseline["seed_taxon_ids"] != state["seed_ids"]
        or baseline["seed_taxon_ids_sha256"] != seed_digest(state["seed_ids"])
    ):
        raise ValueError("Ancestry metadata changed its immutable baseline")
    pins = tuple(document["new_capture_manifest_sha256s"])
    check_group(operation, state, parent, pins, limits)
    for pin in pins:
        operation.capture_pins.add(pin)
        manifest, plan = operation.controls[pin, parent]
        state["new_request_count"] += manifest["request_count"]
        epoch = operation.epoch(
            plan["current_context_manifest_sha256"],
            plan["current_native_archive_manifest_sha256"],
        )
        operation.history = strongest_roles(operation.history, epoch["roles"])
    for edge in document["edges"]:
        if edge["edge_id"] in state["edges"]:
            raise ValueError("Ancestry metadata literal edge is duplicated")
        state["edges"][edge["edge_id"]] = edge
    state["results"].update(document["known_entity_results"])
