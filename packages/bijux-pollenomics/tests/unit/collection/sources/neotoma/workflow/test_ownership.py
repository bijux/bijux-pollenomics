"""The complete collection owns its files even when path entries are replaced."""

from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma import collection
from bijux_pollenomics.collection.sources.neotoma.publication import ownership

from .native_products import collect


@pytest.mark.parametrize("boundary", ["before_publish", "after_publish"])
def test_equal_byte_competing_collection_is_refused(
    tmp_path: Path, source: list[str], monkeypatch: pytest.MonkeyPatch, boundary: str
) -> None:
    output, stage = tmp_path / "neotoma", tmp_path / ".neotoma.staging"
    saved = tmp_path / "original-owned-collection"
    module = collection if "publish_new_output_tree" in vars(collection) else ownership
    publish = vars(module)["publish_new_output_tree"]

    def swap(**kwargs: Any) -> None:
        if boundary == "after_publish":
            publish(**kwargs)
        location = stage if boundary == "before_publish" else output
        location.rename(saved)
        shutil.copytree(saved, location)
        if boundary == "before_publish":
            publish(**kwargs)

    monkeypatch.setattr(module, "publish_new_output_tree", swap)
    with pytest.raises(ValueError, match="identity|inode"):
        collect(output)
    assert source == ["inventory"]
    assert (saved / "raw/neotoma_pollen_sites.json").read_bytes() == (
        output / "raw/neotoma_pollen_sites.json"
    ).read_bytes()


@pytest.mark.parametrize("transport_failure", [False, True])
def test_source_response_cannot_write_into_a_competing_collection(
    tmp_path: Path,
    source: list[str],
    monkeypatch: pytest.MonkeyPatch,
    transport_failure: bool,
) -> None:
    output, stage = tmp_path / "neotoma", tmp_path / ".neotoma.staging"
    saved = tmp_path / "original-owned-collection"
    original_fetch = collection.fetch_neotoma_dataset_inventory_rows

    def replaced(*args: Any) -> list[dict[str, object]]:
        response = original_fetch(*args)
        stage.rename(saved)
        stage.mkdir()
        (stage / "raw").mkdir()
        (stage / "normalized").mkdir()
        (stage / "foreign-owner.txt").write_bytes(b"another writer's source")
        if transport_failure:
            raise TimeoutError("Source interrupted after root substitution")
        return response

    monkeypatch.setattr(collection, "fetch_neotoma_dataset_inventory_rows", replaced)
    with pytest.raises((ValueError, TimeoutError), match="identity|Source interrupted"):
        collect(output)
    assert not output.exists()
    assert (stage / "foreign-owner.txt").read_bytes() == b"another writer's source"
    assert sorted(p.relative_to(stage).as_posix() for p in stage.rglob("*")) == [
        "foreign-owner.txt",
        "normalized",
        "raw",
    ]
    assert saved.is_dir()


def test_child_directory_replacement_never_receives_source_writes(
    tmp_path: Path, source: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.core.filesystem import OwnedTreeWriter

    output, stage = tmp_path / "neotoma", tmp_path / ".neotoma.staging"
    saved, raw = tmp_path / "original-raw", stage / "raw"
    original = OwnedTreeWriter.write_bytes
    replaced = []

    def write(writer: OwnedTreeWriter, name: str, content: bytes) -> None:
        original(writer, name, content)
        if name == "raw/neotoma_pollen_dataset_inventory.json":
            raw.rename(saved)
            raw.mkdir()
            (raw / "foreign-owner.txt").write_bytes(b"independent source")
            replaced.append(True)

    monkeypatch.setattr(OwnedTreeWriter, "write_bytes", write)
    with pytest.raises(ValueError, match="identity"):
        collect(output)
    assert source == ["inventory"] and replaced == [True]
    assert sorted(p.name for p in raw.iterdir()) == ["foreign-owner.txt"]
    assert (saved / "neotoma_pollen_dataset_inventory.json").is_file()
    assert not output.exists()


def test_complete_collection_manifest_records_bytes_without_provider_admission(
    tmp_path: Path, source: list[str]
) -> None:
    from hashlib import sha256
    import json

    output = tmp_path / "neotoma"
    collect(output)
    manifest = json.loads((output / "collection-manifest.json").read_bytes())
    assert manifest["http_custody"] == "not_recorded_by_legacy_collector"
    assert manifest["scientific_admission"] == "not_asserted"
    assert len(manifest["files"]) == 9
    assert manifest["source_bytes"] == sum(
        row["bytes"] for row in manifest["files"].values()
    )
    for name, expected in manifest["files"].items():
        raw = (output / name).read_bytes()
        assert len(raw) == expected["bytes"]
        assert sha256(raw).hexdigest() == expected["sha256"]
    assert source == ["inventory"]


def test_final_member_readback_cannot_adopt_competing_child_directory(
    tmp_path: Path, source: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.publication.collection import (
        CollectionTreeWriter,
    )

    output, saved = tmp_path / "neotoma", tmp_path / "owned-raw"
    validate = CollectionTreeWriter._validate_member
    swapped = []

    def replaced(root: Path, name: str, expected: dict[str, Any]) -> None:
        validate(root, name, expected)
        if root == output and name == "raw/neotoma_pollen_dataset_inventory.json":
            (root / "raw").rename(saved)
            shutil.copytree(saved, root / "raw")
            target = root / "raw" / name.split("/")[-1]
            raw = target.read_bytes()
            changed = raw.replace(b"201", b"999")
            assert raw != changed and len(raw) == len(changed)
            target.write_bytes(changed)
            swapped.append(True)

    monkeypatch.setattr(
        CollectionTreeWriter, "_validate_member", staticmethod(replaced)
    )
    with pytest.raises(ValueError, match="identity|attachment"):
        collect(output)
    assert swapped == [True]
    assert saved.is_dir() and (output / "raw").is_dir()


def test_special_leaf_substitution_cannot_block_collection_readback(
    tmp_path: Path,
) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from concurrent.futures import TimeoutError as FutureTimeout
    import os

    from bijux_pollenomics.collection.sources.neotoma.publication.collection import (
        CollectionTreeWriter,
    )

    root = tmp_path / "collection"
    root.mkdir()
    target = root / "source"
    os.mkfifo(target)
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(
        CollectionTreeWriter._validate_member,
        root,
        "source",
        {"bytes": 10, "sha256": "0" * 64},
    )
    try:
        with pytest.raises(ValueError, match="identity"):
            future.result(timeout=2)
    except FutureTimeout:
        # Release a regressed blocking reader before closing the worker pool.
        descriptor = os.open(target, os.O_WRONLY | os.O_NONBLOCK)
        os.close(descriptor)
        pytest.fail("Collection readback blocked on a substituted special file")
    finally:
        executor.shutdown(wait=True)
