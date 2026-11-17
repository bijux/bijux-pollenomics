"""Capture only explicitly authorized native frontier entities into owned trees."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
import time
from typing import Any

from bijux_pollenomics.core.errors.cleanup import add_cleanup_note
from bijux_pollenomics.core.filesystem import OwnedTreeWriter
from bijux_pollenomics.core.owned_tree import build_staging_output_dir

from ......publication.ownership import publish_owned_source_tree
from ......resource_catalogue.archive.files import encoded_json
from .....receipts import (
    _retain_http_response,
    _retain_transport_failure,
    _safe_root,
    _write_json,
)
from .....transport import NeotomaHttpResponse, _fetch_response
from ....assessment import assess_http
from ....protocol import request_for
from ..authority import ChainOperation
from ..models import (
    CAPTURE_SCHEMA,
    DEFAULT_LIMITS,
    MAX_CAPTURE_BYTES,
    MAX_ENTITY_BYTES,
    NeotomaTaxonAncestryChainLimits,
    NeotomaTaxonAncestryChainSources,
)
from ..publication import _derive
from .models import (
    DEFAULT_CAPTURE_LIMITS,
    MAX_CONTROL_BYTES,
    NeotomaTaxonFrontierCapture,
    NeotomaTaxonFrontierCaptureLimits,
)
from .planning import (
    prepare_targets,
    require_separate_output,
    source_signature,
    validate_selection,
)


def _bounded_control(payload: Any) -> None:
    if len(encoded_json(payload)) > MAX_CONTROL_BYTES:
        raise ValueError("Frontier capture control exceeds finite metadata bound")


def _control(path: Path, payload: Any, writer: OwnedTreeWriter) -> str:
    _bounded_control(payload)
    return _write_json(path, payload, writer=writer)


def _manifest(
    plan_pin: str, entries: list[dict[str, Any]], count: int, total: int
) -> dict[str, Any]:
    return {
        "schema_version": CAPTURE_SCHEMA,
        "status": "closed",
        "plan_sha256": plan_pin,
        "resources": entries,
        "request_count": count,
        "response_bytes": total,
        "scientific_admission": "not_asserted",
    }


def _planned_controls(targets: list[dict[str, Any]], plan: dict[str, Any]) -> None:
    _bounded_control(plan)
    entries = []
    for target in targets:
        request = request_for(target, 1)
        entries.append(
            {
                **target,
                "terminal_status": "received_complete_unqualified_linked_resource",
                "attempts": [
                    {
                        "request_name": request.name,
                        "receipt_file": request.name + ".receipt.json",
                        "receipt_sha256": "0" * 64,
                        "body_file": request.name + ".body",
                    }
                ],
            }
        )
    _bounded_control(
        _manifest(
            "0" * 64, entries, len(targets), len(targets) * (MAX_ENTITY_BYTES + 1)
        )
    )


def _response(response: NeotomaHttpResponse, url: str) -> None:
    if (
        type(response) is not NeotomaHttpResponse
        or response.final_url != url
        or type(response.http_status) is not int
        or not 100 <= response.http_status <= 599
        or type(response.body) is not bytes
        or type(response.body_complete) is not bool
        or len(response.body) > MAX_ENTITY_BYTES + int(not response.body_complete)
        or not isinstance(response.headers, tuple)
        or len(response.headers) > 128
    ):
        raise ValueError("Frontier transport returned an invalid finite HTTP entity")
    size = 0
    for pair in response.headers:
        if (
            not isinstance(pair, tuple)
            or len(pair) != 2
            or any(not isinstance(value, str) for value in pair)
        ):
            raise ValueError("Frontier response headers are malformed")
        size += sum(len(value.encode()) for value in pair)
        if size > 65536:
            raise ValueError("Frontier response headers exceed finite receipt bound")


def capture_neotoma_taxon_ancestry_frontier(
    directory: Path,
    *,
    sources: NeotomaTaxonAncestryChainSources,
    parent_chain_sha256: str | None,
    target_keys: tuple[str, ...],
    limits: NeotomaTaxonAncestryChainLimits = DEFAULT_LIMITS,
    capture_limits: NeotomaTaxonFrontierCaptureLimits = DEFAULT_CAPTURE_LIMITS,
    fetch: Callable[..., NeotomaHttpResponse] = _fetch_response,
) -> NeotomaTaxonFrontierCapture:
    """Acquire one finite explicit frontier batch without recursive or retried GETs."""
    if (
        type(capture_limits) is not NeotomaTaxonFrontierCaptureLimits
        or type(limits) is not NeotomaTaxonAncestryChainLimits
    ):
        raise ValueError("Frontier capture limit type differs from the finite profile")
    validate_selection(target_keys, capture_limits)
    limits.validate()
    requested = Path(directory).absolute()
    if ".." in requested.parts or requested != requested.resolve(strict=False):
        raise ValueError("Frontier output must be a canonical literal path")
    final = _safe_root(requested)
    if final.exists():
        raise FileExistsError(f"Ancestry frontier output exists: {final}")
    started = time.monotonic()
    with ChainOperation(sources) as operation:
        identity = source_signature(sources)
        targets, plan = prepare_targets(
            operation, parent_chain_sha256, target_keys, limits, native_replay=False
        )
        require_separate_output(operation, final)
        _planned_controls(targets, plan)

        def check_sources() -> None:
            if time.monotonic() - started >= capture_limits.wall_seconds:
                raise TimeoutError("Frontier capture wall budget exhausted")
            if source_signature(sources) != identity:
                raise ValueError("Frontier source resolver bindings changed")
            operation._check_live()

        check_sources()
        verified_targets, verified_plan = prepare_targets(
            operation, parent_chain_sha256, target_keys, limits, native_replay=True
        )
        if verified_targets != targets or verified_plan != plan:
            raise ValueError(
                "Frontier metadata differs from authenticated native sources"
            )
        check_sources()
        staging = build_staging_output_dir(final)
        with OwnedTreeWriter(
            staging, max_bytes=MAX_CAPTURE_BYTES, max_files=len(target_keys) * 2 + 3
        ) as writer:
            count = total = 0
            entries = []
            try:
                plan_pin = _control(staging / "request-plan.json", plan, writer)
                for target in targets:
                    check_sources()
                    remaining = capture_limits.wall_seconds - (
                        time.monotonic() - started
                    )
                    if remaining <= 0:
                        raise TimeoutError("Frontier capture wall budget exhausted")
                    request = request_for(target, 1)
                    request_started = datetime.now(UTC).isoformat()
                    count += 1
                    try:
                        response = fetch(
                            request.url,
                            max_bytes=MAX_ENTITY_BYTES,
                            timeout=min(capture_limits.timeout_seconds, remaining),
                        )
                    except Exception as error:
                        check_sources()
                        if len(str(error)) > 65536:
                            raise ValueError(
                                "Frontier transport error exceeds receipt bound"
                            ) from error
                        reference, _ = _retain_transport_failure(
                            staging, request, request_started, error, writer=writer
                        )
                        terminal = "unavailable_transport"
                    else:
                        check_sources()
                        _response(response, request.url)
                        if (
                            total + len(response.body)
                            > capture_limits.max_total_response_bytes
                        ):
                            raise ValueError(
                                "Frontier capture aggregate response budget exceeded"
                            )
                        reference, receipt = _retain_http_response(
                            staging, request, response, request_started, writer=writer
                        )
                        total += len(response.body)
                        terminal = assess_http(
                            receipt, request, response.body, MAX_ENTITY_BYTES
                        )["terminal_status"]
                    entries.append(
                        {**target, "terminal_status": terminal, "attempts": [reference]}
                    )
                check_sources()
                manifest = _manifest(plan_pin, entries, count, total)
                pin = _control(staging / "capture-manifest.json", manifest, writer)

                def validate(path: Path) -> NeotomaTaxonFrontierCapture:
                    check_sources()
                    with operation._capture_child(pin, path) as child:
                        _derive(child, parent_chain_sha256, (pin,), limits)
                        child._check_live()
                    check_sources()
                    return NeotomaTaxonFrontierCapture(
                        path, pin, count, total, target_keys
                    )

                return publish_owned_source_tree(
                    writer, staging=staging, final=final, validate=validate
                )
            except BaseException as error:
                try:
                    writer.validate_attachment()
                    _control(
                        staging / "refusal.json",
                        {
                            "schema_version": CAPTURE_SCHEMA,
                            "status": "refused_execution",
                            "error": f"{type(error).__name__}: {error}",
                            "request_count": count,
                            "response_bytes": total,
                        },
                        writer,
                    )
                except Exception as receipt_error:

                    def receipt_note(failure: Exception = receipt_error) -> str:
                        return (
                            "Frontier refusal receipt failed: "
                            f"{type(failure).__name__}: {failure}"
                        )

                    add_cleanup_note(error, receipt_note)
                raise
