"""Selected archive custody does not claim verification of unrelated numerical bytes."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma import resource_catalogue as api
from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
    NeotomaResourcePlan,
    NeotomaRetainedSource,
    capture_neotoma_resources,
)
from bijux_pollenomics.collection.sources.neotoma.capture.resources.protocol import (
    plan_from_json,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import archive

from .test_access import forbid_bodies, make_archive, selected_api


@pytest.mark.parametrize("mode", ["resource", "entity"])
def test_wrong_archive_anchor_refuses_before_body_access(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    read = selected_api(mode)
    root, _, _ = make_archive(catalogue_sources, publish_catalogue, tmp_path)
    forbid_bodies(monkeypatch)
    with pytest.raises(ValueError, match="manifest identity"):
        read(root, expected_manifest_sha256="0" * 64, dataset_id=201, version="current")


@pytest.mark.parametrize("mode", ["resource", "entity"])
def test_selected_body_corruption_refuses_using_actual_buffer(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., Any],
    tmp_path: Path,
    mode: str,
) -> None:
    read = selected_api(mode)
    root, pin, _ = make_archive(catalogue_sources, publish_catalogue, tmp_path)
    body = next((root / "captures").glob("*/dataset-201-current-attempt-1.body"))
    content = body.read_bytes()
    assert b'"value": 7' in content
    body.write_bytes(content.replace(b'"value": 7', b'"value": 8'))
    with pytest.raises(ValueError, match="body identity"):
        read(root, expected_manifest_sha256=pin, dataset_id=201, version="current")


@pytest.mark.parametrize("mode", ["resource", "entity"])
def test_unselected_same_length_corruption_is_outside_selected_integrity_scope(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., Any],
    tmp_path: Path,
    mode: str,
) -> None:
    read = selected_api(mode)
    root, pin, _ = make_archive(catalogue_sources, publish_catalogue, tmp_path)
    body = next((root / "captures").glob("*/dataset-202-current-attempt-1.body"))
    content = body.read_bytes()
    assert b'"value": null' in content
    body.write_bytes(content.replace(b'"value": null', b'"value": true'))
    result = read(root, expected_manifest_sha256=pin, dataset_id=201, version="current")
    assert result["archive"]["unselected_source_bodies_verified"] is False
    with pytest.raises(ValueError, match="identity"):
        archive.load_neotoma_source_archive(root, expected_manifest_sha256=pin)


@pytest.mark.parametrize("field", ["sha256", "bytes"])
def test_rehashed_outer_member_claim_must_equal_native_descriptor_before_body(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    read = selected_api("resource")
    root, _, _ = make_archive(catalogue_sources, publish_catalogue, tmp_path)
    path = root / "manifest.json"
    manifest = json.loads(path.read_bytes())
    key = next(
        name
        for name in manifest["files"]
        if name.endswith("dataset-201-current-attempt-1.body")
    )
    if field == "sha256":
        manifest["files"][key][field] = "0" * 64
    else:
        manifest["files"][key][field] += 1
        manifest["source_bytes"] += 1
    path.write_text(json.dumps(manifest))
    pin = sha256(path.read_bytes()).hexdigest()
    forbid_bodies(monkeypatch)
    with pytest.raises(ValueError):
        read(root, expected_manifest_sha256=pin, dataset_id=201, version="current")


def test_selected_archive_uses_internal_reuse_ancestor_only(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = catalogue_sources()
    ancestors = inputs["resource_captures"]
    original = next(iter(ancestors.values()))
    plan, _ = plan_from_json(json.loads((original / "request-plan.json").read_bytes()))
    reused_root = tmp_path / "reused"
    reused = capture_neotoma_resources(
        reused_root,
        plan=plan,
        reuse_from=ancestors,
        fetch=lambda *a, **k: pytest.fail("reuse GET"),
    )
    inputs.update(
        resource_captures={reused.manifest_sha256: reused_root},
        source_captures=ancestors,
    )
    root, pin, _ = make_archive(lambda **_: inputs, publish_catalogue, tmp_path)
    opened: list[str] = []
    native_open = Path.open

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.name.startswith("dataset-") and path.suffix == ".body":
            opened.append(path.name)
        return native_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observed)
    result = selected_api("resource")(
        root, expected_manifest_sha256=pin, dataset_id=201, version="current"
    )
    assert opened == ["dataset-201-current-attempt-1.body"]
    assert result["source"]["capture_manifest_sha256"] == next(iter(ancestors))


@pytest.mark.parametrize("mode", ["resource", "entity"])
def test_selected_archive_resolves_original_retained_epoch_without_external_paths(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    mode: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = catalogue_sources()
    native_root = next(iter(inputs["resource_captures"].values()))
    plan, _ = plan_from_json(
        json.loads((native_root / "request-plan.json").read_bytes())
    )
    body = tmp_path / "original.body"
    body.write_bytes((native_root / "dataset-201-current-attempt-1.body").read_bytes())
    expected = body.read_bytes()
    checksum = sha256(expected).hexdigest()
    provenance = tmp_path / "original-provenance.json"
    url = "https://api.neotomadb.org/v2.0/data/downloads/201"
    provenance.write_text(
        json.dumps(
            {
                "schema_version": "bokesjon-public-core-sources.v1",
                "sources": [
                    {
                        "source_url": url,
                        "final_url": url,
                        "status": 200,
                        "bytes": len(expected),
                        "sha256": checksum,
                        "retrieved_at": "2026-11-14T17:32:38.790438+00:00",
                    }
                ],
            }
        )
    )
    retained = {
        "dataset-201-current": NeotomaRetainedSource(
            body, provenance, sha256(provenance.read_bytes()).hexdigest(), checksum
        )
    }
    retained_root = tmp_path / "retained-capture"
    captured = capture_neotoma_resources(
        retained_root,
        plan=NeotomaResourcePlan(
            (replace(plan.resources[0], versions=("current",)),), plan.roster_sha256
        ),
        retained_sources=retained,
        fetch=lambda *a, **k: pytest.fail("retained GET"),
    )
    inputs.update(
        resource_captures={captured.manifest_sha256: retained_root},
        retained_sources=retained,
    )
    logical = api.build_neotoma_resource_catalogue(**inputs)
    sources = {**inputs["metadata_captures"], **inputs["resource_captures"]}
    public = tmp_path / "public"
    api.write_neotoma_resource_catalogue(
        public,
        catalogue=logical,
        roster_path=inputs["roster_path"],
        capture_sources=sources,
        retained_sources=retained,
    )
    output = tmp_path / "archive"
    archive.write_neotoma_source_archive(
        output,
        catalogue_directory=public,
        expected_catalogue_manifest_sha256=sha256(
            (public / "manifest.json").read_bytes()
        ).hexdigest(),
        capture_sources=sources,
        retained_sources=retained,
    )
    body.unlink()
    provenance.unlink()
    retained_body = output / "captures/retained/dataset-201-current/native.body"
    opened: list[Path] = []
    native_open = Path.open

    def observed(path: Path, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        if path == retained_body and mode == "rb":
            opened.append(path)
        return native_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observed)
    kwargs = {"include_native_body": True} if mode == "resource" else {}
    result = selected_api(mode)(
        output,
        expected_manifest_sha256=sha256(
            (output / "manifest.json").read_bytes()
        ).hexdigest(),
        dataset_id=201,
        version="current",
        **kwargs,
    )
    assert result["native_body"] == expected
    assert opened == [retained_body]
    assert result["source"]["epoch_kind"] == "original_timed_public_response"


@pytest.mark.parametrize("mode", ["resource", "entity"])
@pytest.mark.parametrize(
    "override", ["capture_sources", "retained_sources", "original_relational_root"]
)
def test_archive_reader_accepts_no_external_resolver_override(
    tmp_path: Path, mode: str, override: str
) -> None:
    with pytest.raises(TypeError):
        selected_api(mode)(
            tmp_path / "absent",
            expected_manifest_sha256="0" * 64,
            dataset_id=201,
            version="current",
            **{override: {}},
        )


def test_native_ledger_metadata_is_hashed_before_selected_body(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, pin, _ = make_archive(catalogue_sources, publish_catalogue, tmp_path)
    path = next((root / "captures").glob("*/capture-manifest.json"))
    content = path.read_bytes()
    assert b'"not_asserted"' in content
    path.write_bytes(content.replace(b'"not_asserted"', b'"not_assertef"'))
    forbid_bodies(monkeypatch)
    with pytest.raises(ValueError, match="metadata.*identity|identity.*metadata"):
        selected_api("resource")(
            root, expected_manifest_sha256=pin, dataset_id=201, version="current"
        )
