"""Genuine pinned contexts for source-only environment/lake capture contracts."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import NeotomaMetadataResponse


def pin(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def context_resource_inputs(
    unit_products: Callable[..., dict[str, Any]],
) -> Callable[..., dict[str, Any]]:
    def prepare(**kwargs: Any) -> dict[str, Any]:
        inputs = unit_products(**kwargs)
        return {
            "context_directory": inputs["context"],
            "native_archive_directory": inputs["native"],
            "context_manifest_sha256": inputs["reader"]["expected_context_sha256"],
            "native_archive_manifest_sha256": inputs["reader"][
                "expected_native_archive_sha256"
            ],
        }

    return prepare


def source_response(url: str, **_: Any) -> NeotomaMetadataResponse:
    if "/apps/depenvt?" in url:
        body = {
            "status": "success",
            "data": [
                {
                    "siteid": 12,
                    "collectionunitid": 100,
                    "datasetid": 201,
                    "depenvt": "Lake",
                }
            ],
        }
    else:
        body = {
            "status": "success",
            "data": [{"hydrolakeid": 7, "lakearea": 0.02, "watershedarea": -9999}],
            "message": "Literal source candidate",
        }
    return NeotomaMetadataResponse(url, 200, (), json.dumps(body).encode())


def capture_legacy_context_fixture(
    directory: Path,
    *,
    plan: Any,
    context_directory: Path,
    native_archive_directory: Path,
    fetch: Callable[..., Any],
    limits: Any = None,
) -> Any:
    """TEST-ONLY old wire builder from maintained primitives, never a live producer.

    The old siteid environment query is retained for replay controls. A fetcher
    is mandatory; this fixture has no default network transport or source-code
    snapshot execution and cannot enable legacy acquisition in production.
    """
    from collections import Counter
    from dataclasses import asdict
    from datetime import UTC, datetime
    import time

    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources.models import (
        CONTEXT_SCHEMA,
        DEFAULT_CONTEXT_LIMITS,
        MAX_BYTES,
        MAX_FILES,
        POLICY_SOURCES,
        RESOURCE_KINDS,
        SNAPSHOT_CONSISTENCY,
        SOURCE_SCOPE,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources.protocol import (
        assess_http,
        request_for,
        validate_plan,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources.replay import (
        replay_neotoma_context_resources,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources.scope import (
        prepare_scope,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.receipts import (
        _retain_http_response,
        _retain_transport_failure,
        _write_json,
    )
    from bijux_pollenomics.core.filesystem import OwnedTreeWriter

    limits = DEFAULT_CONTEXT_LIMITS if limits is None else limits
    validate_plan(plan, limits)
    assert all(kind in RESOURCE_KINDS for kind in plan.resource_kinds)
    started, clock = datetime.now(UTC).isoformat(), time.monotonic()
    scope = prepare_scope(
        plan,
        context_directory=context_directory,
        native_archive_directory=native_archive_directory,
    )
    entries = []
    count = total = 0
    with OwnedTreeWriter(directory, max_bytes=MAX_BYTES, max_files=MAX_FILES) as writer:
        scope_pin = _write_json(directory / "parent-scope.json", scope, writer=writer)
        plan_pin = _write_json(
            directory / "request-plan.json",
            {
                "schema_version": CONTEXT_SCHEMA,
                "plan": asdict(plan),
                "limits": asdict(limits),
                "parent_scope_sha256": scope_pin,
                "source_scope": SOURCE_SCOPE,
                "policy_sources": list(POLICY_SOURCES),
            },
            writer=writer,
        )
        for kind in plan.resource_kinds:
            for parent in scope["requested_sites"]:
                row = {
                    "site_id": parent["site_id"],
                    "resource_kind": kind,
                    "content_version": "current",
                    "api_version": "v2.0",
                    "scope_status": parent["scope_status"],
                    "exposure_role": parent["effective_scope_role"],
                    "attempts": [],
                    "scientific_admission": "not_asserted",
                }
                remaining = limits.wall_seconds - (time.monotonic() - clock)
                if parent["scope_status"] != "eligible_current_scope":
                    row["terminal_status"] = "not_attempted_parent_scope"
                elif (
                    count >= limits.max_requests
                    or total >= limits.max_total_bytes
                    or remaining <= 0
                ):
                    row["terminal_status"] = "not_attempted_budget"
                else:
                    request = request_for(kind, parent["site_id"])
                    count += 1
                    bound = min(
                        limits.max_response_bytes, limits.max_total_bytes - total
                    )
                    utc = datetime.now(UTC).isoformat()
                    try:
                        response = fetch(
                            request.url,
                            timeout=min(limits.timeout_seconds, remaining),
                            max_bytes=bound,
                        )
                    except Exception as error:
                        ref, record = _retain_transport_failure(
                            directory, request, utc, error, writer=writer
                        )
                        assessed = {
                            "terminal_status": "transport_failure",
                            "reason": record["error"],
                        }
                    else:
                        ref, record = _retain_http_response(
                            directory, request, response, utc, writer=writer
                        )
                        total += len(response.body)
                        assessed = assess_http(record, request, response.body, bound)
                    row["attempts"].append(ref)
                    row.update(assessed)
                entries.append(row)
        _write_json(
            directory / "capture-manifest.json",
            {
                "schema_version": CONTEXT_SCHEMA,
                "status": "closed",
                "capture_utc_start": started,
                "capture_utc_end": datetime.now(UTC).isoformat(),
                "plan_sha256": plan_pin,
                "resources": entries,
                "request_count": count,
                "response_bytes": total,
                "partitions": dict(Counter(row["terminal_status"] for row in entries)),
                "source_scope": SOURCE_SCOPE,
                "snapshot_consistency": SNAPSHOT_CONSISTENCY,
                "scientific_admission": "not_asserted",
            },
            writer=writer,
        )
    return replay_neotoma_context_resources(
        directory,
        expected_context_sha256=plan.context_manifest_sha256,
        expected_native_archive_sha256=plan.native_archive_manifest_sha256,
        context_directory=context_directory,
        native_archive_directory=native_archive_directory,
        limits=limits,
    )


def rebuild_context(
    inputs: dict[str, Any], directory: Path, mutate: Callable[..., None]
) -> dict[str, Any]:
    """Retain real native metadata while changing only the frozen roster scope."""
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context import (
        load_neotoma_ancillary_context,
        write_neotoma_ancillary_context,
    )
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import (
        build_neotoma_resource_catalogue,
        write_neotoma_resource_catalogue,
    )
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive import (
        write_neotoma_source_archive,
    )

    directory.mkdir()
    context = load_neotoma_ancillary_context(
        inputs["context_directory"],
        expected_manifest_sha256=inputs["context_manifest_sha256"],
        native_archive_directory=inputs["native_archive_directory"],
    )
    scope = next(iter(context.current_scope_inputs.values()))
    roster = json.loads(scope.roster_path.read_bytes())
    mutate(roster)
    roster_path = directory / "roster.json"
    roster_path.write_text(json.dumps(roster))
    catalogue = build_neotoma_resource_catalogue(
        roster_path=roster_path,
        expected_roster_sha256=pin(roster_path),
        metadata_captures=scope.metadata_captures,
        resource_captures={},
        country_boundaries={
            "Sweden": {
                "features": [
                    {
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [[0, 0], [40, 0], [40, 80], [0, 80], [0, 0]]
                            ],
                        }
                    }
                ]
            }
        },
    )
    catalogue_root = directory / "catalogue"
    write_neotoma_resource_catalogue(
        catalogue_root,
        catalogue=catalogue,
        roster_path=roster_path,
        capture_sources=scope.metadata_captures,
    )
    native = directory / "native"
    write_neotoma_source_archive(
        native,
        catalogue_directory=catalogue_root,
        expected_catalogue_manifest_sha256=pin(catalogue_root / "manifest.json"),
        capture_sources=scope.metadata_captures,
    )
    authority = (
        inputs["context_directory"] / context.manifest["exposure_authority"]["path"]
    )
    output = directory / "context"
    write_neotoma_ancillary_context(
        output,
        native_archive_directory=native,
        expected_native_archive_sha256=pin(native / "manifest.json"),
        legacy_rosters=context.legacy_rosters,
        exposure_authority=authority,
        expected_exposure_authority_sha256=pin(authority),
    )
    return {
        "context_directory": output,
        "native_archive_directory": native,
        "context_manifest_sha256": pin(output / "manifest.json"),
        "native_archive_manifest_sha256": pin(native / "manifest.json"),
    }


def captured(
    context_resource_inputs: Callable[..., dict[str, Any]],
    tmp_path: Path,
    **kwargs: Any,
) -> tuple[dict[str, Any], Any]:
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
        NeotomaContextResourcePlan,
        capture_neotoma_context_resources,
    )

    inputs = context_resource_inputs()
    plan = NeotomaContextResourcePlan(
        (12,),
        inputs.pop("context_manifest_sha256"),
        inputs.pop("native_archive_manifest_sha256"),
        ("dataset_depositional_environment", "lake_candidates"),
    )
    output = tmp_path / "capture"
    result = capture_neotoma_context_resources(
        output,
        plan=plan,
        fetch=kwargs.pop("fetch", source_response),
        **inputs,
        **kwargs,
    )
    return {
        "directory": output,
        "expected_manifest_sha256": result.manifest_sha256,
        "expected_context_sha256": plan.context_manifest_sha256,
        "expected_native_archive_sha256": plan.native_archive_manifest_sha256,
        **inputs,
    }, result


def rehash_source(arguments: dict[str, Any], mutate: Callable[..., None]) -> None:
    root = arguments["directory"]
    manifest = json.loads((root / "capture-manifest.json").read_bytes())
    control = json.loads((root / "request-plan.json").read_bytes())
    mutate(manifest, control, root)
    (root / "request-plan.json").write_text(json.dumps(control))
    manifest["plan_sha256"] = pin(root / "request-plan.json")
    (root / "capture-manifest.json").write_text(json.dumps(manifest))
    arguments["expected_manifest_sha256"] = pin(root / "capture-manifest.json")


def forbid_context_bodies(monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    opened = []
    original = Path.open

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.name.startswith("site-") and path.suffix == ".body":
            opened.append(path)
            raise AssertionError("Context source body opened before refusal")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    return opened
