"""Explicit native-body access retains the same qualified authenticated bytes."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from hashlib import sha256
import importlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import NeotomaMetadataResponse
from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
    NeotomaResourcePlan,
    capture_neotoma_resources,
)
from bijux_pollenomics.collection.sources.neotoma.capture.resources.protocol import (
    plan_from_json,
)


def _formatted_source(
    inputs: dict[str, Any], tmp_path: Path, version: str
) -> tuple[bytes, Path]:
    source = next(iter(inputs["resource_captures"].values()))
    plan, _ = plan_from_json(json.loads((source / "request-plan.json").read_bytes()))
    document = json.loads(
        (source / f"dataset-201-{version}-attempt-1.body").read_bytes()
    )
    body = b" \n" + json.dumps(document, indent=2).encode() + b"\t \n"
    target = tmp_path / "formatted-source"
    captured = capture_neotoma_resources(
        target,
        plan=NeotomaResourcePlan(
            (replace(plan.resources[0], versions=(version,)),), plan.roster_sha256
        ),
        fetch=lambda url, **_: NeotomaMetadataResponse(url, 200, (), body),
    )
    inputs["resource_captures"] = {captured.manifest_sha256: target}
    return body, target


@pytest.mark.parametrize("version", ["current", "doi_frozen"])
def test_opt_in_returns_exact_same_buffer_once_and_default_remains_json_compatible(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    version: str,
    resource_reader: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[[dict[str, Any]], tuple[Path, str, dict[str, Path]]],
) -> None:
    inputs = catalogue_sources()
    body, source = _formatted_source(inputs, tmp_path, version)
    output, digest, sources = publish_catalogue(inputs)
    arguments = {
        "expected_manifest_sha256": digest,
        "dataset_id": 201,
        "version": version,
        "capture_sources": sources,
    }
    default = resource_reader(output, **arguments)
    explicit_false = resource_reader(output, **arguments, include_native_body=False)
    assert default == explicit_false and "native_body" not in default
    json.dumps(default)
    module = importlib.import_module(resource_reader.__module__)
    original_body: Callable[..., bytes] = module._selected_body
    original_read: Callable[[Path, int], bytes] = module._read
    buffers: list[bytes] = []
    opened: list[Path] = []

    def observe_body(*args: Any, **kwargs: Any) -> bytes:
        actual = original_body(*args, **kwargs)
        buffers.append(actual)
        return actual

    def observe_read(path: Path, bound: int) -> bytes:
        if path.name.endswith(".body"):
            opened.append(path)
        return original_read(path, bound)

    monkeypatch.setattr(module, "_selected_body", observe_body)
    monkeypatch.setattr(module, "_read", observe_read)
    result = resource_reader(output, **arguments, include_native_body=True)
    assert opened == [source / f"dataset-201-{version}-attempt-1.body"]
    assert len(buffers) == 1 and result["native_body"] is buffers[0]
    assert result["native_body"] == body
    assert result["source"]["body_sha256"] == sha256(body).hexdigest()
    assert result["native_payload"] == json.loads(body)
    assert json.dumps(result["native_payload"]).encode() != body
    assert {
        key: value for key, value in result.items() if key != "native_body"
    } == default
    assert result["scientific_admission"] == "not_asserted"


@pytest.mark.parametrize("version", ["current", "doi_frozen"])
def test_reused_source_returns_only_the_original_native_body(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    version: str,
    resource_reader: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[[dict[str, Any]], tuple[Path, str, dict[str, Path]]],
) -> None:
    inputs = catalogue_sources()
    body, source = _formatted_source(inputs, tmp_path, version)
    ancestors = inputs["resource_captures"]
    plan, _ = plan_from_json(json.loads((source / "request-plan.json").read_bytes()))
    reused_root = tmp_path / "reused"
    reused = capture_neotoma_resources(
        reused_root,
        plan=plan,
        reuse_from=ancestors,
        fetch=lambda *args, **kwargs: pytest.fail("Reuse performed a GET"),
    )
    inputs.update(
        resource_captures={reused.manifest_sha256: reused_root},
        source_captures=ancestors,
    )
    output, digest, _ = publish_catalogue(inputs)
    module = importlib.import_module(resource_reader.__module__)
    original: Callable[[Path, int], bytes] = module._read
    opened = []

    def tracked(path: Path, bound: int) -> bytes:
        if path.name.endswith(".body"):
            opened.append(path)
        return original(path, bound)

    monkeypatch.setattr(module, "_read", tracked)
    result = resource_reader(
        output,
        expected_manifest_sha256=digest,
        dataset_id=201,
        version=version,
        capture_sources=ancestors,
        include_native_body=True,
    )
    assert result["native_body"] == body
    assert opened == [source / f"dataset-201-{version}-attempt-1.body"]
    assert result["source"]["capture_manifest_sha256"] == next(iter(ancestors))


@pytest.mark.parametrize("flag", [None, 0, 1, "true", [], {}])
def test_nonboolean_opt_in_refuses_before_any_catalogue_or_source_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    flag: object,
    resource_reader: Callable[..., dict[str, Any]],
    no_outcome_resolver: dict[str, Path],
) -> None:
    module = importlib.import_module(resource_reader.__module__)
    monkeypatch.setattr(
        module,
        "load_neotoma_resource_catalogue",
        lambda *args, **kwargs: pytest.fail("Invalid flag opened catalogue"),
    )
    with pytest.raises(ValueError, match="native_body.*boolean"):
        resource_reader(
            tmp_path / "absent",
            expected_manifest_sha256="0" * 64,
            dataset_id=201,
            version="current",
            capture_sources=no_outcome_resolver,
            include_native_body=flag,
        )


@pytest.mark.parametrize("dataset_id", [203, 204])
@pytest.mark.parametrize("version", ["current", "doi_frozen"])
def test_body_opt_in_does_not_bypass_reserved_or_heldout_roles(
    catalogue_sources: Callable[..., dict[str, Any]],
    dataset_id: int,
    version: str,
    resource_reader: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[[dict[str, Any]], tuple[Path, str, dict[str, Path]]],
    no_outcome_resolver: dict[str, Path],
) -> None:
    output, digest, _ = publish_catalogue(catalogue_sources())
    with pytest.raises(ValueError, match="exposure role"):
        resource_reader(
            output,
            expected_manifest_sha256=digest,
            dataset_id=dataset_id,
            version=version,
            capture_sources=no_outcome_resolver,
            include_native_body=True,
        )


@pytest.mark.parametrize("version", ["current", "doi_frozen"])
def test_body_opt_in_keeps_pending_qualification_refusal_before_resolver(
    catalogue_sources: Callable[..., dict[str, Any]],
    version: str,
    resource_reader: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[[dict[str, Any]], tuple[Path, str, dict[str, Path]]],
    no_outcome_resolver: dict[str, Path],
) -> None:
    output, digest, _ = publish_catalogue(catalogue_sources(capture_resources=False))
    with pytest.raises(ValueError, match="not.*qualified|not_attempted"):
        resource_reader(
            output,
            expected_manifest_sha256=digest,
            dataset_id=201,
            version=version,
            capture_sources=no_outcome_resolver,
            include_native_body=True,
        )


def test_body_opt_in_keeps_unsupported_current_schema_refusal(
    catalogue_sources: Callable[..., dict[str, Any]],
    resource_reader: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[[dict[str, Any]], tuple[Path, str, dict[str, Path]]],
    no_outcome_resolver: dict[str, Path],
) -> None:
    output, digest, _ = publish_catalogue(
        catalogue_sources(auxiliary_type="unqualified native type")
    )
    with pytest.raises(ValueError, match="not qualified"):
        resource_reader(
            output,
            expected_manifest_sha256=digest,
            dataset_id=202,
            version="current",
            capture_sources=no_outcome_resolver,
            include_native_body=True,
        )


def test_body_opt_in_cannot_invent_a_missing_source_resolver(
    catalogue_sources: Callable[..., dict[str, Any]],
    resource_reader: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[[dict[str, Any]], tuple[Path, str, dict[str, Path]]],
) -> None:
    output, digest, _ = publish_catalogue(catalogue_sources())
    with pytest.raises(ValueError, match="resolver|capture"):
        resource_reader(
            output,
            expected_manifest_sha256=digest,
            dataset_id=201,
            version="current",
            capture_sources={},
            include_native_body=True,
        )
