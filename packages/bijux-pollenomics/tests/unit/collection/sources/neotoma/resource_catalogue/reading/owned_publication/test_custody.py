"""Metadata publication cannot adopt a foreign root or an open filesystem namespace."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma import resource_catalogue as api
from bijux_pollenomics.collection.sources.neotoma.capture.receipts import _write_json
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import (
    publication,
    storage,
)
from bijux_pollenomics.core.owned_tree import build_staging_output_dir


@pytest.mark.parametrize("partitioned", [False, True])
@pytest.mark.parametrize("replacement", ["symlink", "directory"])
def test_catalogue_writes_never_follow_a_replaced_root(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    partitioned: bool,
    replacement: str,
) -> None:
    inputs = catalogue_sources()
    catalogue = api.build_neotoma_resource_catalogue(**inputs)
    output = tmp_path / "catalogue"
    staging = build_staging_output_dir(output)
    original = tmp_path / "original-owned-stage"
    foreign = tmp_path / "another-writer"
    foreign.mkdir()
    (foreign / "preserve").write_bytes(b"foreign evidence")
    redirected = False

    def replace_root() -> None:
        nonlocal redirected
        assert not redirected
        redirected = True
        staging.rename(original)
        if replacement == "symlink":
            staging.symlink_to(foreign, target_is_directory=True)
        else:
            foreign.rename(staging)

    if partitioned:
        encode = storage._encode

        def encode_then_redirect(value: Any) -> bytes:
            content = encode(value)
            if (
                not redirected
                and isinstance(value, dict)
                and value.get("schema_version") == "neotoma-resource-catalogue-part.v1"
            ):
                replace_root()
            return content

        monkeypatch.setattr(storage, "_encode", encode_then_redirect)
    else:
        write_json = _write_json

        def write_then_redirect(path: Path, value: Any, **kwargs: Any) -> str:
            if not redirected and path == staging / "catalogue.json":
                replace_root()
            return write_json(path, value, **kwargs)

        monkeypatch.setattr(publication, "_write_json", write_then_redirect)

    with pytest.raises((ValueError, OSError)):
        api.write_neotoma_resource_catalogue(
            output,
            catalogue=catalogue,
            roster_path=inputs["roster_path"],
            capture_sources={
                **inputs["metadata_captures"],
                **inputs["resource_captures"],
            },
            partition_collections=partitioned,
        )
    assert redirected
    foreign_root = foreign if replacement == "symlink" else staging
    assert sorted(path.name for path in foreign_root.iterdir()) == ["preserve"]
    assert (foreign_root / "preserve").read_bytes() == b"foreign evidence"
    assert (original / "source-inventory.json").is_file()
    assert not output.exists()


@pytest.mark.parametrize("entry", ["empty_directory", "fifo", "hardlinked_member"])
def test_compact_loader_requires_a_closed_ordinary_namespace(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., Any],
    tmp_path: Path,
    entry: str,
) -> None:
    root, anchor, _ = publish_catalogue(catalogue_sources())
    if entry == "empty_directory":
        (root / "unowned").mkdir()
    elif entry == "fifo":
        os.mkfifo(root / "unowned")
    else:
        os.link(root / "catalogue.json", tmp_path / "foreign-alias.json")
    assert sha256((root / "manifest.json").read_bytes()).hexdigest() == anchor
    with pytest.raises(ValueError):
        api.load_neotoma_resource_catalogue(root, expected_manifest_sha256=anchor)


@pytest.mark.parametrize("partitioned", [False, True])
@pytest.mark.parametrize("limit", ["bytes", "files"])
def test_catalogue_loader_preflights_total_namespace_before_member_buffers(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    partitioned: bool,
    limit: str,
) -> None:
    inputs = catalogue_sources()
    root = tmp_path / "catalogue"
    api.write_neotoma_resource_catalogue(
        root,
        catalogue=api.build_neotoma_resource_catalogue(**inputs),
        roster_path=inputs["roster_path"],
        capture_sources={**inputs["metadata_captures"], **inputs["resource_captures"]},
        partition_collections=partitioned,
    )
    manifest = root / "manifest.json"
    digest = sha256(manifest.read_bytes()).hexdigest()
    members = [path for path in root.rglob("*") if path.is_file()]
    monkeypatch.setattr(
        publication,
        "MAX_BYTES" if limit == "bytes" else "MAX_FILES",
        sum(path.stat().st_size for path in members) - 1
        if limit == "bytes"
        else len(members) - 1,
        raising=False,
    )
    read = Path.open

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path != manifest and path.is_relative_to(root):
            pytest.fail("over-budget compact member buffer opened")
        return read(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observed)
    with pytest.raises(ValueError):
        api.load_neotoma_resource_catalogue(root, expected_manifest_sha256=digest)


@pytest.mark.parametrize("partitioned", [False, True])
def test_catalogue_publication_budget_is_enforced_before_member_write(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    partitioned: bool,
) -> None:
    inputs = catalogue_sources()
    output = tmp_path / "catalogue"
    monkeypatch.setattr(publication, "MAX_BYTES", 1, raising=False)
    with pytest.raises(ValueError):
        api.write_neotoma_resource_catalogue(
            output,
            catalogue=api.build_neotoma_resource_catalogue(**inputs),
            roster_path=inputs["roster_path"],
            capture_sources={
                **inputs["metadata_captures"],
                **inputs["resource_captures"],
            },
            partition_collections=partitioned,
        )
    assert not output.exists()
    assert not list(build_staging_output_dir(output).rglob("*.json"))
