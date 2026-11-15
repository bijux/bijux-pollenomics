"""Selected native resource reuse lineage controls."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


def test_reader_resolves_reused_ancestor_without_scanning_other_native_entities(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    resource_reader: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[[dict[str, Any]], tuple[Path, str, dict[str, Path]]],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
        capture_neotoma_resources,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.resources.protocol import (
        plan_from_json,
    )

    read = resource_reader
    inputs = catalogue_sources()
    original_sources = inputs["resource_captures"]
    original_root = next(iter(original_sources.values()))
    plan, _ = plan_from_json(
        json.loads((original_root / "request-plan.json").read_bytes())
    )
    reused_root = tmp_path / "reused"
    reused = capture_neotoma_resources(
        reused_root,
        plan=plan,
        reuse_from=original_sources,
        fetch=lambda *args, **kwargs: pytest.fail("Reuse performed a GET"),
    )
    inputs["resource_captures"] = {reused.manifest_sha256: reused_root}
    inputs["source_captures"] = original_sources
    output, digest, _ = publish_catalogue(inputs)
    module = importlib.import_module(read.__module__)
    original_read: Callable[[Path, int], bytes] = module._read
    opened = []

    def tracked(path: Path, bound: int) -> bytes:
        if path.name.endswith(".body"):
            opened.append(path)
        return original_read(path, bound)

    monkeypatch.setattr(module, "_read", tracked)
    result = read(
        output,
        expected_manifest_sha256=digest,
        dataset_id=201,
        version="current",
        capture_sources=original_sources,
    )
    assert opened == [original_root / "dataset-201-current-attempt-1.body"]
    assert result["source"]["capture_manifest_sha256"] == next(iter(original_sources))


@pytest.mark.parametrize(
    "mutation", ["wrong_ancestor", "invented_retained", "invented_predecessor"]
)
def test_rehashed_publication_cannot_fabricate_selected_reuse_lineage(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    mutation: str,
    resource_reader: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[[dict[str, Any]], tuple[Path, str, dict[str, Path]]],
    no_outcome_resolver: dict[str, Path],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
        capture_neotoma_resources,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.resources.protocol import (
        plan_from_json,
    )

    read = resource_reader
    inputs = catalogue_sources()
    ancestors = inputs["resource_captures"]
    source = next(iter(ancestors.values()))
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
    output, _, _ = publish_catalogue(inputs)
    catalogue_path = output / "catalogue.json"
    catalogue = json.loads(catalogue_path.read_bytes())
    old = reused.manifest_sha256
    directory = output / "captures" / old
    native_manifest_path = directory / "capture-manifest.json"
    native_manifest = json.loads(native_manifest_path.read_bytes())
    entry = next(
        row
        for row in native_manifest["resources"]
        if row["resource_key"] == "dataset-201-current"
    )
    if mutation == "wrong_ancestor":
        entry["reused_from"]["resource_key"] = "dataset-999-current"
    elif mutation == "invented_retained":
        entry["retained_source"] = {"body_sha256": "0" * 64}
    else:
        entry["predecessor_result"] = {
            "manifest_sha256": "0" * 64,
            "resource_key": "dataset-201-current",
            "terminal_status": "parsed_native",
        }
    native_manifest_path.write_text(json.dumps(native_manifest))
    digest = sha256(native_manifest_path.read_bytes()).hexdigest()
    renamed = directory.with_name(digest)
    directory.rename(renamed)
    descriptor = catalogue["capture_descriptors"].pop(old)
    descriptor["capture_manifest_sha256"] = digest
    member = next(
        row for row in descriptor["files"] if row["name"] == "capture-manifest.json"
    )
    member.update(
        sha256=digest, bytes=(renamed / "capture-manifest.json").stat().st_size
    )
    (renamed / "descriptor.json").write_text(json.dumps(descriptor))
    catalogue["capture_descriptors"][digest] = descriptor
    catalogue["selected_resource_capture_manifest_sha256"] = [digest]
    for resource in catalogue["resources"]:
        for version in resource["versions"].values():
            if version["source"].get("capture_manifest_sha256") == old:
                version["source"]["capture_manifest_sha256"] = digest
    catalogue_path.write_text(json.dumps(catalogue))
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["files"] = {
        name.replace(old, digest): sha256(
            (output / name.replace(old, digest)).read_bytes()
        ).hexdigest()
        for name in manifest["files"]
    }
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="ancestor|reused entry"):
        read(
            output,
            expected_manifest_sha256=sha256(manifest_path.read_bytes()).hexdigest(),
            dataset_id=201,
            version="current",
            capture_sources=no_outcome_resolver,
        )
