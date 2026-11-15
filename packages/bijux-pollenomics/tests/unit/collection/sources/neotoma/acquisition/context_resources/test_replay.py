"""Literal source replay authenticates HTTP status and exact context scopes."""

from __future__ import annotations

from collections.abc import Callable
import json
import os
from pathlib import Path
from typing import Any

import pytest

from .native_products import (
    capture_legacy_context_fixture,
    captured,
    forbid_context_bodies,
    pin,
    rehash_source,
    source_response,
)


def test_replay_preserves_original_requests_and_unqualified_source_assessment(
    context_resource_inputs: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
        NeotomaContextResourcePlan,
        replay_neotoma_context_resources,
    )

    inputs = context_resource_inputs()
    plan = NeotomaContextResourcePlan(
        site_ids=(12,),
        context_manifest_sha256=inputs["context_manifest_sha256"],
        native_archive_manifest_sha256=inputs["native_archive_manifest_sha256"],
    )
    directory = tmp_path / "capture"
    options = {
        key: inputs[key] for key in ("context_directory", "native_archive_directory")
    }
    captured = capture_legacy_context_fixture(
        directory, plan=plan, fetch=source_response, **options
    )
    replayed = replay_neotoma_context_resources(
        directory,
        expected_manifest_sha256=captured.manifest_sha256,
        expected_context_sha256=plan.context_manifest_sha256,
        expected_native_archive_sha256=plan.native_archive_manifest_sha256,
        **options,
    )
    assert replayed == captured


def test_rehashed_fractional_native_receipt_owner_is_refused(
    context_resource_inputs: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
        replay_neotoma_context_resources,
    )

    arguments, _ = captured(context_resource_inputs, tmp_path)

    def mutate(manifest: dict[str, Any], control: dict[str, Any], root: Path) -> None:
        ref = manifest["resources"][0]["attempts"][0]
        path = root / ref["receipt_file"]
        receipt = json.loads(path.read_bytes())
        receipt["expected_site_id"] = 12.0
        path.write_text(json.dumps(receipt))
        ref["receipt_sha256"] = pin(path)

    rehash_source(arguments, mutate)
    with pytest.raises(ValueError, match="receipt"):
        replay_neotoma_context_resources(**arguments)


@pytest.mark.parametrize(
    "anchor",
    [
        "expected_context_sha256",
        "expected_native_archive_sha256",
        "expected_manifest_sha256",
    ],
)
def test_independent_anchor_refusal_precedes_any_context_body(
    context_resource_inputs: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    anchor: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
        replay_neotoma_context_resources,
    )

    arguments, _ = captured(context_resource_inputs, tmp_path)
    arguments[anchor] = "f" * 64
    opened = forbid_context_bodies(monkeypatch)
    with pytest.raises(ValueError):
        replay_neotoma_context_resources(**arguments)
    assert opened == []


@pytest.mark.parametrize(
    "change",
    [
        "request",
        "attempt",
        "body_pointer",
        "scope",
        "declared_site",
        "order",
        "native_anchor",
    ],
)
def test_rehashed_metadata_tampering_refuses_before_context_body(
    context_resource_inputs: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
        replay_neotoma_context_resources,
    )

    arguments, _ = captured(context_resource_inputs, tmp_path)

    def mutate(manifest: dict[str, Any], control: dict[str, Any], root: Path) -> None:
        row = manifest["resources"][0]
        if change == "request":
            control["limits"]["max_requests"] = 0
        elif change == "attempt":
            row["attempts"] *= 2
        elif change == "body_pointer":
            row["attempts"][0]["body_file"] = "../outside.body"
        elif change == "scope":
            row["scope_status"] = "protected_current_scope"
        elif change == "declared_site":
            row["site_id"] = 13
        elif change == "order":
            manifest["resources"].reverse()
        else:
            control["plan"]["native_archive_manifest_sha256"] = "f" * 64

    rehash_source(arguments, mutate)
    opened = forbid_context_bodies(monkeypatch)
    with pytest.raises(ValueError):
        replay_neotoma_context_resources(**arguments)
    assert opened == []


@pytest.mark.parametrize("kind", ["empty_directory", "fifo", "hardlink", "symlink"])
def test_closed_source_namespace_precedes_body_access(
    context_resource_inputs: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
        replay_neotoma_context_resources,
    )

    arguments, _ = captured(context_resource_inputs, tmp_path)
    path = arguments["directory"] / "foreign"
    if kind == "empty_directory":
        path.mkdir()
    elif kind == "fifo":
        os.mkfifo(path)
    elif kind == "hardlink":
        os.link(arguments["directory"] / "request-plan.json", path)
    else:
        path.symlink_to(arguments["directory"] / "request-plan.json")
    opened = forbid_context_bodies(monkeypatch)
    with pytest.raises(ValueError):
        replay_neotoma_context_resources(**arguments)
    assert opened == [] and path.exists()


@pytest.mark.parametrize("field", ["datasetid", "limit", "offset", "siteid"])
def test_dataset_query_receipt_cannot_narrow_or_replace_native_scope(
    context_resource_inputs: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
        NeotomaContextResourcePlan,
        capture_neotoma_context_resources,
        replay_neotoma_context_resources,
    )

    inputs = context_resource_inputs()
    plan = NeotomaContextResourcePlan(
        (12,),
        inputs.pop("context_manifest_sha256"),
        inputs.pop("native_archive_manifest_sha256"),
        ("dataset_depositional_environment",),
    )
    directory = tmp_path / "capture"
    result = capture_neotoma_context_resources(
        directory, plan=plan, fetch=source_response, **inputs
    )
    options = {
        "directory": directory,
        "expected_manifest_sha256": result.manifest_sha256,
        "expected_context_sha256": plan.context_manifest_sha256,
        "expected_native_archive_sha256": plan.native_archive_manifest_sha256,
        **inputs,
    }

    def change(manifest: dict[str, Any], control: dict[str, Any], root: Path) -> None:
        ref = manifest["resources"][0]["attempts"][0]
        path = root / ref["receipt_file"]
        receipt = json.loads(path.read_bytes())
        receipt["parameters"][field] = "201" if field == "datasetid" else "1"
        path.write_text(json.dumps(receipt))
        ref["receipt_sha256"] = pin(path)

    rehash_source(options, change)
    opened = forbid_context_bodies(monkeypatch)
    with pytest.raises(ValueError, match="receipt"):
        replay_neotoma_context_resources(**options)
    assert opened == []
